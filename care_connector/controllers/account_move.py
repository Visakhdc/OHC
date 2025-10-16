import json
from odoo.http import request, Response
from odoo import http
from ..pydantic_models.account_move import AccountMoveApiRequest
from ..authentication.authenticate_user import UserAuthentication
from ..resources.account_move import AccountUtility

class AccountMove(http.Controller):

    @http.route('/api/account/move', type='json', auth='public', methods=['POST'], csrf=False)
    def account_move(self, **kwargs):
        try:
            auth_header = request.httprequest.headers.get("Authorization")
            user_env = UserAuthentication.get_authenticated_user(auth_header)
            data = json.loads(request.httprequest.data)
            request_data = AccountMoveApiRequest(**data)
            account_move = AccountUtility.get_or_create_account_move(user_env, request_data)

            return Response(
                json.dumps({
                    "success": True,
                    "message": "Invoice created successfully",
                    "payment": {
                        "id": account_move.id,
                        "name": account_move.name,
                        "partner": account_move.partner_id.name,
                        "invoice_date": str(account_move.invoice_date),
                        "amount_total": account_move.amount_total,
                    },
                }),
                status=200,
                mimetype="application/json"
            )

        except ValueError as e:
            return Response(
                json.dumps({"success": False, "error": str(e)}),
                status=400, mimetype="application/json"
            )

        except Exception as err:
            return Response(
                json.dumps({"success": False, "error": f"Unexpected error: {str(err)}"}),
                status=500, mimetype="application/json"
            )

    @http.route('/api/account/move/return', type='json', auth='public', methods=['POST'], csrf=False)
    def account_move_return(self, **kwargs):
        try:
            auth_header = request.httprequest.headers.get("Authorization")
            user_env = UserAuthentication.get_authenticated_user(auth_header)
            data = json.loads(request.httprequest.data)
            request_data = AccountMoveApiRequest(**data)
            account_move = AccountUtility.get_or_create_account_move_return(user_env, request_data)

            return Response(
                json.dumps({
                    "success": True,
                    "message": "Invoice created successfully",
                    "payment": {
                        "id": account_move.id,
                        "name": account_move.name,
                        "partner": account_move.partner_id.name,
                        "invoice_date": str(account_move.invoice_date),
                        "amount_total": account_move.amount_total,
                    },
                }),
                status=200,
                mimetype="application/json"
            )

        except ValueError as e:
            return Response(
                json.dumps({"success": False, "error": str(e)}),
                status=400,mimetype="application/json"
            )

        except Exception as err:
            return Response(
                json.dumps({"success": False, "error": f"Unexpected error: {str(err)}"}),
                status=500,mimetype="application/json"
            )