from odoo import models, fields
from datetime import date
import io
import xlsxwriter
import base64

class InvoiceHSNExcelWizard(models.TransientModel):
    _name = 'invoice.hsn.excel.wizard'
    _description = 'Invoice HSN Excel Report Wizard'

    date_from = fields.Date(string="Date From", required=True, default=lambda self: date.today().replace(day=1))
    date_to = fields.Date(string="Date To", required=True, default=lambda self: date.today())

    def action_print_excel(self):
        invoice_model = self.env['account.move']
        invoices = invoice_model.search([
            ('move_type', '=', 'out_invoice'),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('state', '=', 'posted'),
        ])

        invoices = invoices.filtered(lambda inv: any(line.product_id.l10n_in_hsn_code for line in inv.invoice_line_ids))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('HSN Report')

        sheet.set_column(0, 0, 12)   
        sheet.set_column(1, 1, 18)  
        sheet.set_column(2, 2, 25)   
        sheet.set_column(3, 3, 40)   
        sheet.set_column(4, 4, 25)   
        sheet.set_column(5, 5, 12)   
        sheet.set_column(6, 6, 10)  
        sheet.set_column(7, 7, 12)   
        sheet.set_column(8, 8, 15)   
        sheet.set_column(9, 9, 30)  
        sheet.set_column(10, 10, 15) 
        header = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1, 'align': 'center'})
        text = workbook.add_format({'border': 1})
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#B7DEE8'
        })

        sheet.merge_range('A1:K1', 'HSN INVOICE REPORT', title_format)

        headers = ['Date','Invoice No', 'Customer', 'Product','Account', 'HSN Code', 'Quantity', 'Unit Price', 'Subtotal','Tax','Total Amount']
        for col, title in enumerate(headers):
            sheet.write(2, col, title, header)

        row = 3  
        for inv in invoices:
            for line in inv.invoice_line_ids.filtered(lambda l: l.product_id.l10n_in_hsn_code):
                tax_percentages = ', '.join([f"{tax.name}" for tax in line.tax_ids])

                sheet.write(row, 0, str(inv.invoice_date or ''), text)
                sheet.write(row, 1, inv.name or '', text)
                sheet.write(row, 2, inv.partner_id.name or '', text)
                sheet.write(row, 3, line.product_id.display_name or '', text)
                sheet.write(row, 5, line.product_id.l10n_in_hsn_code or '', text)
                sheet.write(row, 6, line.quantity, text)
                sheet.write(row, 7, line.price_unit, text)
                sheet.write(row, 8, line.price_subtotal, text)
                sheet.write(row, 9, tax_percentages, text)
                sheet.write(row, 10, inv.amount_total, text)
                account_display = ''
                if line.account_id:
                    account_display = f"{line.account_id.code or ''} {line.account_id.name or ''}"
                sheet.write(row, 4, account_display.strip(), text)

                row += 1

        workbook.close()
        output.seek(0)
        file_data = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': f'Invoice_HSN_Report_{self.date_from}_{self.date_to}.xlsx',
            'type': 'binary',
            'datas': file_data,
            'res_model': 'invoice.hsn.excel.wizard',
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
