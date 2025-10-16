import json
from odoo import http
from odoo.http import request, Response
from ..authentication.authenticate_user import UserAuthentication
from ..pydantic_models.res_partner import PartnerData
from ..resources.res_partner import PartnerUtility


class ResPartner(http.Controller):

    @http.route('/api/add/partner', type='json', auth='public', methods=['POST'], csrf=False)
    def create_update_partner(self, **kwargs):
        try:
            auth_header = request.httprequest.headers.get("Authorization")
            user_env = UserAuthentication.get_authenticated_user(auth_header)
            data = json.loads(request.httprequest.data)
            request_data = PartnerData(**data)
            res_partner = PartnerUtility.get_or_create_partner(user_env, request_data)

            return Response(
                json.dumps({
                    "success": True,
                    "message": "Product created successfully",
                    "product": {
                        "product_id": res_partner.id,
                        "product_name": res_partner.name,
                        "x_care_id": res_partner.x_care_id,
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