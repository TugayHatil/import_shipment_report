# -*- coding: utf-8 -*-
import io
import xlsxwriter
import logging
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ImportShipment(models.Model):
    _inherit = 'import.shipment'

    stock_qty = fields.Float(
        string='Stock Qty',
        compute='_compute_stock_qty',
        store=False,  # Change to store=False to force real-time computation
        readonly=True,
        group_operator='avg',
        help="Current stock quantity from filtered locations only"
    )

    free_qty = fields.Float(
        string='Free Qty',
        compute='_compute_free_qty',
        store=False,  # Change to store=False to force real-time computation
        readonly=True,
        group_operator='avg',
        help="Free quantity (available - reserved) from filtered locations only"
    )

    @api.depends('product_id')
    def _compute_stock_qty(self):
        _logger.info("=== STARTING STOCK_QY COMPUTATION ===")
        
        # First, let's check if any locations are marked
        all_marked_locations = self.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('include_in_stock_qty', '=', True)
        ])
        
        _logger.info(f"TOTAL MARKED LOCATIONS IN SYSTEM: {len(all_marked_locations)}")
        for loc in all_marked_locations:
            _logger.info(f"  - {loc.name} (ID: {loc.id})")
        
        for record in self:
            _logger.info(f"Computing stock_qty for record {record.id}, product {record.product_id.name if record.product_id else 'None'}")
            
            if not record.product_id:
                record.stock_qty = 0.0
                _logger.info(f"No product for record {record.id}, setting stock_qty to 0")
                continue
                
            # Force return 0 if no locations are marked
            if not all_marked_locations:
                record.stock_qty = 0.0
                _logger.info(f"NO MARKED LOCATIONS FOUND - FORCING stock_qty to 0 for {record.product_id.name}")
                continue
                
            # Use SQL query for more reliable calculation
            self.env.cr.execute("""
                SELECT COALESCE(SUM(sq.quantity), 0)
                FROM stock_quant sq
                JOIN stock_location sl ON sq.location_id = sl.id
                WHERE sq.product_id = %s
                AND sl.usage = 'internal'
                AND sl.include_in_stock_qty = true
                AND sq.quantity > 0
            """, (record.product_id.id,))
            
            result = self.env.cr.fetchone()
            total_qty = result[0] if result and result[0] else 0.0
            
            record.stock_qty = total_qty
            _logger.info(f"Final stock_qty for {record.product_id.name}: {total_qty} (SQL query result)")
        
        _logger.info("=== STOCK_QY COMPUTATION COMPLETED ===")

    @api.depends('product_id')
    def _compute_free_qty(self):
        _logger.info("=== STARTING FREE_QY COMPUTATION ===")
        
        # First, let's check if any locations are marked
        all_marked_locations = self.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('include_in_stock_qty', '=', True)
        ])
        
        _logger.info(f"TOTAL MARKED LOCATIONS IN SYSTEM: {len(all_marked_locations)}")
        
        for record in self:
            _logger.info(f"Computing free_qty for record {record.id}, product {record.product_id.name if record.product_id else 'None'}")
            
            if not record.product_id:
                record.free_qty = 0.0
                _logger.info(f"No product for record {record.id}, setting free_qty to 0")
                continue
                
            # Force return 0 if no locations are marked
            if not all_marked_locations:
                record.free_qty = 0.0
                _logger.info(f"NO MARKED LOCATIONS FOUND - FORCING free_qty to 0 for {record.product_id.name}")
                continue
                
            # Use SQL query for more reliable calculation
            self.env.cr.execute("""
                SELECT COALESCE(SUM(sq.quantity - sq.reserved_quantity), 0)
                FROM stock_quant sq
                JOIN stock_location sl ON sq.location_id = sl.id
                WHERE sq.product_id = %s
                AND sl.usage = 'internal'
                AND sl.include_in_stock_qty = true
                AND sq.quantity > 0
            """, (record.product_id.id,))
            
            result = self.env.cr.fetchone()
            total_free_qty = result[0] if result and result[0] else 0.0
            
            record.free_qty = total_free_qty
            _logger.info(f"Final free_qty for {record.product_id.name}: {total_free_qty} (SQL query result)")
        
        _logger.info("=== FREE_QY COMPUTATION COMPLETED ===")

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
                    'imported_qty': 0.0,
                    'open_qty': 0.0,
                }
            product_data[product_id]['ordered_qty'] += shipment.ordered_qty
            product_data[product_id]['imported_qty'] += shipment.imported_qty
            product_data[product_id]['open_qty'] += shipment.open_qty

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
        worksheet.set_column('B:F', 15)  # Stock Qty, Free Qty, Ordered Qty, Imported Qty, Open Qty

        # Write headers
        headers = ['Ürün', 'Stok Miktarı', 'Free Miktar', 'Sipariş Miktarı', 'Imported Miktar', 'Open Miktar']
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
            worksheet.write(row, 4, data['imported_qty'], cell_format)
            worksheet.write(row, 5, data['open_qty'], cell_format)
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
