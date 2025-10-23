from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_care_id = fields.Char(string='Care ID')


class AccountMoveLines(models.Model):
    _inherit = 'account.move.line'

    x_care_id = fields.Char(string='Care Ml ID')
    received_qty = fields.Float(string='Quantity', store=True)
    free_qty = fields.Float(string='Free Quantity')

    @api.onchange('free_qty')
    def _onchange_free_qty(self):
        self.quantity = self.quantity - self.free_qty

    @api.onchange('received_qty')
    def _onchange_received_qty(self):
        self.quantity = self.received_qty - self.free_qty