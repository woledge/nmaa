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


# ملاحظة: تم حذف override الخاص بـ stock.quant لأنه كان يستخدم الحقل
# 'warehouse_id' الذي غير موجود على stock.quant (يستخدم stock.quant الحقل
# location_id للربط بالمستودع بشكل غير مباشر). تم استبداله بـ record rule
# في ملف security/warehouse_user_access_security.xml يستخدم
# location_id مع child_of view_location_id.
