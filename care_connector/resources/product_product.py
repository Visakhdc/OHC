from odoo.http import request
from .product_category import CategoryUtility

class ProductUtility:

    @classmethod
    def get_or_create_product(cls,user_env, product_data):
        """Retrieve or create product"""
        try:
            product_product_model = user_env['product.product']
            product = product_product_model.search([('x_care_id', '=', product_data.x_care_id)], limit=1)
            category_data = product_data.category
            category = CategoryUtility.get_or_create_category(user_env, category_data)
            categ_id = None
            if category:
                categ_id = category.id

            if not product:
                product = product_product_model.create({
                    'name': product_data.product_name if product_data.product_name else 'New Product',
                    'x_care_id': product_data.x_care_id,
                    'list_price': product_data.mrp if product_data.mrp else 0.0,
                    'standard_price': product_data.cost if product_data.cost else 0.0,
                    'categ_id': categ_id,
                })
            else:
                product.name = product_data.product_name
                product.list_price = product_data.mrp
                product.categ_id = categ_id
                product.standard_price = product_data.cost

            return product

        except Exception as e:
            return {'error': f"Error while creating/updating product: {str(e)}"}