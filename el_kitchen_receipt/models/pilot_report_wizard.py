# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError


class PilotReportWizard(models.TransientModel):
    _name = 'pilot.report.wizard'
    _description = 'تقرير أوامر البيع حسب الطيار'

    x_driver_name = fields.Many2one(
        'x.pilot',
        string='اسم الطيار',
        required=True,
    )

    date_from = fields.Date(
        string='من تاريخ',
    )

    date_to = fields.Date(
        string='إلى تاريخ',
    )

    sale_order_id = fields.Many2one(
        'sale.order',
        string='أمر بيع ',
        domain=[('x_driver_name', '!=', False)],
        help='اتركه فارغاً إذا كنت تريد جميع أوامر البيع للطيار',
    )

    def action_print_report(self):
        self.ensure_one()

        domain = [
            ('x_driver_name', '=', self.x_driver_name.id),
        ]

        if self.date_from:
            domain.append(('date_order', '>=', self.date_from))

        if self.date_to:
            domain.append(('date_order', '<=', self.date_to))

        if self.sale_order_id:
            domain.append(('id', '=', self.sale_order_id.id))

        orders = self.env['sale.order'].search(domain, order='date_order desc')

        if not orders:
            raise UserError(
                _('لا توجد أوامر بيع تطابق معايير البحث المحددة.')
            )

        return self.env.ref(
            'el_kitchen_receipt.action_pilot_report'
        ).with_context(
            from_wizard=True,
            wizard_driver_name=self.x_driver_name.name,
            wizard_date_from=self.date_from,
            wizard_date_to=self.date_to,
            wizard_sale_order=self.sale_order_id.name if self.sale_order_id else False,
        ).report_action(orders)