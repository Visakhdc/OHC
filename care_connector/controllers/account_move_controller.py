import json
from odoo.http import request, Response, Controller
from odoo.exceptions import AccessDenied
from odoo import http, registry, fields
from datetime import datetime
from ..pydantic_models.account_move_pydantic_model import AccountMoveApiRequest,AccountMovePaymentApiRequest
from ..authentication.authenticate_user import UserAuthentication
from ..master_services.item_master import ItemMasterService
from ..master_services.partner_master import PartnerMasterService

class AccountMoveController(http.Controller):

    @http.route('/api/account/move', type='json', auth='public', methods=['POST'], csrf=False)
    def account_move(self, **kwargs):
        """Creating customer invoice or vendor bill"""

        auth_header = request.httprequest.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return Response(json.dumps({"error": "Missing or invalid Authorization header"}),
                            status=401, mimetype="application/json")

        try:
            auth_user = UserAuthentication.get_authenticated_user(auth_header)
            if not auth_user:
                return Response(json.dumps({"error": "Invalid credentials"}),
                                status=401, mimetype="application/json")


            user_env = request.env(user=auth_user, su=False)
            data = json.loads(request.httprequest.data)
            try:
                request_data = AccountMoveApiRequest(**data)
            except Exception as e:
                return Response(
                    json.dumps({
                        "status": "error",
                        "message": "Validation failed",
                        "details": json.loads(e.json())
                    }),
                    status=422,
                    content_type="application/json"
                )

            x_care_id = request_data.x_care_id
            partner_data = request_data.partner_data
            invoice_items = request_data.invoice_items

            if not all([x_care_id, partner_data, invoice_items]):
                return Response(json.dumps({
                    "error": "Missing required fields: x_care_id, vendor reference, or invoice items."
                }), status=400, mimetype="application/json")

            account_move = user_env["account.move"]
            existing_invoice = account_move.search([('x_care_id', '=', x_care_id)], limit=1)
            if existing_invoice:
                return Response(
                    json.dumps({
                        "error": "Invoice already exists",
                        "invoice_id": existing_invoice.id,
                        "invoice_name": existing_invoice.name,
                    }),
                    status=409,
                    content_type="application/json"
                )
            res_partner = PartnerMasterService.get_or_create_partner(user_env, partner_data)
            bill_type = request_data.bill_type.value
            invoice_date = request_data.invoice_date
            due_date = request_data.due_date

            move_type = "out_invoice"
            tax_use_type = 'sale'
            if bill_type == "vendor":
                tax_use_type = 'purchase'
                move_type = "in_invoice"

            move_data_dict = {
                    "x_care_id" :x_care_id,
                    "res_partner" : res_partner,
                    "invoice_items" : invoice_items,
                    "invoice_date" : invoice_date,
                    "due_date" : due_date,
                    "move_type":move_type,
                    "tax_use_type":tax_use_type,
            }
            account_move = self.create_account_move(user_env,move_data_dict)
            if not account_move:
                return Response(json.dumps({"error": "Failed to create the Invoice"}),
                                status=400, mimetype="application/json")
            return {
                "success": True,
                "invoice_id": account_move.id,
                "invoice_name": account_move.name,
            }

        except Exception:
            return Response(json.dumps({"error": "Invalid credentials format"}),
                            status=401, mimetype="application/json")

    @http.route('/api/account/move/return', type='json', auth='public', methods=['POST'], csrf=False)
    def account_move_return(self, **kwargs):
        """Creating credit note or refund"""

        auth_header = request.httprequest.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return Response(json.dumps({"error": "Missing or invalid Authorization header"}),
                            status=401, mimetype="application/json")

        try:
            auth_user = UserAuthentication.get_authenticated_user(auth_header)
            if not auth_user:
                return Response(json.dumps({"error": "Invalid credentials"}),
                                status=401, mimetype="application/json")

            user_env = request.env(user=auth_user, su=False)
            data = json.loads(request.httprequest.data)

            try:
                request_data = AccountMoveApiRequest(**data)
            except Exception as e:
                return Response(
                    json.dumps({
                        "status": "error",
                        "message": "Validation failed",
                        "details": json.loads(e.json())
                    }),
                    status=422,
                    content_type="application/json"
                )

            x_care_id = request_data.x_care_id
            partner_data = request_data.partner_data
            invoice_items = request_data.invoice_items

            if not all([x_care_id, partner_data, invoice_items]):
                return Response(json.dumps({
                    "error": "Missing required fields: x_care_id, vendor reference, or invoice items."
                }), status=400, mimetype="application/json")

            reason = request_data.reason if request_data.reason else None
            account_move = user_env["account.move"]
            a_m_r_model = user_env['account.move.reversal']
            existing_invoice = account_move.search([('x_care_id', '=', x_care_id)], limit=1)

            if existing_invoice:
                reversal_wizard = a_m_r_model.with_context(
                    {'active_ids': [existing_invoice.id], 'active_id': existing_invoice.id,
                     'active_model': 'account.move'}).create({
                    'reason': reason,
                    'journal_id': existing_invoice.journal_id.id,
                })
                if not reversal_wizard:
                    return Response(json.dumps({"error": "Failed to reverse the Invoice"}),
                                    status=500, content_type="application/json")
                reversal_wizard.reverse_moves()

                credit_note = account_move.search([
                    ('reversed_entry_id', '=', existing_invoice.id),
                    ('move_type', 'in', ['out_refund', 'in_refund'])
                ], limit=1)

                if not credit_note:
                    return Response(json.dumps({"error": "Failed to create Credit note"}),
                                    status=500, content_type="application/json")
                credit_note.action_post()
                return Response(json.dumps({
                    "success": True,
                    "credit_note_id": credit_note.id,
                    "credit_note_name": credit_note.name,
                    "refunded_invoice": existing_invoice.name,
                }), status=201, content_type="application/json")

            else:
                res_partner = PartnerMasterService.get_or_create_partner(user_env, partner_data)
                bill_type = request_data.bill_type.value
                invoice_date = request_data.invoice_date
                due_date = request_data.due_date

                move_type = "out_refund"
                tax_use_type = 'sale'
                if bill_type == "vendor":
                    tax_use_type = 'purchase'
                    move_type = "in_refund"

                move_data_dict = {
                    "x_care_id": x_care_id,
                    "res_partner": res_partner,
                    "invoice_items": invoice_items,
                    "invoice_date": invoice_date,
                    "due_date": due_date,
                    "move_type": move_type,
                    "tax_use_type": tax_use_type,
                }
                account_move = self.create_account_move(user_env, move_data_dict)
                if not account_move:
                    return Response(json.dumps({"error": "Failed to create the Invoice"}),
                                    status=400, mimetype="application/json")
                return {
                    "success": True,
                    "invoice_id": account_move.id,
                    "invoice_name": account_move.name,
                }

        except Exception:
            return Response(json.dumps({"error": "Invalid credentials format"}),
                            status=401, mimetype="application/json")



    def create_account_move(self,user_env,move_data):
        """Creating Invoices"""
        x_care_id = move_data.get("x_care_id")
        res_partner = move_data.get("res_partner")
        invoice_items = move_data.get("invoice_items")
        invoice_date = move_data.get("invoice_date")
        due_date = move_data.get("due_date")
        move_type = move_data.get("move_type")
        tax_use_type = move_data.get("tax_use_type")
        account_move_model = user_env['account.move']
        account_tax_model = user_env['account.tax']

        invoice_line_list = []
        for item in invoice_items:
            product_data = item.product_data
            product = ItemMasterService.get_or_create_product(user_env, product_data)
            if not product:
                return Response(json.dumps({"error": "Failed to create or retrieve the product"}),
                                status=400, mimetype="application/json")
            tax = int(item.tax)
            default_tax = account_tax_model.search([
                ('amount', '=', tax),
                ('type_tax_use', '=', tax_use_type)
            ], limit=1)
            tax_ids = [default_tax.id] if default_tax else []

            invoice_line_list.append((0, 0, {
                'product_id': product.id,
                'quantity': item.quantity,
                'price_unit': item.sale_price,
                'tax_ids': [(6, 0, tax_ids)],
                'x_care_id': item.x_care_id,
            }))
        invoice_date = datetime.strptime(invoice_date, "%d-%m-%Y").date()
        due_date = datetime.strptime(due_date, "%d-%m-%Y").date()
        account_move = account_move_model.create({
            'move_type': move_type,
            'partner_id': res_partner.id,
            'x_care_id': x_care_id,
            'invoice_date': invoice_date,
            'invoice_date_due': due_date,
            'invoice_line_ids': invoice_line_list,
        })
        if account_move:
            account_move.action_post()

        return account_move


    @http.route('/api/account/move/payment', type='json', auth='public', methods=['POST'], csrf=False)
    def account_move_payment(self, **kwargs):
        """Invoice payment"""

        auth_header = request.httprequest.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return Response(json.dumps({"error": "Missing or invalid Authorization header"}),
                            status=401, mimetype="application/json")

        try:
            auth_user = UserAuthentication.get_authenticated_user(auth_header)
            if not auth_user:
                return Response(json.dumps({"error": "Invalid credentials"}),
                                status=401, mimetype="application/json")

            user_env = request.env(user=auth_user, su=False)
            data = json.loads(request.httprequest.data)
            try:
                request_data = AccountMovePaymentApiRequest(**data)
            except Exception as e:
                return Response(
                    json.dumps({
                        "status": "error",
                        "message": "Validation failed",
                        "details": json.loads(e.json())
                    }),
                    status=422,
                    content_type="application/json"
                )
            x_care_id = request_data.x_care_id
            amount = request_data.amount
            journal_input = request_data.journal_input.value
            payment_date = request_data.payment_date


            if not all([x_care_id, amount, journal_input,payment_date]):
                return Response(json.dumps({
                    "error": "Missing required fields: x_care_id, vendor reference, or invoice items."
                }), status=400, mimetype="application/json")

            account_move_model = user_env["account.move"]
            account_journal_model = user_env['account.journal']
            a_p_r_transient_model = user_env['account.payment.register']
            existing_invoice = account_move_model.search([('x_care_id', '=', x_care_id)], limit=1)

            if not existing_invoice:
                return Response(
                    json.dumps({
                        "error": "Invoice not found",
                    }),
                    status=400,
                    content_type="application/json"
                )

            if existing_invoice.state != 'posted':
                return Response(json.dumps({"error": f"Invoice {existing_invoice.name} is not posted"}),
                                status=400, mimetype="application/json")

            if existing_invoice.payment_state == 'paid':
                return Response(json.dumps({"error": f"Invoice {existing_invoice.name} is already marked as paid. "
                                                     f"No further payment can be processed"}),status=400, mimetype="application/json")

            account_journal = account_journal_model.sudo().search([
                    '|', '|',
                    ('name', 'ilike', journal_input),
                    ('code', 'ilike', journal_input),
                    ('type', '=', journal_input.lower())
                ], limit=1)
            if not account_journal:
                return Response(json.dumps({"error": f"No journal found for '{journal_input}'"}),
                                status=404, mimetype="application/json")

            ctx = {
                'active_model': 'account.move',
                'active_ids': [existing_invoice.id],
                'active_id': existing_invoice.id,
            }

            payment_wizard = a_p_r_transient_model.with_context(ctx).create({
                'amount': amount,
                'journal_id': account_journal.id,
                'payment_date': payment_date or fields.Date.today()
            })._create_payments()
            if not payment_wizard:
                return Response(json.dumps({
                    "error": f"Payment creation failed"
                }), status=500, content_type="application/json")

            payment_wizard.action_create_payments()
            return Response(json.dumps({
                "success": True,
                "invoice": existing_invoice.name,
                "invoice_id": existing_invoice.id,
                "amount_paid": amount,
                "journal_id": account_journal.id,
                "status": "Payment registered successfully"
            }), status=201, mimetype="application/json")


        except Exception:
            return Response(json.dumps({"error": "Invalid credentials format"}),
                            status=401, mimetype="application/json")
