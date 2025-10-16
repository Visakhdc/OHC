import json
from odoo import http
from odoo.http import request, Response
from ..authentication.authenticate_user import UserAuthentication
from ..pydantic_models.account_move_payment import AccountMovePaymentApiRequest
from ..resources.account_move_payment import InvoicePaymentUtility


class AccountMovePayment(http.Controller):
    @http.route('/api/account/move/payment', type='json', auth='public', methods=['POST'], csrf=False)
    def account_move_payment(self, **kwargs):
        try:
            auth_header = request.httprequest.headers.get("Authorization")
            user_env = UserAuthentication.get_authenticated_user(auth_header)
            data = json.loads(request.httprequest.data)
            request_data = AccountMovePaymentApiRequest(**data)
            account_payment = InvoicePaymentUtility.get_or_create_invoice_payment(user_env, request_data)

            return Response(
                json.dumps({
                    "success": True,
                    "message": "Payment processed successfully",
                    "payment": {
                        "id": account_payment.id,
                        "name": account_payment.name,
                        "amount": account_payment.amount,
                        "partner": account_payment.partner_id.name,
                        "journal": account_payment.journal_id.name,
                        "payment_type": account_payment.payment_type,
                        "state": account_payment.state,
                        "date": str(account_payment.date),
                    },
                }),
                status=200,
                mimetype="application/json"
            )

        except ValueError as e:
            return Response(
                json.dumps({"success": False, "error": str(e)}),
                status=400,
                mimetype="application/json"
            )

        except Exception as err:
            return Response(
                json.dumps({"success": False, "error": f"Unexpected error: {str(err)}"}),
                status=500,
                mimetype="application/json"
            )