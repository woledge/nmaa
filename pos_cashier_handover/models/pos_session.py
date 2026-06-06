from odoo import models, fields, api


class PosSession(models.Model):
    _inherit = 'pos.session'

    def action_print_cashier_handover(self):
        """
        طباعة تقرير تسليم الخزينة
        يُستدعى من زر 'طباعة تسليم الخزينة' في واجهة إغلاق الجلسة
        """
        self.ensure_one()
        return self.env.ref(
            'pos_cashier_handover.action_report_cashier_handover'
        ).report_action(self)

    def _get_handover_data(self):
        """
        تجميع كافة البيانات المطلوبة لورقة التسليم
        """
        self.ensure_one()

        # ---- المبيعات حسب طريقة الدفع ----
        cash_total = 0.0
        card_total = 0.0
        transfer_total = 0.0

        payment_method_totals = {}
        for payment in self.payment_method_ids:
            payment_method_totals[payment.name] = 0.0

        for order in self.order_ids.filtered(lambda o: o.state in ('paid', 'done', 'invoiced')):
            for payment in order.payment_ids:
                method_name = payment.payment_method_id.name or ''
                journal = payment.payment_method_id.journal_id
                method_type = payment.payment_method_id.type if hasattr(payment.payment_method_id, 'type') else ''

                amount = payment.amount

                # تصنيف المدفوعات
                name_lower = method_name.lower()
                if 'cash' in name_lower or 'نقد' in name_lower or 'كاش' in name_lower:
                    cash_total += amount
                elif 'visa' in name_lower or 'card' in name_lower or 'فيزا' in name_lower or 'كارد' in name_lower or 'بطاقة' in name_lower:
                    card_total += amount
                elif 'transfer' in name_lower or 'تحويل' in name_lower or 'bank' in name_lower or 'بنك' in name_lower:
                    transfer_total += amount
                else:
                    # دفعات أخرى تُضاف للنقدي بشكل افتراضي
                    cash_total += amount

        # ---- Cash In / Cash Out ----
        cash_in = sum(
            st.amount for st in self.statement_line_ids
            if st.amount > 0
        ) if hasattr(self, 'statement_line_ids') else 0.0

        cash_out = abs(sum(
            st.amount for st in self.statement_line_ids
            if st.amount < 0
        )) if hasattr(self, 'statement_line_ids') else 0.0

        # Cash In/Out من cash_register_balance_end
        pos_cash_in = sum(
            t.amount for t in self.sudo().statement_line_ids
            if t.amount > 0
        ) if hasattr(self, 'statement_line_ids') else 0.0

        pos_cash_out = abs(sum(
            t.amount for t in self.sudo().statement_line_ids
            if t.amount < 0
        )) if hasattr(self, 'statement_line_ids') else 0.0

        # إجمالي المبيعات
        total_sales = cash_total + card_total + transfer_total

        # المبلغ المسلم للحسابات = إجمالي النقدي
        delivered_to_accounts = cash_total

        return {
            'session': self,
            'cashier_name': self.user_id.name,
            'close_date': self.stop_at or fields.Datetime.now(),
            'total_sales': total_sales,
            'cash_total': cash_total,
            'card_total': card_total,
            'transfer_total': transfer_total,
            'cash_in': pos_cash_in,
            'cash_out': pos_cash_out,
            'delivered_to_accounts': delivered_to_accounts,
        }
