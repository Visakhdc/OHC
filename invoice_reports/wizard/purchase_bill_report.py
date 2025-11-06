from odoo import models, fields
from datetime import date
import io
import xlsxwriter
import base64

class VendorBillExcelWizard(models.TransientModel):
    _name = 'vendor.bill.excel.wizard'
    _description = 'Vendor Bill Excel Report Wizard'

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
        ('purchase', 'Purchase Bills'),
        ('purchase_return', 'Purchase Returns'),
    ], string="Section", default='purchase', required=True)

    def action_print_excel(self):
        """Generate Excel report for vendor bills or purchase returns"""
        move_type = 'in_invoice' if self.section_type == 'purchase' else 'in_refund'

        bills = self.env['account.move'].search([
            ('move_type', '=', move_type),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('state', '=', 'posted'),
        ])

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Vendor Bill Report')

        sheet.set_column(0, 0, 12)
        sheet.set_column(1, 1, 18)
        sheet.set_column(2, 2, 25)
        sheet.set_column(3, 3, 40)
        sheet.set_column(4, 4, 25)
        sheet.set_column(5, 5, 10)
        sheet.set_column(6, 6, 12)
        sheet.set_column(7, 7, 15)
        sheet.set_column(8, 8, 20)
        sheet.set_column(9, 9, 30)
        sheet.set_column(10, 10, 15)
        sheet.set_column(11, 11, 15)

        header = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1, 'align': 'center'})
        text = workbook.add_format({'border': 1})
        title_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center',
            'valign': 'vcenter', 'bg_color': '#B7DEE8'
        })

        title_text = 'VENDOR BILL REPORT' if self.section_type == 'purchase' else 'PURCHASE RETURN REPORT'
        sheet.merge_range('A1:L1', title_text, title_format)

        headers = [
            'Date', 'Bill No', 'Vendor', 'Product', 'Account',
            'Qty', 'Unit Price', 'Subtotal', 'Tax %', 'Taxed Amount', 'Total Amount'
        ]
        for col, title in enumerate(headers):
            sheet.write(2, col, title, header)

        row = 3
        for bill in bills:
            for line in bill.invoice_line_ids:
                tax_names = ', '.join([tax.name for tax in line.tax_ids]) or '0%'
                tax_data = line.tax_ids.compute_all(
                    line.price_unit,
                    bill.currency_id,
                    line.quantity,
                    product=line.product_id,
                    partner=bill.partner_id
                )
                tax_amount = sum(t['amount'] for t in tax_data.get('taxes', []))

                sheet.write(row, 0, str(bill.invoice_date or ''), text)
                sheet.write(row, 1, bill.name or '', text)
                sheet.write(row, 2, bill.partner_id.name or '', text)
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
                sheet.write(row, 10, bill.amount_total, text)
                row += 1

        workbook.close()
        output.seek(0)
        file_data = base64.b64encode(output.read())

        section_label = "Purchase_Bills" if self.section_type == 'purchase' else "Purchase_Returns"
        file_name = f'{section_label}_Report_{self.date_from}_{self.date_to}.xlsx'

        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': file_data,
            'res_model': 'vendor.bill.excel.wizard',
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
