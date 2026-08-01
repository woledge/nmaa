from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_driver_name = fields.Char(
        string="اسم الطيار",
        help="اسم الطيار المسؤول عن التوصيل. بيتم مزامنته تلقائياً مع أمر البيع المرتبط.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        pickings = super().create(vals_list)
        for picking in pickings:
            if not picking.x_driver_name and picking.origin:
                sale = self.env['sale.order'].search([
                    ('name', '=', picking.origin),
                ], limit=1)
                if sale and sale.x_driver_name:
                    picking.with_context(syncing_driver_name=True).sudo().write({
                        'x_driver_name': sale.x_driver_name,
                    })
        return pickings

    def write(self, vals):
        res = super().write(vals)
        if 'x_driver_name' in vals and not self.env.context.get('syncing_driver_name'):
            for picking in self:
                if picking.origin:
                    sale = self.env['sale.order'].search([
                        ('name', '=', picking.origin),
                    ], limit=1)
                    if sale and sale.x_driver_name != picking.x_driver_name:
                        sale.with_context(syncing_driver_name=True).sudo().write({
                            'x_driver_name': picking.x_driver_name,
                        })
        return res
