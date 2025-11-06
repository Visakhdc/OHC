from odoo import models, fields

class AccountDiscount(models.Model):
    _name = 'account.discount'
    _description = 'Predefined Discount'

    name = fields.Char(string="Discount Name", required=True)
    x_care_id = fields.Char(string="Care ID", readonly=True)
    discount_group = fields.Many2one('account.discount.groups', string="Discount Group", ondelete='cascade')
    amount = fields.Float(string="Discount Amount", required=True)


