from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_care_id = fields.Char(string='Care ID')


class AccountMoveLines(models.Model):
    _inherit = 'account.move.line'

    x_care_id = fields.Char(string='Care Ml ID')