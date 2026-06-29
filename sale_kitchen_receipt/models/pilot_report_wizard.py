# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PilotReportWizard(models.TransientModel):
    _name = 'pilot.report.wizard'
    _description = 'تقرير أوامر البيع حسب الطيار'

    x_driver_name = fields.Char(
        string="اسم الطيار",
        required=True,
    )

    @api.autovacuum
    def _gc_pilot_report_wizard(self):
        pass

    def action_print_report(self):
        self.ensure_one()
        orders = self.env['sale.order'].search([
            ('x_driver_name', 'ilike', self.x_driver_name),
        ], order='date_order desc')

        if not orders:
            raise UserError(
                _('لا توجد أوامر بيع لهذا الطيار: %s') % self.x_driver_name
            )

        return self.env.ref(
            'sale_kitchen_receipt.action_pilot_report'
        ).with_context(
            from_wizard=True,
            wizard_driver_name=self.x_driver_name,
        ).report_action(orders)