# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ImportShipment(models.Model):
    _inherit = 'import.shipment'

    stock_qty = fields.Float(
        string='Stock Qty',
        compute='_compute_stock_qty',
        store=True,
        help="Current stock quantity from product inventory"
    )

    @api.depends('product_id')
    def _compute_stock_qty(self):
        for record in self:
            if record.product_id:
                # Get the current stock quantity for the product
                quant = self.env['stock.quant']._gather(
                    record.product_id,
                    self.env['stock.location'].search([('usage', '=', 'internal')]),
                    strict=False
                )
                record.stock_qty = sum(quant.mapped('quantity'))
            else:
                record.stock_qty = 0.0
