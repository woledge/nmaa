from odoo import models, api


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        user = self.env.user
        if not user.has_group('base.group_system') and user.warehouse_ids:
            domain.append(('id', 'in', user.warehouse_ids.ids))
        return super(StockWarehouse, self)._search(
            domain, offset=offset, limit=limit, order=order
        )


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        user = self.env.user
        if not user.has_group('base.group_system') and user.warehouse_ids:
            domain.append(('picking_type_id.warehouse_id', 'in', user.warehouse_ids.ids))
        return super(StockPicking, self)._search(
            domain, offset=offset, limit=limit, order=order
        )


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        user = self.env.user
        if not user.has_group('base.group_system') and user.warehouse_ids:
            domain.append(('warehouse_id', 'in', user.warehouse_ids.ids))
        return super(StockQuant, self)._search(
            domain, offset=offset, limit=limit, order=order
        )


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        user = self.env.user
        if not user.has_group('base.group_system') and user.warehouse_ids:
            domain.append(('warehouse_id', 'in', user.warehouse_ids.ids))
        return super(StockPickingType, self)._search(
            domain, offset=offset, limit=limit, order=order
        )