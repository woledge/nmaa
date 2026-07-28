# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_driver_name = fields.Char(string="اسم الطيار")
    x_returned = fields.Boolean(string="مرتجع", copy=False, tracking=True)
    x_return_reason_id = fields.Many2one(
        'delivery.return.reason',
        string="سبب الرجوع",
        copy=False,
        tracking=True,
    )
    x_return_note = fields.Text(string="ملاحظات الرجوع", copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        pickings = super().create(vals_list)
        for picking in pickings:
            if not picking.x_driver_name and picking.origin:
                sale = self.env['sale.order'].search([
                    ('name', '=', picking.origin),
                ], limit=1)
                if sale and sale.x_driver_name:
                    picking.sudo().write({
                        'x_driver_name': sale.x_driver_name,
                    })
        return pickings