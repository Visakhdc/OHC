import json
from odoo import http
from odoo.http import request, Response
from ..authentication.authenticate_user import UserAuthentication
from ..pydantic_models.product_product import ProductData
from ..resources.product_product import ProductUtility


class ProductProduct(http.Controller):

    @http.route('/api/add/product', type='json', auth='public', methods=['POST'], csrf=False)
    def create_update_product(self, **kwargs):
        try:
            auth_header = request.httprequest.headers.get("Authorization")
            user_env = UserAuthentication.get_authenticated_user(auth_header)
            data = json.loads(request.httprequest.data)
            request_data = ProductData(**data)
            product_product = ProductUtility.get_or_create_product(user_env, request_data)

            return Response(
                json.dumps({
                    "success": True,
                    "message": "Product created successfully",
                    "product": {
                        "product_id": product_product.id,
                        "product_name": product_product.name,
                        "x_care_id": product_product.x_care_id,
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