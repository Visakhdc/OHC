import json
from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero

class AccountMove(models.Model):
    _inherit = "account.move"

    discount_list = fields.Char(
        compute='_compute_discount_summary',
        string="Discount",
        store=False
    )

    @api.depends('invoice_line_ids.account_discount')
    def _compute_discount_summary(self):
        for move in self:
            discount_dict = {}
            for line in move.invoice_line_ids:
                currency = line.currency_id or line.company_id.currency_id
                if line.account_discount:
                    if float_is_zero(line.account_discount.amount, precision_rounding=currency.rounding
                                     ) or float_is_zero(line.price_unit, precision_rounding=currency.rounding):
                        discount_percent = 0.0
                    else:
                        discount_percent = (line.account_discount.amount / line.price_unit) * 100
                    line.discount = discount_percent

                    discount_dict[line.account_discount.discount_group.name] = line.account_discount.amount

            discount_str = '\n'.join(f"{k} : {v}" for k, v in discount_dict.items())
            move.discount_list = discount_str

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    account_discount = fields.Many2one(
        'account.discount',
        string="Discount"
    )