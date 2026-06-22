# -*- coding: utf-8 -*-
from odoo import models, fields

class StockLocation(models.Model):
    _inherit = 'stock.location'

    include_in_stock_qty = fields.Boolean(
        string='Include in Stock Qty',
        default=False,
        help="If checked, this location will be included in stock quantity calculations. "
             "Only applies to internal locations."
    )
