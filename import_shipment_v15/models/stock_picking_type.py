from odoo import models, fields

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    use_import_shipment = fields.Boolean(
        string='Use Import Shipment', 
        default=False,
        help="If checked, Purchase Orders using this operation type will not create pickings automatically. "
             "Instead, lines will be collected into the Import Shipment list."
    )
