from odoo import fields, models

class ResPartner(models.Model):
    """Inheriting res.partner"""
    _inherit = "res.partner"

    x_care_id = fields.Char(string="Care Partner ID")