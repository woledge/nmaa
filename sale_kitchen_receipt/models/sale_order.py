# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_building_floor = fields.Char(string="العمارة / الدور")
    x_landmark = fields.Char(string="علامة مميزة")
    x_driver_name = fields.Char(string="اسم الطيار")

    # ----------------------------------------------------------
    # Direction 1: Contact -> Quotation (تملي تلقائي عند الاختيار)
    # ----------------------------------------------------------
    @api.onchange('partner_id')
    def _onchange_partner_id_kitchen_fields(self):
        """
        لما يتم اختيار اسم العميل في الكوتيشن، يتم تملي بيانات التوصيل
        تلقائياً من بيانات العميل المسجلة على الـ Contact.
        المستخدم يقدر يعدلها بعد كده على مستوى الكوتيشن لو محتاج.
        """
        if self.partner_id:
            self.x_building_floor = self.partner_id.x_building_floor or False
            self.x_landmark = self.partner_id.x_landmark or False
            self.x_driver_name = self.partner_id.x_driver_name or False
        else:
            self.x_building_floor = False
            self.x_landmark = False
            self.x_driver_name = False

    # ----------------------------------------------------------
    # Direction 2: Quotation -> Contact (Overwrite + Log in chatter)
    # ----------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order in orders:
            order._sync_delivery_fields_to_partner()
        return orders

    def write(self, vals):
        res = super().write(vals)
        # نشتغل بس لو فيه تعديل في أي حقل من حقول التوصيل أو تغيير العميل
        tracked_fields = {'x_building_floor', 'x_landmark', 'x_driver_name', 'partner_id'}
        if tracked_fields & set(vals.keys()):
            for order in self:
                order._sync_delivery_fields_to_partner()
        return res

    def _sync_delivery_fields_to_partner(self):
        """
        حدّث بيانات التوصيل على الـ Contact بالكامل من بيانات الكوتيشن
        (حتى لو الكونتكت فيه بيانات قديمة - بيحصل overwrite).
        وكمان سجّل التغيير في الـ chatter (log notes) بتاع الكونتكت.
        """
        self.ensure_one()
        if not self.partner_id:
            return
        partner = self.partner_id

        # نجمع الفروقات الفعلية علشان نسجلها في اللوج
        changes = []
        field_labels = {
            'x_building_floor': 'العمارة / الدور',
            'x_landmark': 'علامة مميزة',
            # 'x_driver_name': 'اسم الطيار',
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

        # تحديث بيانات الكونتكت
        partner.sudo().write(partner_vals)

        # تسجيل التغيير في الـ chatter بتاع الكونتكت
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