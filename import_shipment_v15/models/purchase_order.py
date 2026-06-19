from odoo import models, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _create_picking(self):
        # Filter orders: Skip picking creation if picking type has x_is_import_type
        # In v15, picking_type_id is on purchase.order
        normal_orders = self.filtered(lambda o: not o.picking_type_id.use_import_shipment)
        
        # Call super only for normal orders
        if normal_orders:
            return super(PurchaseOrder, normal_orders)._create_picking()
        return True

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        # Create import shipment records if picking type has x_is_import_type
        for order in self:
            if order.picking_type_id.x_is_import_type:
                for line in order.order_line:
                    if line.product_id.type == 'service':
                        continue
                    self.env['import.shipment'].create({
                        'partner_id': order.partner_id.id,
                        'purchase_line_id': line.id,
                        'ordered_qty': line.product_qty,
                        'expected_date': line.date_planned.date() if line.date_planned else False,
                    })
        return res

    def button_cancel(self):
        res = super(PurchaseOrder, self).button_cancel()
        for order in self:
            shipments = self.env['import.shipment'].search([
                ('purchase_line_id', 'in', order.order_line.ids)
            ])
            if shipments:
                shipments.write({'state': 'cancel'})
        return res
