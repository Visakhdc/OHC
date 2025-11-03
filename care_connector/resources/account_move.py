from datetime import datetime
from .res_partner import PartnerUtility
from .product_product import ProductUtility

class AccountUtility:

    @classmethod
    def get_or_create_account_move(cls,user_env, request_data):
        try:
            x_care_id = request_data.x_care_id
            partner_data = request_data.partner_data
            invoice_items = request_data.invoice_items

            account_move = user_env["account.move"]
            existing_invoice = account_move.search([('x_care_id', '=', x_care_id)], limit=1)

            if existing_invoice:
                raise ValueError("Invoice already exists")

            res_partner = PartnerUtility.get_or_create_partner(user_env, partner_data)
            bill_type = request_data.bill_type.value
            invoice_date = request_data.invoice_date
            due_date = request_data.due_date

            move_type = "out_invoice"
            if bill_type == "vendor":
                move_type = "in_invoice"

            move_data_dict = {
                "x_care_id": x_care_id,
                "res_partner": res_partner,
                "invoice_items": invoice_items,
                "invoice_date": invoice_date,
                "due_date": due_date,
                "move_type": move_type,
            }
            account_move = cls._create_account_move(user_env, move_data_dict)
            if not account_move:
                raise ValueError("Failed to create the Invoice")
            return account_move
        except Exception as e:
            raise Exception(f"{str(e)}")

    @classmethod
    def get_or_create_account_move_return(cls,user_env, request_data):
        try:
            x_care_id = request_data.x_care_id
            partner_data = request_data.partner_data
            invoice_items = request_data.invoice_items
            reason = request_data.reason if request_data.reason else None
            account_move = user_env["account.move"]
            a_m_r_model = user_env['account.move.reversal']
            existing_invoice = account_move.search([('x_care_id', '=', x_care_id)], limit=1)

            if existing_invoice:
                existing_credit_note = account_move.search([
                    ("reversed_entry_id", "=", existing_invoice.id)
                ], limit=1)
                if existing_credit_note:
                    raise ValueError(f"This invoice has already been reversed and a credit note [{str(existing_credit_note.name)}] exists.")

                reversal_wizard = a_m_r_model.with_context(
                    {'active_ids': [existing_invoice.id], 'active_id': existing_invoice.id,
                     'active_model': 'account.move'}).create({
                    'reason': reason,
                    'journal_id': existing_invoice.journal_id.id,
                })
                if not reversal_wizard:
                    raise ValueError("Failed to reverse the Invoice")
                reversal_wizard.reverse_moves()

                credit_note = account_move.search([
                    ('reversed_entry_id', '=', existing_invoice.id),
                    ('move_type', 'in', ['out_refund', 'in_refund'])
                ], limit=1)

                if not credit_note:
                    raise ValueError("Failed to create Credit note")

                credit_note.x_care_id = f"RE/{credit_note.x_care_id}"
                credit_note.action_post()
                return credit_note

            else:
                res_partner = PartnerUtility.get_or_create_partner(user_env, partner_data)
                bill_type = request_data.bill_type.value
                invoice_date = request_data.invoice_date
                due_date = request_data.due_date

                move_type = "out_refund"
                if bill_type == "vendor":
                    move_type = "in_refund"

                move_data_dict = {
                    "x_care_id": x_care_id,
                    "res_partner": res_partner,
                    "invoice_items": invoice_items,
                    "invoice_date": invoice_date,
                    "due_date": due_date,
                    "move_type": move_type,
                }
                account_move = cls._create_account_move(user_env, move_data_dict)
                if not account_move.id:
                    raise ValueError(f"Failed to create the Invoice, err:{str(account_move)}")
                return {
                    "success": True,
                    "invoice_id": account_move.id,
                    "invoice_name": account_move.name,
                }

        except Exception as e:
            raise Exception(f"{str(e)}")


    @classmethod
    def _create_account_move(cls,user_env,move_data):
        try:
            x_care_id = move_data.get("x_care_id")
            res_partner = move_data.get("res_partner")
            invoice_items = move_data.get("invoice_items")
            invoice_date = move_data.get("invoice_date")
            due_date = move_data.get("due_date")
            move_type = move_data.get("move_type")
            account_move_model = user_env['account.move']
            res_partner_model = user_env['res.partner']

            invoice_line_list = []
            for item in invoice_items:
                product_data = item.product_data
                product = ProductUtility.get_or_create_product(user_env, product_data)

                if not product.id:
                    raise ValueError(f"Failed to create or retrieve the product, err:{str(product)}")

                agent_ids = []
                if item.agent_id:
                    agent_res_partner = res_partner_model.search([('x_care_id', '=', item.agent_id)], limit=1)
                    if agent_res_partner and agent_res_partner.agent:
                        agent_ids = [(0, 0, {
                            'agent_id': agent_res_partner.id,
                            'commission_id': agent_res_partner.commission_id.id if agent_res_partner.commission_id else False,
                        })]
                invoice_line_list.append((0, 0, {
                    'product_id': product.id,
                    'quantity': item.quantity,
                    'received_qty': item.quantity,
                    'price_unit': item.sale_price,
                    'x_care_id': item.x_care_id,
                    'agent_ids': agent_ids,
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
            if not account_move:
                raise ValueError("Failed to create the Invoice")

            if move_type == 'out_invoice':
                account_move.action_post()
            return account_move

        except Exception as e:
            raise Exception(f"{str(e)}")
