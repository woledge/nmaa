from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_building_floor = fields.Char(string="العمارة / الدور")
    x_landmark = fields.Char(string="علامة مميزة")
    x_driver_name = fields.Char(string="اسم الطيار")

    @api.onchange('partner_id')
    def _onchange_partner_id_kitchen_fields(self):
        """Auto-fill delivery info from partner when selecting a customer."""
        if self.partner_id:
            self.x_building_floor = self.partner_id.x_building_floor or False
            self.x_landmark = self.partner_id.x_landmark or False
            self.x_driver_name = self.partner_id.x_driver_name or False
        else:
            self.x_building_floor = False
            self.x_landmark = False
            self.x_driver_name = False

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order in orders:
            order._sync_delivery_fields_to_partner()
        return orders

    def write(self, vals):
        res = super().write(vals)
        tracked_fields = {'x_building_floor', 'x_landmark', 'x_driver_name', 'partner_id'}
        if tracked_fields & set(vals.keys()):
            for order in self:
                order._sync_delivery_fields_to_partner()
                if 'x_driver_name' in vals and not self.env.context.get('syncing_driver_name'):
                    order._sync_driver_name_to_pickings()
        return res

    def _sync_delivery_fields_to_partner(self):
        """Sync delivery info from quotation back to partner + log in chatter."""
        self.ensure_one()
        if not self.partner_id:
            return
        partner = self.partner_id
        changes = []
        field_labels = {
            'x_building_floor': 'العمارة / الدور',
            'x_landmark': 'علامة مميزة',
        }
        partner_vals = {}
        for field, label in field_labels.items():
            new_val = (getattr(self, field) or '').strip()
            old_val = (getattr(partner, field) or '').strip()
            if new_val != old_val:
                partner_vals[field] = new_val
                changes.append((label, old_val, new_val))
        if not partner_vals:
            return
        partner.sudo().write(partner_vals)
        body_lines = [
            "<div style='direction: rtl; font-family: Arial, sans-serif;'>",
            "<b>تحديث بيانات التوصيل من أمر البيع: %s</b><br/>" % (self.name or ''),
            "<ul>",
        ]
        for label, old_val, new_val in changes:
            body_lines.append(
                "<li><b>%s:</b> <span style='color:#999;text-decoration:line-through;'>%s</span> "
                "← <b>%s</b></li>" % (label, old_val or '—', new_val or '—')
            )
        body_lines.append("</ul>")
        body_lines.append("</div>")
        partner.sudo().message_post(
            body=''.join(body_lines),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )

    def _prepare_invoice(self):
        """Pass driver name from sale order to invoice."""
        invoice_vals = super()._prepare_invoice()
        invoice_vals['x_driver_name'] = self.x_driver_name or False
        return invoice_vals

    def _sync_driver_name_to_pickings(self):
        """Sync driver name from sale order to related delivery pickings."""
        self.ensure_one()
        if self.env.context.get('syncing_driver_name'):
            return
        pickings = self.picking_ids.filtered(
            lambda p: p.x_driver_name != self.x_driver_name
        )
        if not pickings:
            return
        pickings.with_context(syncing_driver_name=True).sudo().write({
            'x_driver_name': self.x_driver_name,
        })
