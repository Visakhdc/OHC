import base64
import json
from odoo.http import request, Response, Controller
from odoo.exceptions import AccessDenied
from odoo import http, registry
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
                if data['partner_data']:
                    partner_id = self.get_or_create_partner(data['partner_data'],user_env)

                    invoice_lines = []
                    for line in data['invoice_items']:
                        if line["product"]:
                            product = self.get_or_create_product(line["product"], user_env)

                            invoice_lines.append((0, 0, {
                                'product_id': product.id,
                                'quantity': line.get('quantity', 1),
                                'price_unit': line.get('sale_price', 0.0),
                                'x_care_id': line.get('x_care_id'),
                            }))

                    if partner_id and invoice_lines:
                        move_type = "out_invoice"
                        invoice_date = datetime.strptime(data['invoice_date'], "%d-%m-%Y").date()
                        if data['bill_type']=="vendor":
                            move_type = "in_invoice"
                        move = user_env['account.move'].create({
                            'move_type': move_type,
                            'partner_id': partner_id.id,
                            'x_care_id': data['x_care_id'],
                            'invoice_date': invoice_date,
                            'invoice_line_ids': invoice_lines,
                        })

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
                        "product_id": partner_id.id,
                        "product_name": partner_id.name,
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