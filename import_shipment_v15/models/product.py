from odoo import models, fields

class ProductProduct(models.Model):
    _inherit = 'product.product'

    x_manufacturer_code = fields.Char(string='Manufacturer Pref', help='Manufacturer part number or code for the product.')
