from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class InvestmentSubscription(models.Model):
    _name = 'investment.subscription'
    _description = 'Investment Subscription'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    # ===== Basic Fields =====

    name = fields.Char(
        string='Reference',
        readonly=True,
        copy=False,
        default='New'
    )

    membership_id = fields.Many2one(
        'investment.membership',
        string='Membership',
        required=True,
        ondelete='cascade'
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Investor',
        related='membership_id.partner_id',
        store=True,
        readonly=True
    )

    club_id = fields.Many2one(
        'investment.club',
        string='Club',
        related='membership_id.club_id',
        store=True,
        readonly=True
    )

    project_id = fields.Many2one(
        'investment.project',
        string='Investment Project',
        required=True,
        domain="[('club_id', '=', club_id), ('state', '=', 'active')]"
    )

    # ===== Project Return Settings (from project) =====

    return_calculation_type = fields.Selection(
        related='project_id.return_calculation_type',
        string='Return Type',
        readonly=True,
        store=True
    )

    grace_period_months = fields.Integer(
        related='project_id.grace_period_months',
        string='Grace Period (Months)',
        readonly=True,
        store=True
    )

    grace_period_days = fields.Integer(
        related='project_id.grace_period_days',
        string='Grace Period (Days)',
        readonly=True,
        store=True
    )

    return_period_days = fields.Integer(
        related='project_id.return_period_days',
        string='Return Period (Days)',
        readonly=True,
        store=True
    )

    return_percentage = fields.Float(
        related='project_id.return_percentage',
        string='Return Percentage (%)',
        readonly=True,
        store=True
    )

    capital_return_period = fields.Integer(
        related='project_id.capital_return_period',
        string='Capital Return Period (Months)',
        readonly=True,
        store=True
    )

    fixed_return_amount = fields.Float(
        related='project_id.fixed_return_amount',
        string='Fixed Return Amount',
        readonly=True,
        store=True
    )

    # ===== Investment Details =====

    investment_date = fields.Date(
        string='Investment Date',
        default=fields.Date.today,
        required=True
    )

    share_count = fields.Integer(string='Number of Shares', default=1, required=True)

    share_value = fields.Float(
        string='Share Value',
        related='project_id.share_value',
        readonly=True,
        store=True
    )

    amount = fields.Float(
        string='Investment Amount',
        compute='_compute_amount',
        store=True
    )

    # ===== Computed Dates =====

    returns_start_date = fields.Date(
        string='Returns Start Date',
        compute='_compute_return_dates',
        store=True
    )

    capital_return_date = fields.Date(
        string='Capital Return Date',
        compute='_compute_return_dates',
        store=True
    )

    expected_period_return = fields.Float(
        string='Expected Period Return',
        compute='_compute_return_dates',
        store=True
    )

    # ===== Return Tracking =====

    actual_return_ids = fields.One2many(
        'investment.actual.return',
        'subscription_id',
        string='Actual Returns History'
    )

    total_actual_returns = fields.Float(
        string='Total Actual Returns Paid',
        compute='_compute_total_returns',
        store=True
    )

    last_return_date = fields.Date(
        string='Last Return Date',
        compute='_compute_last_return',
        store=True
    )

    grace_period_passed = fields.Boolean(
        string='Grace Period Passed',
        compute='_compute_grace_period_status',
        store=True
    )

    months_until_returns_start = fields.Integer(
        string='Months Until Returns Start',
        compute='_compute_grace_period_status',
        store=True
    )

    days_until_returns_start = fields.Integer(
        string='Days Until Returns Start',
        compute='_compute_grace_period_status',
        store=True
    )

    # ===== Payment =====

    payment_journal_id = fields.Many2one(
        'account.journal',
        string='Payment Journal',
        domain="[('type', 'in', ('bank', 'cash'))]"
    )

    payment_id = fields.Many2one(
        'account.payment',
        string='Payment',
        readonly=True,
        copy=False
    )

    payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('paid', 'Paid')
    ], string='Payment Status', default='not_paid', readonly=True)

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        related='project_id.analytic_account_id',
        string='Analytic Account',
        readonly=True,
        store=True
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    approval_user_id = fields.Many2one(
        'res.users',
        string='Approved By',
        readonly=True,
        copy=False
    )

    approval_date = fields.Date(
        string='Approval Date',
        readonly=True,
        copy=False
    )

    rejection_reason = fields.Text(
        string='Rejection Reason',
        readonly=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='membership_id.company_id',
        store=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        store=True
    )

    notes = fields.Text(string='Notes')

    # ===== Compute Methods =====

    @api.depends('share_count', 'share_value')
    def _compute_amount(self):
        for sub in self:
            sub.amount = sub.share_count * sub.share_value

    @api.depends('investment_date', 'grace_period_months', 'grace_period_days',
                 'return_period_days', 'return_percentage', 'return_calculation_type',
                 'amount', 'capital_return_period', 'fixed_return_amount')
    def _compute_return_dates(self):
        for sub in self:
            if not sub.investment_date:
                sub.returns_start_date = False
                sub.capital_return_date = False
                sub.expected_period_return = 0.0
                continue

            # Returns start: investment date + grace months + grace days
            grace_months = sub.grace_period_months or 0
            grace_days = sub.grace_period_days or 0
            sub.returns_start_date = (
                sub.investment_date
                + relativedelta(months=grace_months)
                + timedelta(days=grace_days)
            )

            # Capital return date
            capital_months = sub.capital_return_period or 0
            if capital_months > 0:
                sub.capital_return_date = sub.investment_date + relativedelta(months=capital_months)
            else:
                sub.capital_return_date = False

            # Expected return per period based on calculation type
            if sub.return_calculation_type == 'grace_period':
                if sub.fixed_return_amount > 0:
                    sub.expected_period_return = sub.fixed_return_amount
                elif sub.return_percentage > 0:
                    sub.expected_period_return = (sub.return_percentage / 100) * sub.amount / 12
                else:
                    sub.expected_period_return = 0

            elif sub.return_calculation_type == 'fixed_monthly':
                sub.expected_period_return = (sub.return_percentage / 100) * sub.amount / 12

            elif sub.return_calculation_type == 'fixed_quarterly':
                sub.expected_period_return = (sub.return_percentage / 100) * sub.amount / 4

            elif sub.return_calculation_type == 'fixed_yearly':
                sub.expected_period_return = (sub.return_percentage / 100) * sub.amount

            elif sub.return_calculation_type == 'custom':
                days = sub.return_period_days or 30
                sub.expected_period_return = (sub.return_percentage / 100) * sub.amount * (days / 365)

            elif sub.return_calculation_type == 'capital_plus_return':
                sub.expected_period_return = sub.fixed_return_amount if sub.fixed_return_amount > 0 else 0

            else:
                sub.expected_period_return = 0

    @api.depends('returns_start_date', 'investment_date')
    def _compute_grace_period_status(self):
        today = fields.Date.today()
        for sub in self:
            if not sub.returns_start_date or not sub.investment_date:
                sub.grace_period_passed = False
                sub.months_until_returns_start = 0
                sub.days_until_returns_start = 0
                continue

            sub.grace_period_passed = today >= sub.returns_start_date

            if sub.grace_period_passed:
                sub.months_until_returns_start = 0
                sub.days_until_returns_start = 0
            else:
                diff = relativedelta(sub.returns_start_date, today)
                sub.months_until_returns_start = diff.months + (diff.years * 12)
                sub.days_until_returns_start = (sub.returns_start_date - today).days

    @api.depends('actual_return_ids.actual_amount', 'actual_return_ids.state')
    def _compute_total_returns(self):
        for sub in self:
            sub.total_actual_returns = sum(
                sub.actual_return_ids.filtered(lambda r: r.state == 'paid').mapped('actual_amount')
            )

    @api.depends('actual_return_ids')
    def _compute_last_return(self):
        for sub in self:
            paid_returns = sub.actual_return_ids.filtered(lambda r: r.state == 'paid')
            sub.last_return_date = max(paid_returns.mapped('date_to')) if paid_returns else False

    # ===== CRUD Overrides =====

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('investment.subscription') or 'New'
        return super(InvestmentSubscription, self).create(vals_list)

    def copy(self, default=None):
        """Reset payment and status fields on duplicate."""
        default = dict(default or {})
        default['name'] = 'New'
        default['payment_id'] = False
        default['payment_state'] = 'not_paid'
        default['state'] = 'draft'
        return super().copy(default)

    # ===== Actions =====

    def _get_config(self, key, default=False):
        """Read a config parameter value."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'investment_club.%s' % key, default
        )

    def action_submit_approval(self):
        """Submit investment for manager approval."""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Only draft investments can be submitted for approval!'))
        self.write({'state': 'pending_approval'})
        self.message_post(
            body=_('Investment submitted for approval.'),
            partner_ids=[],
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )

    def action_approve(self):
        """Approve the investment (manager action)."""
        self.ensure_one()
        if self.state != 'pending_approval':
            raise UserError(_('Only pending investments can be approved!'))
        self.write({
            'state': 'approved',
            'approval_user_id': self.env.uid,
            'approval_date': fields.Date.today(),
        })
        self.message_post(
            body=_('Investment approved by %s.') % self.env.user.name,
            partner_ids=[],
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )

    def action_reject(self):
        """Reject the investment (manager action)."""
        self.ensure_one()
        if self.state != 'pending_approval':
            raise UserError(_('Only pending investments can be rejected!'))
        # Open wizard to enter rejection reason
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Investment'),
            'res_model': 'investment.subscription.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_subscription_id': self.id},
        }

    def action_register_payment(self):
        self.ensure_one()

        # If approval is required, check state
        if self._get_config('require_approval_for_investment', 'False') == 'True':
            if self.state not in ('approved', 'draft'):
                raise UserError(_('Investment must be approved before payment!'))

        if not self.payment_journal_id:
            raise UserError(_('Please select payment journal!'))

        payment_vals = {
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.partner_id.id,
            'journal_id': self.payment_journal_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'date': fields.Date.today(),
            'memo': _('Investment %s - %s') % (self.name, self.project_id.name),
        }

        payment = self.env['account.payment'].create(payment_vals)
        payment.action_post()

        self.write({
            'payment_id': payment.id,
            'payment_state': 'paid',
            'state': 'paid'
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment',
            'res_model': 'account.payment',
            'res_id': payment.id,
            'view_mode': 'form',
        }

    def action_activate(self):
        self.ensure_one()
        if self.payment_state != 'paid':
            raise UserError(_('Investment must be paid first!'))
        self.write({'state': 'active'})

    def action_create_return(self):
        """Create a return payment based on the actual return calculation type."""
        self.ensure_one()

        # ===== Validate subscription is active =====
        if self.state != 'active':
            raise UserError(_('Investment must be active to create returns!'))

        today = fields.Date.today()

        # ===== Check grace period =====
        if not self.grace_period_passed:
            diff = relativedelta(self.returns_start_date, today)
            months_remaining = diff.months + (diff.years * 12)
            days_remaining = diff.days

            raise UserError(_(
                'لم تنتهِ فترة السماح بعد!\n\n'
                'فترة السماح: %s شهر\n'
                'تاريخ الاستثمار: %s\n'
                'تاريخ بدء العوائد: %s\n\n'
                'المتبقي: %s شهر و %s يوم\n\n'
                'ستكون العوائد متاحة بدءًا من: %s'
            ) % (
                self.grace_period_months or 0,
                self.investment_date,
                self.returns_start_date,
                months_remaining,
                days_remaining,
                self.returns_start_date.strftime('%Y-%m-%d') if self.returns_start_date else 'N/A'
            ))

        # ===== Determine period start date =====
        if self.actual_return_ids:
            last_return = self.actual_return_ids.sorted('date_to', reverse=True)[0]
            next_date_from = last_return.date_to + timedelta(days=1)
        else:
            next_date_from = self.returns_start_date

        # ===== Validate return start date exists =====
        if not next_date_from:
            raise UserError(_(
                'Could not determine return start date!\n'
                'Please check the subscription settings.\n'
                'Investment Date: %s\n'
                'Grace Period: %s months'
            ) % (self.investment_date, self.grace_period_months or 0))

        # ===== Cannot create future returns =====
        if next_date_from > today:
            raise UserError(_(
                'The next return period starts on %s which is in the future!\n'
                'Please wait until the period begins.'
            ) % next_date_from.strftime('%Y-%m-%d'))

        # ===== Calculate period end date based on return type =====
        if self.return_calculation_type == 'fixed_monthly':
            next_date_to = next_date_from + relativedelta(months=1, days=-1)
        elif self.return_calculation_type == 'fixed_quarterly':
            next_date_to = next_date_from + relativedelta(months=3, days=-1)
        elif self.return_calculation_type == 'fixed_yearly':
            next_date_to = next_date_from + relativedelta(years=1, days=-1)
        elif self.return_calculation_type == 'custom':
            days = self.return_period_days or 30
            next_date_to = next_date_from + timedelta(days=days - 1)
        else:
            # Default to monthly for grace_period, capital_plus_return, etc.
            next_date_to = next_date_from + relativedelta(months=1, days=-1)

        # ===== Calculate expected amount based on return type =====
        if self.return_calculation_type in ('grace_period', 'capital_plus_return'):
            expected_amount = (
                self.fixed_return_amount
                if self.fixed_return_amount > 0
                else self.expected_period_return
            )
        else:
            expected_amount = self.expected_period_return

        # ===== Period name =====
        period_name = '%s / %s' % (
            next_date_from.strftime('%B %Y'),
            self.partner_id.name or 'Unknown'
        )

        # ===== Create return record =====
        try:
            return_payment = self.env['investment.actual.return'].create({
                'subscription_id': self.id,
                'date_from': next_date_from,
                'date_to': next_date_to,
                'expected_amount': expected_amount,
                'actual_amount': expected_amount,
                'period_name': period_name,
                'state': 'draft',
            })
        except Exception as e:
            raise UserError(_(
                'Failed to create return record:\n%s'
            ) % str(e))

        # ===== Open the return form =====
        return {
            'type': 'ir.actions.act_window',
            'name': _('Review Return Payment'),
            'res_model': 'investment.actual.return',
            'res_id': return_payment.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'form_view_initial_mode': 'edit',
            }
        }

    def action_close(self):
        self.write({'state': 'closed'})

    def action_cancel(self):
        if self.payment_id and self.payment_id.state == 'posted':
            self.payment_id.button_cancel()
        self.write({'state': 'cancelled'})

    def name_get(self):
        result = []
        for record in self:
            name = "%s (%s shares)" % (record.project_id.name, record.share_count)
            result.append((record.id, name))
        return result

    # ===== SQL Constraints =====

    _sql_constraints = [
        (
            'unique_name',
            'unique(name)',
            'Investment reference must be unique!'
        ),
    ]
