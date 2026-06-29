# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # ----------------------------------------------------------
    # الحقل الجديد على شاشة الدليفري
    # ----------------------------------------------------------
    x_driver_name = fields.Char(
        string="اسم الطيار",
        help="اسم الطيار المسؤول عن التوصيل. بيتم مزامنته تلقائياً مع أمر البيع المرتبط.",
    )

    # ----------------------------------------------------------
    # Direction 1: Sale Order -> Delivery (عند إنشاء الدليفري)
    # ----------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        pickings = super().create(vals_list)
        for picking in pickings:
            # لو الدليفري اتخلق من أمر بيع وفيه اسم طيار على الأوردر، انسخه
            if not picking.x_driver_name and picking.sale_id and picking.sale_id.x_driver_name:
                picking.with_context(syncing_driver_name=True).sudo().write({
                    'x_driver_name': picking.sale_id.x_driver_name,
                })
        return pickings

    # ----------------------------------------------------------
    # Direction 2: Delivery -> Sale Order (عند التعديل على الدليفري)
    # ----------------------------------------------------------
    def write(self, vals):
        res = super().write(vals)
        # لو المستخدم عدّل اسم الطيار في شاشة الدليفري، حدّث أمر البيع المرتبط
        if 'x_driver_name' in vals and not self.env.context.get('syncing_driver_name'):
            for picking in self:
                if not picking.sale_id:
                    continue
                if picking.sale_id.x_driver_name != picking.x_driver_name:
                    picking.sale_id.with_context(syncing_driver_name=True).sudo().write({
                        'x_driver_name': picking.x_driver_name,
                    })
        return res
