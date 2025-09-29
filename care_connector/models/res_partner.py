from odoo import fields, models

class ResPartner(models.Model):
    """Inheriting res.partner"""
    _inherit = "res.partner"

    care_partner_id = fields.Char(string="Care Partner ID")