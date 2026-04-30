from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class MembershipTerminateWizard(models.TransientModel):
    _name = 'membership.terminate.wizard'
    _description = 'Membership Termination Wizard'

    # ===== Membership Reference =====
    membership_id = fields.Many2one(
        'investment.membership',
        string='Membership',
        required=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        related='membership_id.partner_id',
        string='Customer',
        readonly=True
    )

    club_id = fields.Many2one(
        'investment.club',
        related='membership_id.club_id',
        string='Club',
        readonly=True
    )

    membership_date = fields.Date(
        related='membership_id.membership_date',
        string='Membership Start Date',
        readonly=True
    )

    investor_code = fields.Char(
        related='membership_id.investor_code',
        string='Investor Code',
        readonly=True
    )

    # ===== Financial Fields =====
    original_paid_fee = fields.Float(
        string='Original Paid Amount',
        compute='_compute_financials',
        store=True
    )

    current_fee = fields.Float(
        string='Current Membership Value',
        compute='_compute_financials',
        store=True
    )

    termination_attachment = fields.Binary(
        string='Attachment',
        attachment=True
    )

    termination_attachment_name = fields.Char(
        string='Attachment Filename'
    )

    increase_amount = fields.Float(
        string='Increase Amount',
        compute='_compute_financials',
        store=True,
        help='الفرق بين القيمة الحالية والمبلغ المدفوع'
    )

    # ===== Termination Calculations =====
    months_elapsed = fields.Integer(
        string='Months Elapsed',
        compute='_compute_period',
        store=True
    )

    is_first_3_months = fields.Boolean(
        string='Within First 3 Months',
        compute='_compute_period',
        store=True
    )

    deduction_amount = fields.Float(
        string='Deduction (First 3 Months)',
        default=6500.0,
        help='مبلغ 6500 جنيه يخصم في حالة الفسخ خلال أول 3 شهور'
    )

    actual_deduction = fields.Float(
        string='Actual Deduction Applied',
        compute='_compute_refund',
        store=True,
        help='الخصم الفعلي المطبق (الخصم أو قيمة العضوية أيهما أقل)'
    )

    client_share_increase = fields.Float(
        string='Client Share of Increase (70%)',
        compute='_compute_financials',
        store=True,
        help='نصيب العميل 70% من قيمة الزيادة'
    )

    company_share_increase = fields.Float(
        string='Company Share of Increase (30%)',
        compute='_compute_financials',
        store=True,
        help='نصيب الشركة 30% من قيمة الزيادة'
    )

    company_income = fields.Float(
        string='Company Income Amount',
        compute='_compute_refund',
        store=True,
        help='إجمالي المبلغ الذي يحق للشركة'
    )

    refund_amount = fields.Float(
        string='Final Refund Amount',
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

    @api.depends('membership_id')
    def _compute_period(self):
        today = fields.Date.today()
        for wizard in self:
            if not wizard.membership_id or not wizard.membership_id.membership_date:
                wizard.months_elapsed = 0
                wizard.is_first_3_months = False
                continue

            start = wizard.membership_id.membership_date
            diff = relativedelta(today, start)
            wizard.months_elapsed = diff.months + (diff.years * 12)
            wizard.is_first_3_months = wizard.months_elapsed < 3

    @api.depends('membership_id')
    def _compute_financials(self):
        for wizard in self:
            if not wizard.membership_id:
                wizard.original_paid_fee = 0.0
                wizard.current_fee = 0.0
                wizard.increase_amount = 0.0
                wizard.client_share_increase = 0.0
                wizard.company_share_increase = 0.0
                continue

            membership = wizard.membership_id

            # Original paid = what was stored at activation
            wizard.original_paid_fee = membership.original_paid_fee or 0.0

            # Current value = product list price now
            wizard.current_fee = membership.initial_membership_fee or 0.0

            # Increase
            increase = wizard.current_fee - wizard.original_paid_fee
            if increase > 0:
                wizard.increase_amount = increase
                wizard.client_share_increase = increase * 0.70
                wizard.company_share_increase = increase * 0.30
            else:
                wizard.increase_amount = 0.0
                wizard.client_share_increase = 0.0
                wizard.company_share_increase = 0.0

    @api.depends('membership_id', 'is_first_3_months', 'current_fee',
                 'original_paid_fee', 'increase_amount', 'deduction_amount')
    def _compute_refund(self):
        for wizard in self:
            if not wizard.membership_id:
                wizard.refund_amount = 0.0
                wizard.actual_deduction = 0.0
                wizard.company_income = 0.0
                continue

            if wizard.is_first_3_months:
                # خلال أول 3 شهور: أصل المبلغ - خصم (مش أكتر من المبلغ نفسه)
                wizard.actual_deduction = min(wizard.deduction_amount, wizard.original_paid_fee)
                refund = wizard.original_paid_fee - wizard.actual_deduction
                wizard.refund_amount = max(refund, 0.0)
                # الشركة تستفيد بمبلغ الخصم
                wizard.company_income = wizard.actual_deduction
            elif wizard.increase_amount > 0:
                # بعد 3 شهور وفيه زيادة: أصل المبلغ + 70% من الزيادة للعميل
                wizard.refund_amount = wizard.original_paid_fee + wizard.client_share_increase
                wizard.actual_deduction = 0.0
                # الشركة تستفيد بـ 30% من الزيادة
                wizard.company_income = wizard.company_share_increase
            else:
                # بعد 3 شهور ومفيش زيادة: أصل المبلغ كامل للعميل
                wizard.refund_amount = wizard.original_paid_fee
                wizard.actual_deduction = 0.0
                wizard.company_income = 0.0

    # ===== Actions =====

    def _get_default_income_account(self):
        """Get the default income account for recording company share."""
        self.ensure_one()
        company = self.membership_id.company_id or self.env.company

        # First try to get from the default product category income account.
        default_category = self.env.ref('product.product_category_all', raise_if_not_found=False)
        income_account = default_category.with_company(company).property_account_income_categ_id \
            if default_category else self.env['account.account']
        if income_account:
            return income_account

        category = self.env['product.category'].with_company(company).search([
            ('property_account_income_categ_id', '!=', False),
        ], limit=1)
        if category.property_account_income_categ_id:
            return category.property_account_income_categ_id

        # Fallback: find a regular income account for the company.
        income_account = self.env['account.account'].search([
            ('company_ids', 'in', company.ids),
            ('deprecated', '=', False),
            ('account_type', 'in', ('income', 'income_other')),
        ], limit=1)
        if income_account:
            return income_account

        return self.env['account.account']

    def _create_company_income_entry(self, membership, income_amount, description):
        """Create a journal entry recording company income from termination.

        Creates a journal entry:
        - Debit: Bank/Cash account (money stays in company)
        - Credit: Income account (recognizing revenue)

        Args:
            membership: The membership record being terminated
            income_amount: The amount the company earns
            description: Description for the journal entry lines

        Returns:
            account.move record or False if no account found
        """
        if income_amount <= 0:
            return False

        income_account = self._get_default_income_account()
        if not income_account:
            return False

        # Try to get liquidity account from the refund journal.
        bank_account = self.refund_journal_id.default_account_id

        if bank_account:
            # Journal entry using the refund journal (bank)
            move_vals = {
                'move_type': 'entry',
                'journal_id': self.refund_journal_id.id,
                'date': fields.Date.today(),
                'ref': _('Company Income - Membership Termination - %s') % (
                    membership.investor_code or ''
                ),
                'line_ids': [
                    (0, 0, {
                        'account_id': bank_account.id,
                        'debit': income_amount,
                        'credit': 0.0,
                        'partner_id': membership.partner_id.id,
                        'name': description,
                    }),
                    (0, 0, {
                        'account_id': income_account.id,
                        'debit': 0.0,
                        'credit': income_amount,
                        'name': description,
                    }),
                ],
            }
            move = self.env['account.move'].create(move_vals)
            move.action_post()
            return move

        # Fallback: use General Journal (Misc Operations)
        misc_journal = self.env['account.journal'].search(
            [('type', '=', 'general'), ('company_id', '=', membership.company_id.id)],
            limit=1
        )
        if misc_journal:
            move_vals = {
                'move_type': 'entry',
                'journal_id': misc_journal.id,
                'date': fields.Date.today(),
                'ref': _('Company Income - Membership Termination - %s') % (
                    membership.investor_code or ''
                ),
                'line_ids': [
                    (0, 0, {
                        'account_id': misc_journal.default_account_id.id,
                        'debit': income_amount,
                        'credit': 0.0,
                        'partner_id': membership.partner_id.id,
                        'name': description,
                    }),
                    (0, 0, {
                        'account_id': income_account.id,
                        'debit': 0.0,
                        'credit': income_amount,
                        'name': description,
                    }),
                ],
            }
            move = self.env['account.move'].create(move_vals)
            move.action_post()
            return move

        return False

    def _attach_termination_document(self, membership):
        """Attach the termination document to the membership record."""
        if self.termination_attachment:
            self.env['ir.attachment'].create({
                'name': self.termination_attachment_name or 'membership_termination_attachment',
                'res_model': membership._name,
                'res_id': membership.id,
                'type': 'binary',
                'datas': self.termination_attachment,
                'datas_fname': self.termination_attachment_name or 'membership_termination_attachment',
                'mimetype': 'application/octet-stream',
            })

    def action_confirm_termination(self):
        self.ensure_one()
        if not self.reason:
            raise UserError(_('Please provide a termination reason!'))

        if self.refund_amount < 0:
            raise UserError(_('Refund amount is negative! Cannot proceed.'))

        membership = self.membership_id

        if membership.state not in ('active', 'initial_invoiced'):
            raise UserError(_('Membership must be active to terminate!'))

        # ===== 1. Create refund payment to customer =====
        if self.refund_amount > 0:
            payment_vals = {
                'payment_type': 'outbound',
                'partner_type': 'customer',
                'partner_id': membership.partner_id.id,
                'journal_id': self.refund_journal_id.id,
                'amount': self.refund_amount,
                'currency_id': membership.currency_id.id,
                'date': fields.Date.today(),
                'memo': _(
                    'Membership Termination Refund - %s'
                ) % (membership.investor_code or membership.membership_number),
            }
            payment = self.env['account.payment'].create(payment_vals)
            payment.action_post()

        # ===== 2. Create company income journal entry =====
        company_income_move = False

        if self.is_first_3_months and self.actual_deduction > 0:
            # خلال أول 3 شهور: الخصم يبقى إيراد للشركة
            description = _(
                'Membership early termination penalty (deduction) - %s'
            ) % (membership.investor_code or '')
            company_income_move = self._create_company_income_entry(
                membership, self.actual_deduction, description
            )

        elif not self.is_first_3_months and self.company_share_increase > 0:
            # بعد 3 شهور وفيه زيادة: 30% من الزيادة بيبقوا إيراد للشركة
            description = _(
                'Company share (30%% of membership value increase) - %s'
            ) % (membership.investor_code or '')
            company_income_move = self._create_company_income_entry(
                membership, self.company_share_increase, description
            )

        # ===== 3. Update membership state =====
        membership.write({
            'state': 'terminated',
            'termination_date': fields.Date.today(),
            'termination_reason': self.reason,
            'termination_refund_amount': self.refund_amount,
            'termination_deduction': self.actual_deduction,
        })

        self._attach_termination_document(membership)

        # ===== 4. Post chatter message =====
        summary = _(
            '<p><b>تم فسخ عقد العضوية</b></p>'
            '<ul>'
            '<li>العميل: <b>%s</b></li>'
            '<li>كود المستثمر: <b>%s</b></li>'
            '<li>المبلغ الأصلي المدفوع: <b>%s</b></li>'
        ) % (
            membership.partner_id.name or '',
            membership.investor_code or '',
            membership.original_paid_fee or 0.0,
        )

        if self.is_first_3_months:
            summary += _(
                '<li>الخصم المطبق: <b>%s</b></li>'
                '<li>مبلغ الاسترداد للعميل: <b>%s</b></li>'
                '<li>إيراد الشركة (الخصم): <b>%s</b></li>'
            ) % (
                self.actual_deduction,
                self.refund_amount,
                self.company_income,
            )
        elif self.increase_amount > 0:
            summary += _(
                '<li>القيمة الحالية للعضوية: <b>%s</b></li>'
                '<li>قيمة الزيادة: <b>%s</b></li>'
                '<li>نصيب العميل (70%% من الزيادة): <b>%s</b></li>'
                '<li>نصيب الشركة (30%% من الزيادة): <b>%s</b></li>'
                '<li>مبلغ الاسترداد النهائي للعميل: <b>%s</b></li>'
            ) % (
                self.current_fee,
                self.increase_amount,
                self.client_share_increase,
                self.company_share_increase,
                self.refund_amount,
            )
        else:
            summary += _(
                '<li>مبلغ الاسترداد للعميل: <b>%s</b></li>'
            ) % self.refund_amount

        summary += _('<li>السبب: <b>%s</b></li>') % self.reason

        if company_income_move:
            summary += _(
                '<li>قيد المحاسبة للشركة: <b>%s</b></li>'
            ) % company_income_move.name

        summary += '</ul>'

        membership.message_post(
            body=summary,
            partner_ids=[membership.partner_id.id],
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )

        return {'type': 'ir.actions.act_window_close'}
