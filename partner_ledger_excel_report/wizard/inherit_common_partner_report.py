from odoo import models, fields, api
from odoo.tools.misc import get_lang
import io
import base64
import xlsxwriter
from datetime import datetime

class AccountingCommonPartnerReportInherit(models.TransientModel):
    _inherit = 'account.common.partner.report'

    partner_ids = fields.Many2many('res.partner', string='Partners')



    def _build_contexts(self, data):
        """Extend original context with partner filter fields."""
        result = super()._build_contexts(data)
        if data['form'].get('partner_ids'):
            result['partner_ids'] = data['form']['partner_ids']
        form = data.get('form', {})
        if form.get('partner_ids'):
            result['partner_ids'] = [p.id for p in self.partner_ids]
        result['partner_ids'] = data['form'].get('partner_ids', [])
        return result

    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')

        data['form'] = self.read([
            'date_from',
            'date_to',
            'journal_ids',
            'target_move',
            'company_id',
            'partner_ids'
        ])[0]

        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
        return self.with_context(discard_logo_check=True)._print_report(data)
