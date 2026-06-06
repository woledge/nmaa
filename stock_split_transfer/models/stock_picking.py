from odoo import models, fields, api
from odoo.osv import expression
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # ── Split Transfer Link Fields ──

    split_parent_id = fields.Many2one(
        'stock.picking',
        string='Previous Transfer',
        help='For Leg 2 (transit → dest): points to Leg 1 (source → transit).',
        ondelete='cascade',
    )
    split_child_id = fields.Many2one(
        'stock.picking',
        string='Next Transfer',
        help='For Leg 1 (source → transit): points to Leg 2 (transit → dest).',
        ondelete='cascade',
    )
    split_visible = fields.Boolean(
        default=True,
        string='Visible',
        help='Whether this picking appears in the operations list. '
             'Leg 2 starts invisible until Leg 1 is validated.',
    )
    is_split_transfer = fields.Boolean(
        compute='_compute_is_split_transfer',
        store=True,
        string='Split Transfer',
    )

    @api.depends('split_parent_id', 'split_child_id')
    def _compute_is_split_transfer(self):
        for picking in self:
            picking.is_split_transfer = bool(picking.split_parent_id) or bool(picking.split_child_id)

    # ── Transit Location Helper ──

    def _get_transit_location(self):
        """Find or create the transit location used for split transfers."""
        self.ensure_one()
        transit = self.env['stock.location'].search([
            ('usage', '=', 'transit'),
            ('company_id', 'in', [self.env.company.id, False]),
        ], limit=1)
        if not transit:
            transit = self.env['stock.location'].sudo().create({
                'name': 'Split Transfer Transit',
                'usage': 'transit',
                'company_id': self.env.company.id,
                'location_id': self.env.ref('stock.stock_location_locations_virtual').id,
            })
            _logger.info('Created transit location (id=%d) for split transfers.', transit.id)
        return transit

    # ── Split Detection ──

    def _needs_split(self):
        """Check if this internal transfer should be split into two legs."""
        self.ensure_one()
        if self.picking_type_code != 'internal':
            return False
        if self.split_parent_id:
            return False  # Already a child — do not re-split
        if not self.location_id or not self.location_dest_id:
            return False
        return self.location_id.id != self.location_dest_id.id

    # ── Override: action_confirm (Split Before Confirm) ──

    def action_confirm(self):
        """Split qualifying internal transfers before standard confirmation."""
        pickings_to_confirm = self.env['stock.picking']

        for picking in self:
            if picking._needs_split():
                picking._create_split_transfer()
                pickings_to_confirm |= picking
            else:
                pickings_to_confirm |= picking

        return super(StockPicking, pickings_to_confirm).action_confirm()

    # ── Split Creation ──

    def _create_split_transfer(self):
        """
        Split this picking into two legs:
          Leg 1 (self):  Source Location → Transit Location
          Leg 2 (new):   Transit Location → Original Destination
        """
        self.ensure_one()

        transit = self._get_transit_location()
        original_dest = self.location_dest_id

        # Create Leg 2 picking (transit → original dest)
        child_picking = self.copy(default={
            'location_id': transit.id,
            'location_dest_id': original_dest.id,
            'state': 'draft',
            'split_parent_id': self.id,
            'split_visible': False,
            'move_ids': False,
            'move_line_ids': False,
        })

        # Create moves for Leg 2 (mirror Leg 1 moves)
        for move in self.move_ids:
            move.copy(default={
                'picking_id': child_picking.id,
                'location_id': transit.id,
                'location_dest_id': original_dest.id,
                'state': 'draft',
                'move_line_ids': False,
            })

        # Update Leg 1: redirect destination to transit
        self.write({
            'location_dest_id': transit.id,
            'split_child_id': child_picking.id,
        })

        # Update Leg 1 moves: redirect destination to transit
        self.move_ids.write({
            'location_dest_id': transit.id,
        })

        # Update Leg 1 move lines (if any exist)
        if self.move_line_ids:
            self.move_line_ids.write({
                'location_dest_id': transit.id,
            })

        _logger.info(
            'Split transfer created: Leg 1 (id=%d) %s → Transit, '
            'Leg 2 (id=%d) Transit → %s',
            self.id, self.location_id.display_name,
            child_picking.id, original_dest.display_name,
        )

        return child_picking

    # ── Override: button_validate (Activate Leg 2 After Leg 1) ──

    def button_validate(self):
        """After validating Leg 1, reveal and confirm Leg 2."""
        result = super().button_validate()

        children_to_activate = self.env['stock.picking'].sudo()
        for picking in self:
            child = picking.split_child_id.sudo()
            if child and child.state == 'draft' and not child.split_visible:
                children_to_activate |= child

        for child in children_to_activate:
            child.split_visible = True
            if child.state == 'draft':
                try:
                    child.with_context(_split_transfer_auto_confirm=True).action_confirm()
                    _logger.info('Activated Leg 2 (id=%d) after Leg 1 validation.', child.id)
                except Exception as e:
                    _logger.error(
                        'Failed to activate Leg 2 (id=%d): %s', child.id, str(e), exc_info=True,
                    )

        return result

    # ── Override: _search (Location-Based Visibility Filter) ──

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        user = self.env.user
        if (not self.env.su
                and user.allowed_location_ids
                and not user.has_group('stock.group_stock_manager')):
            location_ids = user.allowed_location_ids.ids
            custom_domain = [
                '&',
                '|',
                ('location_id', 'in', location_ids),
                ('location_dest_id', 'in', location_ids),
                ('split_visible', '=', True),
            ]
            domain = expression.AND([custom_domain, domain])

        return super()._search(domain, offset=offset, limit=limit, order=order)
