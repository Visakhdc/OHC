from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = "product.template"

    care_product_id = fields.Char(string="Care ID")