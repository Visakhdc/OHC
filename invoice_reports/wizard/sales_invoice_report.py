from odoo import models, fields
from datetime import date
import io
import xlsxwriter
import base64

class SalesInvoiceExcelWizard(models.TransientModel):
    _name = 'sales.invoice.excel.wizard'
    _description = 'Sales Invoice Excel Report Wizard'

    date_from = fields.Date(
        string="Date From",
        required=True,
        default=lambda self: date.today().replace(day=1)
    )
    date_to = fields.Date(
        string="Date To",
        required=True,
        default=lambda self: date.today()
    )

    section_type = fields.Selection([
        ('sales', 'Sales'),
        ('sales_return', 'Sales Return'),
    ], string="Section", default='sales', required=True)

    def action_print_excel(self):
        """Generate Excel report for sales or sales returns"""
        move_type = 'out_invoice' if self.section_type == 'sales' else 'out_refund'

        invoices = self.env['account.move'].search([
            ('move_type', '=', move_type),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('state', '=', 'posted'),
        ])

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Sales Invoice Report')

        sheet.set_column(0, 0, 12)
        sheet.set_column(1, 1, 18)
        sheet.set_column(2, 2, 25)
        sheet.set_column(3, 3, 40)
        sheet.set_column(4, 4, 25)
        sheet.set_column(5, 5, 12)
        sheet.set_column(6, 6, 10)
        sheet.set_column(7, 7, 12)
        sheet.set_column(8, 8, 25)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 20)

        header = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1, 'align': 'center'})
        text = workbook.add_format({'border': 1})
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#B7DEE8'
        })

        title_text = 'SALES INVOICE REPORT' if self.section_type == 'sales' else 'SALES RETURN REPORT'
        sheet.merge_range('A1:K1', title_text, title_format)

        headers = [
            'Date', 'Invoice No', 'Customer', 'Product', 'Account',
            'Quantity', 'Unit Price', 'Subtotal', 'Tax', 'Tax Amount', 'Total Amount'
        ]
        for col, title in enumerate(headers):
            sheet.write(2, col, title, header)

        row = 3
        for inv in invoices:
            for line in inv.invoice_line_ids:
                tax_names = ', '.join([tax.name for tax in line.tax_ids]) or '0%'
                tax_data = line.tax_ids.compute_all(
                    line.price_unit,
                    inv.currency_id,
                    line.quantity,
                    product=line.product_id,
                    partner=inv.partner_id
                )
                tax_amount = sum(t['amount'] for t in tax_data.get('taxes', []))

                sheet.write(row, 0, str(inv.invoice_date or ''), text)
                sheet.write(row, 1, inv.name or '', text)
                sheet.write(row, 2, inv.partner_id.name or '', text)
                sheet.write(row, 3, line.product_id.display_name or '', text)

                account_display = ''
                if line.account_id:
                    account_display = f"{line.account_id.code or ''} {line.account_id.name or ''}"
                sheet.write(row, 4, account_display.strip(), text)

                sheet.write(row, 5, line.quantity, text)
                sheet.write(row, 6, line.price_unit, text)
                sheet.write(row, 7, line.price_subtotal, text)
                sheet.write(row, 8, tax_names, text)
                sheet.write(row, 9, tax_amount, text)
                sheet.write(row, 10, inv.amount_total, text)
                row += 1

        workbook.close()
        output.seek(0)
        file_data = base64.b64encode(output.read())

        section_label = "Sales" if self.section_type == 'sales' else "Sales_Return"
        file_name = f"{section_label}_Invoice_Report_{self.date_from}_{self.date_to}.xlsx"

        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': file_data,
            'res_model': 'sales.invoice.excel.wizard',
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
