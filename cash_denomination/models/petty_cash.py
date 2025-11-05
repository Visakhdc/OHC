from odoo import models, fields, api

class PettyCash(models.Model):
    _name = 'petty.cash'  
    _description = 'Petty Cash' 
    _rec_name = "from_user"
    _order = 'id desc'

    date = fields.Date(string='Date', readonly=True)
    from_user = fields.Many2one('res.users',string='From User',readonly=True)
    to_user = fields.Many2one('res.users',string='To user',readonly=True)
    counter = fields.Char(string='Counter',readonly=True)
    line_ids = fields.One2many('petty.cash.line', 'petty_cash_id', string='Denomination Lines',readonly=True)
    grand_total = fields.Float(string='Total', compute='_comput_grand_total', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('accepted', 'Accepcted'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True)

    @api.depends('line_ids.sub_total')
    def _comput_grand_total(self):
        for record in self:
            self.grand_total=sum(record.line_ids.mapped('sub_total'))

    class PettyCashLine(models.Model):
        _name = 'petty.cash.line'
        _description = 'Petty Cash Line'

        petty_cash_id = fields.Many2one('petty.cash', string='Petty Cash', ondelete='cascade')
        counts = fields.Integer(string='Counts', required=True,readonly=True)
        currency = fields.Selection(
            [('1','1'),('2','2'),('5','5'),('10','10'),('20','20'),('50','50'),('100','100'),('200','200'),('500','500')],
            string='Currency', required=True,readonly=True)
        sub_total = fields.Float(string='Sub Total', compute='_compute_sub_total', store=True,readonly=True)

        
        @api.depends('counts', 'currency')
        def _compute_sub_total(self):
            for line in self:
                line.sub_total = line.counts * int(line.currency)