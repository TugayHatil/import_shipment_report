# -*- coding: utf-8 -*-
import io
import xlsxwriter
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError

class ImportShipment(models.Model):
    _inherit = 'import.shipment'

    stock_qty = fields.Float(
        string='Stock Qty',
        compute='_compute_stock_qty',
        store=True,
        readonly=True,
        group_operator='avg',
        help="Current stock quantity from product inventory"
    )

    free_qty = fields.Float(
        string='Free Qty',
        compute='_compute_free_qty',
        store=True,
        readonly=True,
        group_operator='avg',
        help="Free quantity (available - reserved) from product inventory"
    )

    @api.depends('product_id')
    def _compute_stock_qty(self):
        for record in self:
            if record.product_id:
                record.stock_qty = record.product_id.qty_available
            else:
                record.stock_qty = 0.0

    @api.depends('product_id')
    def _compute_free_qty(self):
        for record in self:
            if record.product_id:
                record.free_qty = record.product_id.free_qty
            else:
                record.free_qty = 0.0

    def action_download_excel_report(self):
        """Download Excel report directly without wizard"""
        # Get all shipments
        shipments = self.env['import.shipment'].search([])
        
        if not shipments:
            raise UserError(_("No import shipments found."))

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

        # Create attachment with proper Excel extension
        filename = 'import_shipment_report.xlsx'
        excel_data = output.getvalue()
        
        # Encode data properly for Odoo
        import base64
        encoded_data = base64.b64encode(excel_data)
        
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': encoded_data.decode('utf-8'),
            'res_model': self._name,
            'res_id': 1,  # Use fixed res_id to avoid singleton error
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
