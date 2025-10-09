import base64
import json
from odoo.http import request, Response, Controller
from odoo.exceptions import AccessDenied
from odoo import http, registry,fields
from datetime import datetime

class CareIntegrationController(http.Controller):

    @http.route('/api/create_invoice', type='json', auth='public', methods=['POST'], csrf=False)
    def create_invoice(self, **kwargs):
        auth_header = request.httprequest.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return Response(json.dumps({"error": "Missing or invalid Authorization header"}),
                            status=401, mimetype="application/json")

        try:
            auth_user = self.get_authenticated_user(auth_header)
            if auth_user:
                user_env = request.env(user=auth_user, su=False)
                data = json.loads(request.httprequest.data)
                x_care_id = data.get("x_care_id")

                if not x_care_id:
                    return Response(
                        json.dumps({"error": "Missing required field: x_care_id"}),
                        status=400,  # Bad Request
                        content_type="application/json"
                    )

                existing_invoice = user_env["account.move"].search([('x_care_id', '=', x_care_id)], limit=1)
                if existing_invoice:
                    return Response(
                        json.dumps({
                            "error": "Invoice already exists",
                            "invoice_id": existing_invoice.id,
                            "invoice_name": existing_invoice.name,
                        }),
                        status=409,  # Conflict
                        content_type="application/json"
                    )
                if data['partner_data']:
                    partner_id = self.get_or_create_partner(data['partner_data'], user_env)

                    move_type = "out_invoice"
                    tax_use_type = 'sale'
                    if data['bill_type'] == "vendor":
                        tax_use_type = 'purchase'
                        move_type = "in_invoice"
                    invoice_lines = []
                    for line in data['invoice_items']:
                        if line["product"]:
                            product = self.get_or_create_product(line["product"], user_env)
                            tax = int(line["tax"])
                            default_tax = user_env['account.tax'].search([
                                ('amount', '=', tax),
                                ('type_tax_use', '=', tax_use_type)
                            ], limit=1)
                            tax_ids = [default_tax.id] if default_tax else []

                            invoice_lines.append((0, 0, {
                                'product_id': product.id,
                                'quantity': line.get('quantity', 1),
                                'price_unit': line.get('sale_price', 0.0),
                                'tax_ids': [(6, 0, tax_ids)],
                                'x_care_id': line.get('x_care_id'),
                            }))

                    if partner_id and invoice_lines:
                        invoice_date = datetime.strptime(data['invoice_date'], "%d-%m-%Y").date()

                        move = user_env['account.move'].create({
                            'move_type': move_type,
                            'partner_id': partner_id.id,
                            'x_care_id': x_care_id,
                            'payment_type': data['payment_type'],
                            'invoice_date': invoice_date,
                            'invoice_line_ids': invoice_lines,
                        })
                        move.action_post()

                    return {
                        "success": True,
                        "invoice_id": move.id,
                        "invoice_name": move.name,
                    }
                else:
                    return Response(json.dumps({"error": "No vendor reference"}),
                                    status=401, mimetype="application/json")

            else:
                return Response(json.dumps({"error": "Invalid credentials"}),
                                status=401, mimetype="application/json")


        except Exception:
            return Response(json.dumps({"error": "Invalid credentials format"}),
                            status=401, mimetype="application/json")

    @http.route('/api/pay_invoice', type='json', auth='public', methods=['POST'], csrf=False)
    def pay_invoice(self, **kwargs):
        auth_header = request.httprequest.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return Response(json.dumps({"error": "Missing or invalid Authorization header"}),
                            status=401, mimetype="application/json")

        try:
            auth_user = self.get_authenticated_user(auth_header)
            if auth_user:
                user_env = request.env(user=auth_user, su=True)
                data = json.loads(request.httprequest.data)
                x_care_id = data.get("x_care_id")
                amount = data.get("amount")
                journal_input = data.get("journal_input")
                payment_date = datetime.strptime(data.get("payment_date"), "%d-%m-%Y").date()

                if not all([x_care_id, amount, journal_input]):
                    return Response(json.dumps({"error": "Missing required fields: x_care_id, amount, or journal_id"}),
                                    status=400, mimetype="application/json")

                invoice = user_env["account.move"].search([('x_care_id', '=', x_care_id)], limit=1)
                if not invoice:
                    return Response(json.dumps({"error": "Invoice not found"}),
                                    status=404, mimetype="application/json")

                if invoice.state != 'posted':
                    return Response(json.dumps({"error": f"Invoice {invoice.name} is not posted"}),
                                    status=400, mimetype="application/json")

                journal = user_env['account.journal'].sudo().search([
                    '|', '|',
                    ('name', 'ilike', journal_input),
                    ('code', 'ilike', journal_input),
                    ('type', '=', journal_input.lower())
                ], limit=1)

                if not journal:
                    return Response(json.dumps({"error": f"No journal found for '{journal_input}'"}),
                                    status=404, mimetype="application/json")

                journal_id = journal.id

                ctx = {
                    'active_model': 'account.move',
                    'active_ids': [invoice.id],
                    'active_id': invoice.id,
                }
                try:
                    payment_wizard = user_env['account.payment.register'].with_context(ctx).create({
                        'amount': amount,
                        'journal_id': journal_id,
                        'payment_date': payment_date or fields.Date.today()
                    })._create_payments()

                except Exception as e:
                    return Response(json.dumps({

                        "error": f"Payment creation failed: {str(e)}"

                    }), status=500, content_type="application/json")

                return Response(json.dumps({
                    "success": True,
                    "invoice": invoice.name,
                    "invoice_id": invoice.id,
                    "amount_paid": amount,
                    "journal_id": journal_id,
                    "status": "Payment registered successfully"
                }), status=201, mimetype="application/json")

        except Exception:
            return Response(json.dumps({"error": "Invalid credentials format"}),
                            status=401, mimetype="application/json")



    @http.route('/api/return_bill', type='json', auth='public', methods=['POST'], csrf=False)
    def return_bills(self, **kwargs):
        auth_header = request.httprequest.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return Response(json.dumps({"error": "Missing or invalid Authorization header"}),
                            status=401, mimetype="application/json")

        try:
            auth_user = self.get_authenticated_user(auth_header)
            if auth_user:
                user_env = request.env(user=auth_user, su=True)
                data = json.loads(request.httprequest.data)
                x_care_id = data.get("x_care_id")
                reason = data.get("reason", "Customer Refund")
                invoice = None
                if x_care_id:
                    invoice = user_env["account.move"].search([('x_care_id', '=', x_care_id)], limit=1)
                    if invoice:
                        reversal_wizard = user_env['account.move.reversal'].with_context(
                            {'active_ids': [invoice.id], 'active_id': invoice.id,
                             'active_model': 'account.move'}).create({
                            'reason': reason,
                            'journal_id': invoice.journal_id.id,
                        })
                        reversal_wizard.reverse_moves()

                        credit_note = request.env['account.move'].sudo().search([
                            ('reversed_entry_id', '=', invoice.id),
                            ('move_type', 'in', ['out_refund', 'in_refund'])
                        ], limit=1)

                        if credit_note:
                            return Response(json.dumps({
                                "success": True,
                                "credit_note_id": credit_note.id,
                                "credit_note_name": credit_note.name,
                                "refunded_invoice": invoice.name,
                            }), status=201, content_type="application/json")
                        else:
                            return Response(json.dumps({"error": "Credit note not created"}),
                                            status=500, content_type="application/json")

                if not x_care_id or not invoice.exists():
                    if data['partner_data']:
                        partner_id = self.get_or_create_partner(data['partner_data'], user_env)

                        move_type = "out_refund"
                        tax_use_type = 'sale'
                        if data['bill_type'] == "vendor":
                            tax_use_type = 'purchase'
                            move_type = "in_refund"
                        invoice_lines = []
                        for line in data['invoice_items']:
                            if line["product"]:
                                product = self.get_or_create_product(line["product"], user_env)
                                tax = int(line["tax"])
                                default_tax = user_env['account.tax'].search([
                                    ('amount', '=', tax),
                                    ('type_tax_use', '=', tax_use_type)
                                ], limit=1)
                                tax_ids = [default_tax.id] if default_tax else []

                                invoice_lines.append((0, 0, {
                                    'product_id': product.id,
                                    'quantity': line.get('quantity', 1),
                                    'price_unit': line.get('sale_price', 0.0),
                                    'tax_ids': [(6, 0, tax_ids)],
                                    'x_care_id': line.get('x_care_id'),
                                }))

                        if partner_id and invoice_lines:
                            invoice_date = datetime.strptime(data['invoice_date'], "%d-%m-%Y").date()

                            move = user_env['account.move'].create({
                                'move_type': move_type,
                                'partner_id': partner_id.id,
                                'x_care_id': data['x_care_id'],
                                'payment_type': data['payment_type'],
                                'invoice_date': invoice_date,
                                'invoice_line_ids': invoice_lines,
                            })
                            move.action_post()
                            return {
                                "success": True,
                                "invoice_id": move.id,
                                "invoice_name": move.name,
                            }

                        else:
                            return Response(json.dumps({"error": "Partner or invoice items are missing"}),
                                            status=401, mimetype="application/json")

                    else:
                        return Response(json.dumps({"error": "No vendor reference"}),
                                        status=401, mimetype="application/json")

            else:
                return Response(json.dumps({"error": "Authentication Failed"}),
                                status=401, mimetype="application/json")
        except Exception:
            return Response(json.dumps({"error": "Invalid credentials format"}),
                            status=401, mimetype="application/json")


    @http.route('/api/add_product', type='json', auth='public', methods=['POST'], csrf=False)
    def create_update_product(self, **kwargs):
        try:
            auth_header = request.httprequest.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Basic "):
                return Response(json.dumps({"error": "Missing or invalid Authorization header"}),
                                status=401, mimetype="application/json")
            auth_user = self.get_authenticated_user(auth_header)
            if not auth_user:
                return Response(
                    json.dumps({"error": "Authentication failed"}),
                    status=403, mimetype="application/json"
                )

            created_products = []
            errors = []
            user_env = request.env(user=auth_user, su=True)
            data = json.loads(request.httprequest.data)

            for product_data in data["products"]:
                try:
                    product_id = self.get_or_create_product(product_data, user_env)
                    created_products.append({
                        "product_id": product_id.id,
                        "product_name": product_id.name,
                        "x_care_id": product_id.x_care_id,
                    })
                except Exception as e:
                    errors.append({
                        "product_data": product_data,
                        "error": str(e)
                    })

            response_data = {
                "status": "success",
                "created": len(created_products),
                "errors": len(errors),
                "products": created_products,
                "error_details": errors
            }

            return Response(json.dumps(response_data), status=200, mimetype="application/json")

        except Exception as e:
            return Response(
                json.dumps({"error": f"Server error: {str(e)}"}),
                status=500, mimetype="application/json"
            )

    @http.route('/api/add_partners', type='json', auth='public', methods=['POST'], csrf=False)
    def create_update_partner(self, **kwargs):
        try:
            auth_header = request.httprequest.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Basic "):
                return Response(json.dumps({"error": "Missing or invalid Authorization header"}),
                                status=401, mimetype="application/json")
            auth_user = self.get_authenticated_user(auth_header)
            if not auth_user:
                return Response(
                    json.dumps({"error": "Authentication failed"}),
                    status=403, mimetype="application/json"
                )

            created_partner = []
            errors = []
            user_env = request.env(user=auth_user, su=True)
            data = json.loads(request.httprequest.data)

            for partner_data in data["partners"]:
                try:
                    partner_id = self.get_or_create_partner(partner_data, user_env)
                    created_partner.append({
                        "partner_id": partner_id.id, # need change
                        "partner_name": partner_id.name,# need change
                        "x_care_id": partner_id.x_care_id,
                    })
                except Exception as e:
                    errors.append({
                        "product_data": partner_data,
                        "error": str(e)
                    })

            response_data = {
                "status": "success",
                "created": len(created_partner),
                "errors": len(errors),
                "products": created_partner,
                "error_details": errors
            }

            return Response(json.dumps(response_data), status=200, mimetype="application/json")

        except Exception as e:
            return Response(
                json.dumps({"error": f"Server error: {str(e)}"}),
                status=500, mimetype="application/json"
            )


    def get_authenticated_user(self,header):
        auth_decoded = base64.b64decode(header.split(" ")[1]).decode("utf-8")
        username, password = auth_decoded.split(":", 1)
        credential = {'login': username, 'password': password, 'type': 'password'}
        session_data = request.session.authenticate(request.session.db, credential)
        if session_data and session_data.get("uid"):
            return session_data["uid"]
        return None

    def get_or_create_partner(self,partner_data,user_env):
        """Find partner by care_partner_id, else create one with care_partner_id."""
        res_partner_id = user_env['res.partner'].search([('x_care_id', '=', partner_data['x_care_id'])], limit=1)
        if not res_partner_id:
            country = request.env['res.country'].search([('code', '=', 'IN')], limit=1)  # India

            state = request.env['res.country.state'].search([
                ('name', 'ilike', partner_data['state']),
                ('country_id', '=', country.id)
            ], limit=1)
            res_partner_id = res_partner_id.create({
                'name': partner_data['name'],
                'x_care_id': partner_data['x_care_id'],
                'company_type': partner_data['partner_type'],
                'email': partner_data['email'],
                'phone': partner_data['phone'],
                'country_id': country.id if country else False,
                'state_id': state.id if state else False,
            })
        return res_partner_id

    def get_or_create_product(self, product_data, user_env):
        """Find product by care_product_id, else create one with care_product_id."""
        Product = user_env['product.product']
        Category = user_env['product.category']
        product = Product.search([('x_care_id', '=', product_data['x_care_id'])], limit=1)

        if not product:
            category_name = product_data.get('category', 'All Products')
            category = Category.search([('name', '=', category_name)], limit=1)
            if not category:
                category = Category.create({'name': category_name})

            product = Product.create({
                'name': product_data.get('product_name', 'New Product'),
                'x_care_id': product_data['x_care_id'],
                'list_price': product_data.get('mrp', 0.0),
                'standard_price': product_data.get('cost', 0.0),
                'categ_id': category.id,
            })

        return product