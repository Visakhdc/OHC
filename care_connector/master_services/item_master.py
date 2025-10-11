from odoo.http import request

class ItemMasterService:

    @staticmethod
    def get_or_create_product(user_env, product_data):
        """Retrieve or create product"""

        product_product_model = user_env['product.product']
        product_category_model = user_env['product.category']
        product = product_product_model.search([('x_care_id', '=', product_data.x_care_id)], limit=1)

        if not product:
            category_name = product_data.category if product_data.category else 'All'
            category = product_category_model.search([('name', '=', category_name)], limit=1)
            if not category:
                category = product_category_model.create({'name': category_name})

            product = product_product_model.create({
                'name': product_data.product_name if product_data.product_name else 'New Product',
                'x_care_id': product_data.x_care_id,
                'list_price': product_data.mrp if product_data.mrp else 0.0,
                'standard_price': product_data.cost if product_data.cost else 0.0,
                'categ_id': category.id,
            })
        else:
            product.list_price = product_data.mrp
            product.standard_price = product_data.cost

        return product