from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    care_inv_ref = fields.Char(string='Care ID')


class AccountMoveLines(models.Model):
    _inherit = 'account.move.line'

    care_ml_ref = fields.Char(string='Care Ml ID')