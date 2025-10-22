from odoo import models, fields, api

class CashDenomination(models.Model):
    _name = 'cash.denomination'  
    _description = 'Cash Denomination' 
    _rec_name = "user"
    _order = 'id desc'

    date = fields.Date(string='Date', readonly=True)
    user = fields.Many2one('res.users',string='Person',readonly=True)
    counter = fields.Integer(string='Counter',readonly=True)
    line_ids = fields.One2many('cash.denomination.line', 'denomination_id', string='Denomination Lines',readonly=True)
    grand_total = fields.Float(string='Total', compute='_comput_grand_total', store=True)
    transfer_line_ids = fields.One2many('cash.denomination.transfer.line', 'denomination_id', string='Cash Transfer Lines', readonly=True)

    @api.depends('line_ids.sub_total')
    def _comput_grand_total(self):
        for record in self:
            self.grand_total=sum(record.line_ids.mapped('sub_total'))
    
class CashDenominationLine(models.Model):
    _name = 'cash.denomination.line'
    _description = 'Cash Denomination Line'

    denomination_id = fields.Many2one('cash.denomination', string='Cash Denomination', ondelete='cascade')
    counts = fields.Integer(string='Counts', required=True,readonly=True)
    currency = fields.Selection(
        [('1','1'),('2','2'),('5','5'),('10','10'),('20','20'),('50','50'),('100','100'),('200','200'),('500','500')],
        string='Currency', required=True,readonly=True)
    sub_total = fields.Float(string='Sub Total', compute='_compute_sub_total', store=True,readonly=True)

    
    @api.depends('counts', 'currency')
    def _compute_sub_total(self):
        for line in self:
            line.sub_total = line.counts * int(line.currency)



class CashDenominationTransferLine(models.Model):
    _name = 'cash.denomination.transfer.line'
    _description = 'Cash Denomination Transfer Line'

    denomination_id = fields.Many2one('cash.denomination', string='Cash Denomination', ondelete='cascade')
    from_counter = fields.Many2one('cash.counter', string='From Counter', readonly=True)
    to_counter = fields.Many2one('cash.counter', string='To Counter', readonly=True)
    amount = fields.Float(string='Amount', readonly=True)
    remarks = fields.Char(string='Remarks', readonly=True)
    transfer_date = fields.Datetime(string='Transfer Date', readonly=True)
    to_user = fields.Many2one('res.users', string='To User')
