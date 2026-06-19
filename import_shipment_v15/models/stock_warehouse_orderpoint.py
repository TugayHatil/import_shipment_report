from odoo import models, fields, api

class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    def _compute_qty_to_order(self):
        # In v15, _compute_qty_to_order handles the calculation of qty_to_order
        super(StockWarehouseOrderpoint, self)._compute_qty_to_order()
        for orderpoint in self:
            # Domain to find open import shipments for this product and destination location
            domain = [
                ('product_id', '=', orderpoint.product_id.id),
                ('state', 'in', ['waiting', 'partially_imported', 'imported']),
                ('purchase_line_id.order_id.picking_type_id.default_location_dest_id', '=', orderpoint.location_id.id)
            ]
            
            shipments = self.env['import.shipment'].search(domain)
            incoming_shipment_qty = sum(shipments.mapped('open_qty'))
            
            if incoming_shipment_qty > 0:
                # Reduce the suggested order quantity by what is already in "Import Shipment" transit
                orderpoint.qty_to_order = max(0.0, orderpoint.qty_to_order - incoming_shipment_qty)
