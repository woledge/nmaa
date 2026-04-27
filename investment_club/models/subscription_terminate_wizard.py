from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class SubscriptionTerminateWizard(models.TransientModel):
    _name = 'subscription.terminate.wizard'
    _description = 'Investment Subscription Termination Wizard'

    # ===== Subscription Reference =====
    subscription_id = fields.Many2one(
        'investment.subscription',
        string='Investment Subscription',
        required=True
    )

    membership_id = fields.Many2one(
        'investment.membership',
        related='subscription_id.membership_id',
        string='Membership',
        readonly=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        related='subscription_id.partner_id',
        string='Investor',
        readonly=True
    )

    project_id = fields.Many2one(
        'investment.project',
        related='subscription_id.project_id',
        string='Project',
        readonly=True
    )

    investor_code = fields.Char(
        related='subscription_id.membership_id.investor_code',
        string='Investor Code',
        readonly=True
    )

    # ===== Date Info =====
    membership_date = fields.Date(
        related='subscription_id.membership_id.membership_date',
        string='Membership Start Date',
        readonly=True
    )

    investment_date = fields.Date(
        related='subscription_id.investment_date',
        string='Investment Date',
        readonly=True
    )

    # ===== Financial =====
    share_count = fields.Integer(
        related='subscription_id.share_count',
        string='Number of Shares',
        readonly=True
    )

    share_value = fields.Float(
        related='subscription_id.share_value',
        string='Share Value',
        readonly=True
    )

    total_amount = fields.Float(
        related='subscription_id.amount',
        string='Total Investment Amount',
        readonly=True
    )

    total_returns_paid = fields.Float(
        related='subscription_id.total_actual_returns',
        string='Total Returns Already Paid',
        readonly=True
    )

    # ===== Termination Calculation =====
    membership_months_elapsed = fields.Integer(
        string='Membership Months Elapsed',
        compute='_compute_period',
        store=True
    )

    is_first_3_months = fields.Boolean(
        string='Within First 3 Months of Membership',
        compute='_compute_period',
        store=True
    )

    refund_amount = fields.Float(
        string='Refund Amount',
        compute='_compute_refund',
        store=True
    )

    # ===== Payment =====
    refund_journal_id = fields.Many2one(
        'account.journal',
        string='Refund Journal',
        domain="[('type', 'in', ('bank', 'cash'))]",
        required=True
    )

    # ===== Notes =====
    reason = fields.Text(
        string='Termination Reason',
        required=True
    )

    notes = fields.Text(string='Additional Notes')

    # ===== Compute Methods =====

    @api.depends('subscription_id')
    def _compute_period(self):
        today = fields.Date.today()
        for wizard in self:
            if not wizard.membership_date:
                wizard.membership_months_elapsed = 0
                wizard.is_first_3_months = False
                continue

            diff = relativedelta(today, wizard.membership_date)
            wizard.membership_months_elapsed = diff.months + (diff.years * 12)
            wizard.is_first_3_months = wizard.membership_months_elapsed < 3

    @api.depends('subscription_id', 'is_first_3_months', 'total_amount')
    def _compute_refund(self):
        for wizard in self:
            if not wizard.subscription_id:
                wizard.refund_amount = 0.0
                continue

            if wizard.is_first_3_months:
                # خلال أول 3 شهور من العضوية: يسترد أصل قيمة الحصة المسددة
                wizard.refund_amount = wizard.total_amount
            else:
                wizard.refund_amount = 0.0

    # ===== Actions =====

    def action_confirm_termination(self):
        self.ensure_one()
        if not self.reason:
            raise UserError(_('Please provide a termination reason!'))

        if not self.is_first_3_months:
            raise UserError(_(
                'Cannot terminate this investment!\n'
                'Investment shares can only be terminated during the first 3 months of membership.'
            ))

        if self.refund_amount <= 0:
            raise UserError(_('Refund amount is zero! Cannot proceed.'))

        subscription = self.subscription_id

        if subscription.state not in ('paid', 'active'):
            raise UserError(_('Investment must be paid or active to terminate!'))

        # Create refund payment
        payment_vals = {
            'payment_type': 'outbound',
            'partner_type': 'customer',
            'partner_id': subscription.partner_id.id,
            'journal_id': self.refund_journal_id.id,
            'amount': self.refund_amount,
            'currency_id': subscription.currency_id.id,
            'date': fields.Date.today(),
            'memo': _('Investment Share Termination Refund - %s') % subscription.name,
        }

        payment = self.env['account.payment'].create(payment_vals)
        payment.action_post()

        # Update subscription state
        subscription.write({
            'state': 'terminated',
        })

        # Post chatter message
        subscription.message_post(
            body=_(
                '<p><b>تم فسخ عقد الحصة الاستثمارية</b></p>'
                '<ul>'
                '<li>المستثمر: <b>%s</b></li>'
                '<li>المشروع: <b>%s</b></li>'
                '<li>عدد الحصص: <b>%s</b></li>'
                '<li>قيمة الحصة: <b>%s</b></li>'
                '<li>إجمالي المبلغ: <b>%s</b></li>'
                '<li>مبلغ الاسترداد: <b>%s</b></li>'
                '<li>السبب: <b>%s</b></li>'
                '</ul>'
            ) % (
                subscription.partner_id.name or '',
                subscription.project_id.name or '',
                subscription.share_count,
                subscription.share_value,
                subscription.amount,
                self.refund_amount,
                self.reason,
            ),
            partner_ids=[subscription.partner_id.id],
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )

        return {'type': 'ir.actions.act_window_close'}