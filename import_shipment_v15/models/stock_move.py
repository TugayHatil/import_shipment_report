from odoo import models, fields

class StockMove(models.Model):
    _inherit = 'stock.move'

    import_shipment_id = fields.Many2one('import.shipment', string='Import Shipment', index=True)
