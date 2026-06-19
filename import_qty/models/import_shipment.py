# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ImportShipment(models.Model):
    _inherit = 'import.shipment'

    stock_qty = fields.Float(
        string='Stock Qty',
        related='product_id.qty_available',
        store=True,
        readonly=True,
        help="Current stock quantity from product inventory"
    )
