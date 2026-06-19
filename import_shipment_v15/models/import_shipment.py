from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class ImportShipment(models.Model):
    _name = 'import.shipment'
    _description = 'Import Shipment Line'
    _order = 'id desc'

    name = fields.Char(string='Name', compute='_compute_name', store=True, readonly=True)
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('partially_imported', 'Partially Imported'),
        ('imported', 'Imported'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='waiting', compute='_compute_state', store=True, tracking=True)

    partner_id = fields.Many2one('res.partner', string='Vendor', required=True)
    purchase_line_id = fields.Many2one('purchase.order.line', string='Purchase Order Line', required=True, ondelete='cascade')
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', related='purchase_line_id.order_id', store=True)
    product_id = fields.Many2one('product.product', string='Product', related='purchase_line_id.product_id', store=True)
    
    # Custom fields
    x_manufacturer_code = fields.Char(string='Manufacturer Pref', related='product_id.x_manufacturer_code', store=True, readonly=True)

    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', related='purchase_line_id.product_uom', store=True, readonly=True)
    price_unit = fields.Float(related='purchase_line_id.price_unit', string='Unit Price', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', related='purchase_order_id.currency_id', string='Currency', store=True, readonly=True)

    ordered_qty = fields.Float(string='Ordered Qty', related='purchase_line_id.product_qty', store=True)
    imported_qty = fields.Float(string='Imported Qty', help="Cumulative quantity imported via Excel", copy=False, default=0.0)
    incoming_qty = fields.Float(string='Incoming Qty', help="Quantity being imported in current session", copy=False, default=0.0)
    received_qty = fields.Float(string='Received Qty', compute='_compute_received_qty', store=True)
    open_qty = fields.Float(string='Open Qty', compute='_compute_open_qty', store=True)
    
    expected_date = fields.Date(string='Expected Date')
    
    picking_id = fields.Many2one('stock.picking', string='Latest Picking', copy=False)
    picking_count = fields.Integer(compute='_compute_picking_count', string='Picking Count')

    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = self.env['stock.picking'].search_count([
                ('move_ids.import_shipment_id', '=', rec.id)
            ])

    def action_open_related_pickings(self):
        self.ensure_one()
        pickings = self.env['stock.picking'].search([
            ('move_ids.import_shipment_id', '=', self.id)
        ])
        return {
            'name': _('Related Pickings'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', pickings.ids)],
            'target': 'current',
        }

    def create_incoming_picking(self, batch_qty=None, excel_date=None):
        lines_to_process = self
        items_qty_map = self.env.context.get('items_qty_map')
        move_dates_map = self.env.context.get('move_dates_map') or {}

        if not items_qty_map:
            # Manual trigger or simplified call
            # Use batch_qty if provided, else use current session's incoming_qty, else difference
            items_qty_map = {l.id: (batch_qty or l.incoming_qty or (l.imported_qty - l.received_qty)) for l in lines_to_process}

        # Filter lines where qty > 0
        valid_line_ids = [l_id for l_id, qty in items_qty_map.items() if qty > 0]
        lines_to_process = self.filtered(lambda l: l.id in valid_line_ids)

        if not lines_to_process:
            return False

        # Group by partner
        partners = lines_to_process.mapped('partner_id')
        pickings = self.env['stock.picking']
        
        for partner in partners:
            partner_lines = lines_to_process.filtered(lambda l: l.partner_id == partner)
            first_po = partner_lines[0].purchase_order_id
            picking_type = first_po.picking_type_id
            
            if not picking_type:
                # Default to an incoming type if not set on PO
                picking_type = self.env['stock.picking.type'].search([
                    ('code', '=', 'incoming'),
                    ('warehouse_id.company_id', '=', self.env.company.id)
                ], limit=1)

            final_date = excel_date
            if not final_date and move_dates_map:
                dates = [d for l_id, d in move_dates_map.items() if l_id in partner_lines.ids and d]
                if dates:
                    final_date = min(dates)

            picking_vals = {
                'partner_id': partner.id,
                'picking_type_id': picking_type.id,
                'location_id': partner.property_stock_supplier.id or self.env.ref('stock.stock_location_suppliers').id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'origin': ', '.join(set(partner_lines.mapped('purchase_order_id.name'))),
                'move_type': 'direct',
            }
            if final_date:
                picking_vals['scheduled_date'] = final_date
            
            picking = self.env['stock.picking'].create(picking_vals)
            
            moves_to_create = []
            for line in partner_lines:
                qty_to_process = items_qty_map.get(line.id, 0.0)
                if qty_to_process <= 0:
                    continue
                
                move_date = move_dates_map.get(line.id) or final_date or fields.Datetime.now()

                move_vals = {
                    'name': line.product_id.display_name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': qty_to_process,
                    'product_uom': line.product_uom.id or line.product_id.uom_id.id,
                    'picking_id': picking.id,
                    'location_id': picking.location_id.id,
                    'location_dest_id': picking.location_dest_id.id,
                    'purchase_line_id': line.purchase_line_id.id,
                    'import_shipment_id': line.id,
                    'origin': line.purchase_order_id.name,
                    'date': move_date,
                }
                moves_to_create.append(move_vals)
            
            if moves_to_create:
                self.env['stock.move'].create(moves_to_create)
                picking.action_confirm()
                partner_lines.write({
                    'picking_id': picking.id,
                    'incoming_qty': 0.0 # reset after processing
                })
                pickings |= picking

        return pickings

    @api.depends('purchase_order_id.name', 'product_id.x_manufacturer_code')
    def _compute_name(self):
        for record in self:
            prefix = record.purchase_order_id.name or ''
            suffix = record.product_id.x_manufacturer_code or ''
            record.name = f"{prefix} - {suffix}" if suffix else prefix

    @api.depends('ordered_qty', 'imported_qty')
    def _compute_open_qty(self):
        for rec in self:
            rec.open_qty = max(0.0, rec.ordered_qty - rec.imported_qty)

    @api.depends('purchase_line_id.move_ids.state', 'purchase_line_id.move_ids.quantity_done')
    def _compute_received_qty(self):
        for rec in self:
            # received_qty is the sum of done quantities in moves linked to this shipment line
            moves = self.env['stock.move'].search([
                ('import_shipment_id', '=', rec.id),
                ('state', '=', 'done')
            ])
            rec.received_qty = sum(moves.mapped('quantity_done'))

    @api.depends('received_qty', 'ordered_qty', 'imported_qty')
    def _compute_state(self):
        for rec in self:
            if rec.state == 'cancel':
                continue
            if rec.received_qty >= rec.ordered_qty and rec.ordered_qty > 0:
                rec.state = 'done'
            elif rec.imported_qty >= rec.ordered_qty and rec.ordered_qty > 0:
                rec.state = 'imported'
            elif rec.imported_qty > 0:
                rec.state = 'partially_imported'
            else:
                rec.state = 'waiting'
