# -*- coding: utf-8 -*-
import io
import xlsxwriter
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError

class ImportShipmentReportWizard(models.TransientModel):
    _name = 'import.shipment.report.wizard'
    _description = 'Import Shipment Report Wizard'

    def _get_default_shipment_ids(self):
        return self.env.context.get('active_ids', [])

    shipment_ids = fields.Many2many('import.shipment', string='Import Shipments', default=_get_default_shipment_ids)

    def action_generate_excel(self):
        shipments = self.shipment_ids
        if not shipments:
            raise UserError(_("No import shipments selected."))

        # Group by product and aggregate data
        product_data = {}
        for shipment in shipments:
            product_id = shipment.product_id.id
            if product_id not in product_data:
                product_data[product_id] = {
                    'product': shipment.product_id,
                    'stock_qty': shipment.stock_qty,
                    'free_qty': shipment.free_qty,
                    'ordered_qty': 0.0,
                }
            product_data[product_id]['ordered_qty'] += shipment.ordered_qty

        # Create Excel file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Import Shipment Report')

        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F81BD',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })

        cell_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })

        # Set column widths
        worksheet.set_column('A:A', 40)  # Product
        worksheet.set_column('B:D', 15)  # Stock Qty, Free Qty, Ordered Qty

        # Write headers
        headers = ['Ürün', 'Stok Miktarı', 'Free Miktar', 'Sipariş Miktarı']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)

        # Write data
        row = 1
        for product_id, data in product_data.items():
            product = data['product']
            worksheet.write(row, 0, product.display_name or '', cell_format)
            worksheet.write(row, 1, data['stock_qty'], cell_format)
            worksheet.write(row, 2, data['free_qty'], cell_format)
            worksheet.write(row, 3, data['ordered_qty'], cell_format)
            row += 1

        workbook.close()
        output.seek(0)

        # Create attachment
        filename = 'import_shipment_report.xlsx'
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': output.read(),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
