from odoo import models, fields, api

class AccountDiscountGroups(models.Model):
    _name = 'account.discount.groups'
    _description = 'Discount Groups'

    name = fields.Char(string="Group Name", required=True)
    x_care_id = fields.Char(string="Care ID", readonly=True)
    incoming = fields.Many2one(
        'account.account',
        string='Incoming Account'
    )
    outgoing = fields.Many2one(
        'account.account',
        string='Outgoing Account'
    )