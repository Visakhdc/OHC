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
            tax_list = product_data.taxes
            category = CategoryUtility.get_or_create_category(user_env, category_data)
            categ_id = category.id if category else None

            taxes_ids = None
            if tax_list:
                taxes_ids = cls._get_or_create_taxes(user_env, tax_list)

            if not product:
                product_data_dict = {
                    'name': product_data.product_name if product_data.product_name else 'New Product',
                    'x_care_id': product_data.x_care_id,
                    'list_price': product_data.mrp if product_data.mrp else 0.0,
                    'standard_price': product_data.cost if product_data.cost else 0.0,
                    'categ_id': categ_id,
                }
                if taxes_ids:
                    product_data_dict['taxes_id'] = taxes_ids['sale_tax']
                    product_data_dict['supplier_taxes_id'] = taxes_ids['purchase_tax']

                product = product_product_model.create(product_data_dict)
            else:
                product.name = product_data.product_name
                product.list_price = product_data.mrp
                product.categ_id = categ_id
                product.standard_price = product_data.cost
                if taxes_ids:
                    product.taxes_id = taxes_ids['sale_tax']
                    product.supplier_taxes_id = taxes_ids['purchase_tax']

            return product

        except Exception as e:
            return {str(e)}

    @classmethod
    def _get_or_create_taxes(cls, user_env, tax_list):
        try:
            account_tax_model = user_env['account.tax']
            sale_tax_ids = []
            purchase_tax_ids = []
            for tax_data in tax_list:
                tax_name = f"{tax_data.tax_name} ({tax_data.tax_percentage}%)"
                for tax_type in ['sale', 'purchase']:
                    name = f"{tax_name} - {tax_type.capitalize()}"
                    existing_tax = account_tax_model.search([
                        ('name', '=', name),
                        ('amount', '=', tax_data.tax_percentage),
                        ('type_tax_use', '=', tax_type)
                    ], limit=1)
                    if not existing_tax:
                        existing_tax = account_tax_model.create({
                            'name': name,
                            'amount': tax_data.tax_percentage,
                            'type_tax_use': tax_type,
                        })
                    (sale_tax_ids if tax_type == 'sale' else purchase_tax_ids).append(existing_tax.id)
            taxes_dict = {
                "purchase_tax": purchase_tax_ids,
                "sale_tax": sale_tax_ids
            }
            return taxes_dict

        except Exception as e:
            raise {str(e)}