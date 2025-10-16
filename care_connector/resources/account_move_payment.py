from datetime import datetime
from odoo import http,registry, fields
from .res_partner import PartnerUtility


class InvoicePaymentUtility:

    @classmethod
    def get_or_create_invoice_payment(cls,user_env,request_data):
        try:
            x_care_id = request_data.x_care_id
            amount = request_data.amount
            journal_input = request_data.journal_input.value
            payment_date = request_data.payment_date
            partner_data = request_data.partner_data
            partner_type = request_data.partner_type

            account_move_model = user_env["account.move"]
            account_journal_model = user_env['account.journal']
            account_payment_model = user_env['account.payment']
            a_p_r_transient_model = user_env['account.payment.register']

            account_journal = account_journal_model.sudo().search([
                '|', '|',
                ('name', 'ilike', journal_input),
                ('code', 'ilike', journal_input),
                ('type', '=', journal_input.lower())
            ], limit=1)

            if not account_journal:
                raise ValueError(f"No journal found for '{journal_input}'")
            existing_invoice = account_move_model.search([('x_care_id', '=', x_care_id)], limit=1)

            if existing_invoice:
                if existing_invoice.state != 'posted':
                    raise ValueError(f"Invoice {existing_invoice.name} is not posted")
                if existing_invoice.payment_state == 'paid':
                    raise ValueError(f"Invoice {existing_invoice.name} is already marked as paid. No further payment can be processed")

                ctx = {
                    'active_model': 'account.move',
                    'active_ids': [existing_invoice.id],
                    'active_id': existing_invoice.id,
                }

                account_payment = a_p_r_transient_model.with_context(ctx).create({
                    'amount': amount,
                    'journal_id': account_journal.id,
                    'payment_date': payment_date or fields.Date.today()
                })._create_payments()
                if not account_payment:
                    raise ValueError(f"Payment creation failed")

                return account_payment

            else:
                partner = PartnerUtility.get_or_create_partner(user_env, partner_data)
                if not partner:
                    raise ValueError(f"Create or retrieve partner is failed ")

                if partner_type.value == "vendor":
                    payment_type = 'outbound'
                    partner_type_str = 'supplier'
                else:
                    payment_type = 'inbound'
                    partner_type_str = 'customer'

                payment_vals = {
                    'payment_type': payment_type,
                    'partner_type': partner_type_str,
                    'partner_id': partner.id,
                    'amount': amount,
                    'journal_id': account_journal.id,
                    'date': payment_date or fields.Date.today(),
                }

                account_payment = account_payment_model.create(payment_vals)
                if not account_payment:
                    raise ValueError(f"Payment creation failed")
                account_payment.action_post()
                return account_payment

        except Exception as e:
            raise ValueError(str(e))