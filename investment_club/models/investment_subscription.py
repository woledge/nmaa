# investment_club/models/investment_subscription.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
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

    # --- العائد الأول ---
    return_1_amount = fields.Float(
        related='project_id.return_1_amount',
        string='Return 1 Amount',
        readonly=True,
        store=True
    )
    return_1_grace_months = fields.Integer(
        related='project_id.return_1_grace_months',
        string='Return 1 Grace (Months)',
        readonly=True,
        store=True
    )
    return_1_date = fields.Date(
        related='project_id.return_1_date',
        string='Return 1 Date',
        readonly=True,
        store=True
    )

    # --- العائد الثاني ---
    return_2_amount = fields.Float(
        related='project_id.return_2_amount',
        string='Return 2 Amount',
        readonly=True,
        store=True
    )
    return_2_percentage = fields.Float(
        related='project_id.return_2_percentage',
        string='Return 2 Percentage (%)',
        readonly=True,
        store=True
    )
    return_2_partner_share = fields.Char(
        related='project_id.return_2_partner_share',
        string='Partner Share Ratio',
        readonly=True,
        store=True
    )
    return_2_grace_months = fields.Integer(
        related='project_id.return_2_grace_months',
        string='Return 2 Grace (Months)',
        readonly=True,
        store=True
    )
    return_2_period_months = fields.Integer(
        related='project_id.return_2_period_months',
        string='Return 2 Period (Months)',
        readonly=True,
        store=True
    )
    return_2_duration_years = fields.Integer(
        related='project_id.return_2_duration_years',
        string='Return 2 Duration (Years)',
        readonly=True,
        store=True
    )
    return_2_first_date = fields.Date(
        related='project_id.return_2_first_date',
        string='Return 2 First Date',
        readonly=True,
        store=True
    )
    return_2_last_date = fields.Date(
        related='project_id.return_2_last_date',
        string='Return 2 Last Date',
        readonly=True,
        store=True
    )

    # --- إعدادات عامة ---
    contract_start_date = fields.Date(
        related='project_id.contract_start_date',
        string='Contract Start Date',
        readonly=True,
        store=True
    )
    contract_end_date = fields.Date(
        related='project_id.contract_end_date',
        string='Contract End Date',
        readonly=True,
        store=True
    )
    max_shares_per_investor = fields.Integer(
        related='project_id.max_shares_per_investor',
        string='Max Shares per Investor',
        readonly=True,
        store=True
    )

    # --- الحقول القديمة (للتوافق) ---
    grace_period_months = fields.Integer(
        related='project_id.grace_period_months',
        string='Grace Period (Months)',
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
        domain="[('type', 'in', ('bank', 'cash'))]",
        default=lambda self: self.env['account.journal'].search([
            ('type', '=', 'bank'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
    )

    payment_id = fields.Many2one(
        'account.payment',
        string='Payment',
        readonly=True,
        copy=False
    )

    contract_id = fields.Many2one(
        'sale.contract',
        string='Contract',
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
        ('reviewed', 'Reviewed'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('terminated', 'Terminated'),
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

    @api.depends('investment_date', 'return_1_grace_months', 'return_2_grace_months',
                 'return_1_amount', 'return_2_amount', 'return_2_period_months',
                 'return_2_percentage', 'share_count', 'amount', 'contract_end_date')
    def _compute_return_dates(self):
        for sub in self:
            if not sub.investment_date:
                sub.returns_start_date = False
                sub.capital_return_date = False
                sub.expected_period_return = 0.0
                continue

            # Returns start: based on return_2_grace_months (main grace period)
            grace_months = sub.return_2_grace_months or sub.grace_period_months or 0
            sub.returns_start_date = sub.investment_date + relativedelta(months=grace_months)

            # Capital return date (contract end)
            if sub.contract_end_date:
                sub.capital_return_date = sub.contract_end_date
            else:
                sub.capital_return_date = False

            # Expected return per period (Return 2 amount)
            if sub.return_2_amount > 0:
                sub.expected_period_return = sub.return_2_amount * sub.share_count
            elif sub.return_2_percentage > 0:
                sub.expected_period_return = (sub.return_2_percentage / 100) * sub.amount
            else:
                sub.expected_period_return = 0.0

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

    # ===== Validation =====
    @api.constrains('share_count', 'max_shares_per_investor')
    def _check_max_shares(self):
        for sub in self:
            if sub.max_shares_per_investor > 0 and sub.share_count > sub.max_shares_per_investor:
                raise ValidationError(_(
                    'Maximum shares per investor is %s! You selected %s shares.'
                ) % (sub.max_shares_per_investor, sub.share_count))

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
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Investment'),
            'res_model': 'investment.subscription.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_subscription_id': self.id},
        }
    def action_review_money_bank_inv(self):
        for rec in self:
            rec.state = 'reviewed'

    def action_register_payment(self):
        self.ensure_one()

        if self._get_config('require_approval_for_investment', 'False') == 'True':
            if self.state not in ('approved', 'draft'):
                raise UserError(_('Investment must be approved before payment!'))

        if not self.payment_journal_id:
            raise UserError(_('Please select payment journal!'))

        payment_vals = {
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.partner_id.id,
            'investment_subscription_id': self.id,
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
        contract = self._get_or_create_sale_contract()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Contract'),
            'res_model': 'sale.contract',
            'res_id': contract.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_contract(self):
        self.ensure_one()
        contract = self._get_or_create_sale_contract()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Contract'),
            'res_model': 'sale.contract',
            'res_id': contract.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_payment(self):
        self.ensure_one()
        if not self.payment_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Payment'),
            'res_model': 'account.payment',
            'res_id': self.payment_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_print_contract(self):
        self.ensure_one()
        contract = self._get_or_create_sale_contract()
        return contract.print_contract_report()

    def _get_or_create_sale_contract(self):
        self.ensure_one()
        if self.contract_id:
            return self.contract_id

        contract_template = self.env['contract.template'].search([], limit=1)
        contract_title = self.env['sale.contract.title'].search([], limit=1)
        agreement_text = contract_template.content if contract_template else self._get_default_contract_terms()

        contract = self.env['sale.contract'].create({
            'partner_id': self.partner_id.id,
            'contract_date': self.investment_date or fields.Date.today(),
            'amount_total': self.amount,
            'currency_id': self.currency_id.id,
            'investment_subscription_id': self.id,
            'contract_template_id': contract_template.id if contract_template else False,
            'contract_title_name': contract_title.id if contract_title else False,
            'agreement_terms': agreement_text,
            'note': _('Generated automatically from investment %s.') % self.name,
        })
        self.contract_id = contract.id
        return contract

    def _get_default_contract_terms(self):
        self.ensure_one()
        return """
            <p>This contract is generated automatically for the activated investment subscription.</p>
            <p><strong>Club:</strong> %s</p>
            <p><strong>Project:</strong> %s</p>
            <p><strong>Investment Reference:</strong> %s</p>
            <p><strong>Shares:</strong> %s</p>
            <p><strong>Investment Amount:</strong> %s</p>
            <p><strong>Contract Start Date:</strong> %s</p>
            <p><strong>Contract End Date:</strong> %s</p>
        """ % (
            self.club_id.display_name or '',
            self.project_id.display_name or '',
            self.name or '',
            self.share_count or 0,
            self.amount or 0.0,
            self.contract_start_date or '',
            self.contract_end_date or '',
        )

    def action_create_return(self):
        """Create a return payment based on the unified return system."""
        self.ensure_one()

        if self.state != 'active':
            raise UserError(_('Investment must be active to create returns!'))

        today = fields.Date.today()

        # ===== Check Return 1 (One-time) =====
        if self.return_1_amount > 0 and self.return_1_date:
            # Check if Return 1 already exists (any state except cancelled)
            return_1_exists = self.actual_return_ids.filtered(
                lambda r: r.return_type == 'return_1' and r.state != 'cancelled'
            )
            if not return_1_exists and today >= self.return_1_date:
                period_name = _('Return 1 - %s') % (self.return_1_date.strftime('%B %Y'))
                return_payment = self.env['investment.actual.return'].create({
                    'subscription_id': self.id,
                    'return_type': 'return_1',
                    'date_from': self.return_1_date,
                    'date_to': self.return_1_date,
                    'expected_amount': self.return_1_amount * self.share_count,
                    'actual_amount': self.return_1_amount * self.share_count,
                    'period_name': period_name,
                    'state': 'draft',
                })
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Review Return 1 Payment'),
                    'res_model': 'investment.actual.return',
                    'res_id': return_payment.id,
                    'view_mode': 'form',
                    'target': 'current',
                    'context': {'form_view_initial_mode': 'edit'},
                }

        # ===== Check grace period for Return 2 =====
        if not self.grace_period_passed:
            diff = relativedelta(self.returns_start_date, today)
            months_remaining = diff.months + (diff.years * 12)
            days_remaining = diff.days

            raise UserError(_(
                'لم تنتهِ فترة السكون بعد!\n\n'
                'فترة السكون: %s شهر\n'
                'تاريخ الاستثمار: %s\n'
                'تاريخ بدء العوائد: %s\n\n'
                'المتبقي: %s شهر و %s يوم\n\n'
                'ستكون العوائد متاحة بدءًا من: %s'
            ) % (
                self.return_2_grace_months or self.grace_period_months or 0,
                self.investment_date,
                self.returns_start_date,
                months_remaining,
                days_remaining,
                self.returns_start_date.strftime('%Y-%m-%d') if self.returns_start_date else 'N/A'
            ))

        # ===== Determine period for Return 2 =====
        return_2_returns = self.actual_return_ids.filtered(
            lambda r: r.return_type == 'return_2' and r.state != 'cancelled'
        )
        if return_2_returns:
            last_return = return_2_returns.sorted('date_to', reverse=True)[0]
            next_date_from = last_return.date_to + timedelta(days=1)
        else:
            next_date_from = self.return_2_first_date or self.returns_start_date

        if not next_date_from:
            raise UserError(_(
                'Could not determine return start date!\n'
                'Please check the subscription settings.\n'
                'Investment Date: %s\n'
                'Grace Period: %s months'
            ) % (self.investment_date, self.return_2_grace_months or self.grace_period_months or 0))

        if next_date_from > today:
            raise UserError(_(
                'The next return period starts on %s which is in the future!\n'
                'Please wait until the period begins.'
            ) % next_date_from.strftime('%Y-%m-%d'))

        # Check if past last return date
        if self.return_2_last_date and next_date_from > self.return_2_last_date:
            raise UserError(_(
                'All return payments have been completed!\n'
                'Last return date was: %s'
            ) % self.return_2_last_date.strftime('%Y-%m-%d'))

        # Calculate period end
        period_months = self.return_2_period_months or 1
        next_date_to = next_date_from + relativedelta(months=period_months, days=-1)

        # Check if period exceeds last date
        if self.return_2_last_date and next_date_to > self.return_2_last_date:
            next_date_to = self.return_2_last_date

        # Calculate expected amount
        expected_amount = self.expected_period_return or 0.0

        period_name = '%s / %s' % (
            next_date_from.strftime('%B %Y'),
            self.partner_id.name or 'Unknown'
        )

        try:
            return_payment = self.env['investment.actual.return'].create({
                'subscription_id': self.id,
                'return_type': 'return_2',
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

    def action_terminate(self):
        """Open investment subscription termination wizard."""
        self.ensure_one()
        if self.state not in ('paid', 'active'):
            raise UserError(_('Only paid or active investments can be terminated!'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Terminate Investment Share'),
            'res_model': 'subscription.terminate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_subscription_id': self.id,
            },
        }

    def action_death_case(self):
        """Open investor death case wizard for this subscription."""
        self.ensure_one()
        if self.state not in ('paid', 'active'):
            raise UserError(_('Only paid or active investments can process death case!'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Investor Death Case'),
            'res_model': 'investor.death.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_membership_id': self.membership_id.id,
                'default_subscription_id': self.id,
            },
        }

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
