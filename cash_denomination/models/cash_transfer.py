from odoo import models, fields, api

class CashTransfer(models.Model):
    _name = 'cash.transfer'
    _description = 'Cash Transfer'
    _order = 'id desc'

    name = fields.Many2one('res.users',string='Transferred By', )
    from_counter = fields.Many2one('cash.counter', string='From Counter', readonly=True)
    to_counter = fields.Many2one('cash.counter', string='To Counter', readonly=True)
    amount = fields.Integer(string='Cash')
    remarks = fields.Char(string='Remarks', readonly=True)
    date = fields.Datetime(string='Transfer Date', default=fields.Datetime.now,)
    transfer_to_user = fields.Many2one('res.users', string='To User', readonly=True)
