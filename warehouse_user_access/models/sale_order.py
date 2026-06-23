from odoo import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _default_warehouse_id(self):
        user = self.env.user
        if user.warehouse_ids:
            return user.warehouse_ids[0]
        return super(SaleOrder, self)._default_warehouse_id()

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        user = self.env.user
        if not user.has_group('base.group_system') and user.warehouse_ids:
            domain.append(('warehouse_id', 'in', user.warehouse_ids.ids))
        return super(SaleOrder, self)._search(
            domain, offset=offset, limit=limit, order=order
        )


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        user = self.env.user
        if not user.has_group('base.group_system') and user.warehouse_ids:
            domain.append(('order_id.warehouse_id', 'in', user.warehouse_ids.ids))
        return super(SaleOrderLine, self)._search(
            domain, offset=offset, limit=limit, order=order
        )