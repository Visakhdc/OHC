# -*- coding: utf-8 -*-
from odoo import models, api

class AccountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def _query_get(self, domain=None):

        ctx = dict(self._context)
        partner_ids = ctx.get('partner_ids')
        if partner_ids and not hasattr(partner_ids, 'ids'):
            ctx['partner_ids'] = self.env['res.partner'].browse(partner_ids)
        self = self.with_context(ctx)
        return super(AccountMoveLineInherit, self)._query_get(domain)
