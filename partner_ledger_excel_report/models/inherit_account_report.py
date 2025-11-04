from odoo import models, fields
import io
import base64
import xlsxwriter
from datetime import datetime, date
from odoo.http import request



class AccountingCommonPartnerReportInherit(models.Model):
    _inherit = 'account.report'

    partner_ids = fields.Many2many('res.partner', string='Partners')

    def get_headers(self):
        return [
            "Date",
            "Journal",
            "Partner",
            "Reference",
            "Account",
            "Label",
            "Debit",
            "Credit",
            "Balance",
        ]

    def get_report_styles(self, workbook):
        return {
            'header': workbook.add_format({
                'bold': True,
                'bg_color': '#DCE6F1',
                'font_name': 'Arial',
                'font_size': 13,
                'align': 'center',
                'valign': 'vcenter',
                'border': 1
            }),
            'cell_left': workbook.add_format({
                'font_name': 'Arial',
                'font_size': 11,
                'align': 'left',
                'valign': 'vcenter',
                'border': 1
            }),
            'cell_center': workbook.add_format({
                'font_name': 'Arial',
                'font_size': 11,
                'align': 'center',
                'valign': 'vcenter',
                'border': 1
            }),
            'cell_number': workbook.add_format({
                'font_name': 'Arial',
                'font_size': 11,
                'align': 'right',
                'valign': 'vcenter',
                'border': 1,
                'num_format': '#,##0.00'
            }),
            'title': workbook.add_format({
                'bold': True,
                'font_name': 'Arial',
                'font_size': 16,
                'align': 'center',
                'valign': 'vcenter'
            }),
            'date': workbook.add_format({
                'num_format': 'dd/mm/yyyy',
                'font_name': 'Arial',
                'font_size': 10,
                'align': 'center',
                'border': 1
            }),
        }



    def get_report_domain(self):
        domain = []

        if self.date_from and self.date_to:
            domain += [
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to),
            ]
        elif self.date_from:  
            domain.append(('date', '>=', self.date_from))
        elif self.date_to:  
            domain.append(('date', '<=', self.date_to))

        if self.journal_ids:
            domain.append(('journal_id', 'in', self.journal_ids.ids))

        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))

        return domain




    def button_download_xlsx_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("Partner Ledger")
        styles = self.get_report_styles(workbook)
        user = request.env.user
        account_move_line = self.env['account.move.line']

        worksheet.merge_range('C1:F1', 'Partner Ledger Report', styles['title'])
        worksheet.freeze_panes(2, 0)
        worksheet.set_column('A:I', 20)

        headers = self.get_headers()
        for col, header in enumerate(headers):
            worksheet.write(1, col, header, styles['header'])

        row = 2
        domain = self.get_report_domain()
        lines = account_move_line.with_user(user).search(domain, order='date asc')

        for line in lines:
            worksheet.write(row, 0, line.date, styles['date'])
            worksheet.write(row, 1, line.journal_id.name or '', styles['cell_left'])
            worksheet.write(row, 2, line.partner_id.name or '', styles['cell_left'])
            worksheet.write(row, 3, line.move_id.ref or '', styles['cell_left'])
            worksheet.write(row, 4, line.account_id.display_name or '', styles['cell_left'])
            worksheet.write(row, 5, line.name or '', styles['cell_left'])
            worksheet.write(row, 6, line.debit, styles['cell_number'])
            worksheet.write(row, 7, line.credit, styles['cell_number'])
            worksheet.write(row, 8, line.balance, styles['cell_number'])
            row += 1

        workbook.close()
        output.seek(0)
        file_name = f"Partner_Ledger_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        attachment_id = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'store_fname': file_name,
            'res_model': self._name,
            'res_id': self.id,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment_id.id}',
            'target': 'self',
        }
