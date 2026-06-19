# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

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
