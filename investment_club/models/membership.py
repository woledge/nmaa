# investment_club/models/membership.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from psycopg2 import IntegrityError
from datetime import timedelta


class InvestmentMembership(models.Model):
    _name = 'investment.membership'
    _description = 'Investment Membership'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'investor_code'

    # ===== Basic Fields =====

    membership_number = fields.Char(
        string='Internal Reference',
        readonly=True,
        copy=False,
        default='New'
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True,
    )

    club_id = fields.Many2one(
        'investment.club',
        string='Club',
        required=True,
        tracking=True
    )

    membership_product_id = fields.Many2one(
        'product.product',
        string='Membership Product',
        domain="[('type', '=', 'service')]",
        required=True
    )

    initial_membership_fee = fields.Float(
        string='Initial Membership Fee',
        related='membership_product_id.lst_price',
        readonly=True,
        store=True
    )

    subscription_product_id = fields.Many2one(
        'product.product',
        string='Subscription Product',
        domain="[('type', '=', 'service')]"
    )

    annual_subscription_fee = fields.Float(
        string='Annual Subscription Fee',
        required=True
    )

    subscription_period = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ], string='Subscription Period', default='yearly', required=True)

    membership_date = fields.Date(
        string='Start Date',
        default=fields.Date.today,
        required=True
    )

    expiry_date = fields.Date(
        string='Expiry Date',
        compute='_compute_dates',
        store=True
    )

    auto_renew = fields.Boolean(string='Auto Renew', default=True)

    initial_invoice_id = fields.Many2one(
        'account.move',
        string='Initial Invoice',
        readonly=True,
        copy=False
    )

    current_invoice_id = fields.Many2one(
        'account.move',
        string='Current/Renewal Invoice',
        readonly=True,
        copy=False
    )

    payment_state = fields.Selection(
        related='current_invoice_id.payment_state',
        string='Payment Status',
        readonly=True,
        store=True
    )

    renewal_ids = fields.One2many(
        'membership.renewal',
        'membership_id',
        string='Renewal History'
    )

    next_renewal_date = fields.Date(
        string='Next Renewal Date',
        compute='_compute_next_renewal',
        store=True
    )

    next_renewal_amount = fields.Float(
        string='Next Renewal Amount',
        related='annual_subscription_fee',
        readonly=True,
        store=True
    )

    renewal_status = fields.Selection([
        ('paid', 'Paid'),
        ('due', 'Due'),
        ('overdue', 'Overdue'),
        ('not_due', 'Not Due Yet')
    ], string='Renewal Status', compute='_compute_renewal_status', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('initial_invoiced', 'Initial Invoiced'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    investment_ids = fields.One2many(
        'investment.subscription',
        'membership_id',
        string='Investments'
    )

    total_invested = fields.Float(
        string='Total Invested',
        compute='_compute_total',
        store=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        store=True
    )

    notes = fields.Text(string='Notes')

    # ===== Termination Fields =====

    original_paid_fee = fields.Float(
        string='Original Paid Fee',
        default=0.0,
        help='المبلغ الذي دفعه العميل عند تفعيل العضوية'
    )

    termination_date = fields.Date(
        string='Termination Date',
        readonly=True,
        copy=False
    )

    termination_reason = fields.Text(
        string='Termination Reason',
        readonly=True
    )

    termination_refund_amount = fields.Float(
        string='Termination Refund Amount',
        readonly=True
    )

    termination_deduction = fields.Float(
        string='Termination Deduction',
        readonly=True,
        help='مبلغ الخصم عند الفسخ خلال أول 3 شهور'
    )

    investor_code = fields.Char(string='Investor code', store=True)

    invoice_count = fields.Integer(compute='_compute_invoice_count')

    investment_count = fields.Integer(compute='_compute_investment_count')

    # ===== Onchange =====

    @api.onchange('subscription_product_id')
    def _onchange_subscription_product(self):
        """Sync annual subscription fee from selected product"""
        if self.subscription_product_id:
            self.annual_subscription_fee = self.subscription_product_id.lst_price

    # ===== Compute Methods =====

    @api.depends('membership_date', 'subscription_period', 'renewal_ids.new_expiry_date')
    def _compute_dates(self):
        """Compute expiry date based on membership date or last renewal."""
        for membership in self:
            if not membership.membership_date:
                membership.expiry_date = False
                continue

            if membership.renewal_ids:
                last_renewal = membership.renewal_ids.sorted('renewal_date', reverse=True)[0]
                membership.expiry_date = last_renewal.new_expiry_date
            else:
                if membership.subscription_period == 'monthly':
                    membership.expiry_date = membership.membership_date + timedelta(days=29)
                elif membership.subscription_period == 'quarterly':
                    membership.expiry_date = membership.membership_date + timedelta(days=89)
                else:  # yearly
                    membership.expiry_date = membership.membership_date + timedelta(days=364)

    @api.depends('expiry_date')
    def _compute_next_renewal(self):
        for membership in self:
            membership.next_renewal_date = membership.expiry_date

    @api.depends('next_renewal_date', 'state')
    def _compute_renewal_status(self):
        today = fields.Date.today()
        for membership in self:
            if membership.state != 'active':
                membership.renewal_status = 'not_due'
            elif not membership.next_renewal_date:
                membership.renewal_status = 'not_due'
            elif membership.next_renewal_date > today:
                membership.renewal_status = 'not_due'
            elif membership.next_renewal_date == today:
                membership.renewal_status = 'due'
            else:
                membership.renewal_status = 'overdue'

    @api.depends('investment_ids.amount', 'investment_ids.state')
    def _compute_total(self):
        for membership in self:
            membership.total_invested = sum(
                membership.investment_ids.filtered(lambda i: i.state == 'active').mapped('amount')
            )

    @api.depends('initial_invoice_id', 'current_invoice_id')
    def _compute_invoice_count(self):
        for rec in self:
            count = 0
            if rec.initial_invoice_id:
                count += 1
            if rec.current_invoice_id and rec.current_invoice_id != rec.initial_invoice_id:
                count += 1
            rec.invoice_count = count

    # ===== Actions =====

    def action_create_initial_invoice(self):
        self.ensure_one()

        if not self.investor_code:
            self.investor_code = self._generate_investor_code()

        if not self.membership_product_id:
            raise UserError(_('Please select membership product!'))

        if self.initial_invoice_id:
            raise UserError(_('Initial invoice already exists!'))

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'investor_code_id': self.id or False,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'product_id': self.membership_product_id.id,
                'name': _('Membership Fee - %s %s') % (self.club_id.name, self.investor_code or ''),
                'quantity': 1,
                'price_unit': self.initial_membership_fee,
            })],
        }

        invoice = self.env['account.move'].create(invoice_vals)

        self.write({
            'initial_invoice_id': invoice.id,
            'current_invoice_id': invoice.id,
            'state': 'initial_invoiced'
        })

        invoice.action_post()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
        }

    def action_open_invoice(self):
        self.ensure_one()

        invoice = self.current_invoice_id or self.initial_invoice_id

        if not invoice:
            raise UserError("No invoice linked to this record.")

        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
        }

    def action_create_renewal_invoice(self):
        self.ensure_one()

        if self.annual_subscription_fee <= 0:
            raise UserError(_('Please set annual subscription fee!'))

        renewal_vals = {
            'membership_id': self.id,
            'renewal_date': fields.Date.today(),
            'amount': self.annual_subscription_fee,
            'period': self.subscription_period,
            'old_expiry_date': self.expiry_date,
            'new_expiry_date': self._calculate_new_expiry(),
        }
        renewal = self.env['membership.renewal'].create(renewal_vals)

        product = self.subscription_product_id or self.membership_product_id

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'name': _('Annual Subscription - %s - %s') % (self.club_id.name,),
                'quantity': 1,
                'price_unit': self.annual_subscription_fee,
            })],
        }

        invoice = self.env['account.move'].create(invoice_vals)
        renewal.write({'invoice_id': invoice.id, 'state': 'invoiced'})

        self.write({
            'current_invoice_id': invoice.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Renewal Invoice',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
        }

    def action_confirm_payment(self):
        self.ensure_one()
        if self.payment_state == 'paid':
            # Store original paid fee at activation time
            vals = {'state': 'active'}
            if not self.original_paid_fee or self.original_paid_fee <= 0:
                vals['original_paid_fee'] = self.initial_membership_fee
            self.write(vals)
            last_renewal = self.renewal_ids.sorted('renewal_date', reverse=True)[:1]
            if last_renewal:
                last_renewal.write({'state': 'paid'})
        else:
            raise UserError(_('Invoice is not paid yet!'))

    def _calculate_new_expiry(self):
        """Calculate new expiry starting from the day after current expiry."""
        if not self.expiry_date:
            return fields.Date.today()

        new_start = self.expiry_date + timedelta(days=1)

        if self.subscription_period == 'monthly':
            return new_start + timedelta(days=29)
        elif self.subscription_period == 'quarterly':
            return new_start + timedelta(days=89)
        else:  # yearly
            return new_start + timedelta(days=364)

    def action_terminate(self):
        """Open membership termination wizard."""
        self.ensure_one()
        if self.state not in ('active', 'initial_invoiced'):
            raise UserError(_('Only active memberships can be terminated!'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Terminate Membership'),
            'res_model': 'membership.terminate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_membership_id': self.id,
            },
        }

    def action_death_case(self):
        """Open investor death case wizard."""
        self.ensure_one()
        if self.state not in ('active', 'initial_invoiced'):
            raise UserError(_('Only active memberships can process death case!'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Investor Death Case'),
            'res_model': 'investor.death.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_membership_id': self.id,
            },
        }

    def action_cancel(self):
        """Cancel membership and cancel unpaid related invoices."""
        if self.current_invoice_id and self.current_invoice_id.payment_state != 'paid':
            self.current_invoice_id.button_cancel()
        for renewal in self.renewal_ids.filtered(lambda r: r.state == 'invoiced'):
            if renewal.invoice_id and renewal.invoice_id.payment_state != 'paid':
                renewal.invoice_id.button_cancel()
        self.write({'state': 'cancelled'})

    def action_create_investment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Investment',
            'res_model': 'investment.subscription',
            'view_mode': 'form',
            'context': {
                'default_membership_id': self.id,
                'default_partner_id': self.partner_id.id,
            },
            'target': 'current',
        }

    def action_open_investment(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Investments'),
            'res_model': 'investment.subscription',
            'view_mode': 'list,form',
            'domain': [('membership_id', '=', self.id)],
            'target': 'current',
            'context': {
                'default_membership_id': self.id,
                'default_partner_id': self.partner_id.id,
            },
        }

        if self.investment_count == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.investment_ids[:1].id,
            })

        return action

    def _compute_investment_count(self):
        for rec in self:
            rec.investment_count = len(rec.investment_ids)

    # ===== Sequence / Investor Code (Merged) =====

    def _get_club_sequence(self, club_id=None):
        """Get or create a dedicated sequence for a club."""
        if club_id:
            club = self.env['investment.club'].browse(club_id)
        elif hasattr(self, 'club_id') and self.club_id:
            club = self.club_id
        else:
            return False

        if not club:
            return False

        club_name = club.name.replace(' ', '')
        sequence_code = f'investor.code.{club.id}'

        sequence = self.env['ir.sequence'].sudo().search([
            ('code', '=', sequence_code),
        ], limit=1)

        if not sequence:
            sequence = self.env['ir.sequence'].sudo().create({
                'name': f'Investor Code - {club.name}',
                'code': sequence_code,
                'prefix': f'INVS-{club_name}-',
                'padding': 5,
                'number_increment': 1,
            })

        return sequence

    def _generate_investor_code(self):
        """Generate: INVS-ElAhly-00001 (per club)"""
        self.ensure_one()
        sequence = self._get_club_sequence()
        if sequence:
            return sequence.next_by_id()
        return False

    # ===== CRUD Overrides =====

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('membership_number') or vals.get('membership_number') == 'New':
                vals['membership_number'] = self.env['ir.sequence'].next_by_code('investment.membership')

            if vals.get('club_id') and not vals.get('investor_code'):
                vals['investor_code'] = self._generate_code_for_vals(vals['club_id'])

        try:
            return super().create(vals_list)
        except IntegrityError:
            for vals in vals_list:
                if vals.get('club_id'):
                    vals['investor_code'] = self._generate_code_for_vals(vals['club_id'])
            return super().create(vals_list)

    def copy(self, default=None):
        """Reset investor code and membership number on duplicate."""
        default = dict(default or {})
        default['investor_code'] = False
        default['membership_number'] = 'New'
        return super().copy(default)

    def _generate_code_for_vals(self, club_id):
        """Generate investor code from vals dict (used during create)."""
        sequence = self._get_club_sequence(club_id)
        if sequence:
            return sequence.next_by_id()
        return False

    # ===== Cron / Scheduled Actions =====

    def _get_config(self, key, default=False):
        """Read a config parameter value."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'investment_club.%s' % key, default
        )

    def _cron_send_renewal_reminders(self):
        """Send renewal reminder notifications for memberships expiring soon."""
        if not self._get_config('enable_renewal_notifications', 'True') == 'True':
            return

        days_before = int(self._get_config('auto_renewal_days', '7'))
        today = fields.Date.today()
        reminder_date = today + timedelta(days=days_before)

        memberships = self.search([
            ('state', '=', 'active'),
            ('expiry_date', '<=', reminder_date),
            ('expiry_date', '>=', today),
            ('auto_renew', '=', True),
        ])

        for membership in memberships:
            days_left = (membership.expiry_date - today).days
            self._send_renewal_notification(membership, days_left)

        overdue = self.search([
            ('state', '=', 'active'),
            ('expiry_date', '<', today),
        ])

        for membership in overdue:
            days_overdue = (today - membership.expiry_date).days
            self._send_overdue_notification(membership, days_overdue)

    def _send_renewal_notification(self, membership, days_left):
        """Send a renewal reminder via Odoo's chatter/message system."""
        subject = _('Membership Renewal Reminder: %s') % (membership.investor_code or membership.membership_number)
        body = _(
            '<p>Dear <b>%s</b>,</p>'
            '<p>Your membership in <b>%s</b> will expire in <b>%s days</b> on <b>%s</b>.</p>'
            '<p>Renewal Amount: <b>%s %s</b></p>'
            '<p>Please renew your membership to avoid any interruption.</p>'
        ) % (
            membership.partner_id.name or '',
            membership.club_id.name or '',
            days_left,
            membership.expiry_date,
            membership.currency_id.symbol or '',
            membership.annual_subscription_fee,
        )
        membership.message_post(
            subject=subject,
            body=body,
            partner_ids=[membership.partner_id.id],
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )

    def _send_overdue_notification(self, membership, days_overdue):
        """Send an overdue notification."""
        subject = _('انتهاء العضوية: %s') % (membership.investor_code or membership.membership_number)

        body = _(
            '<p>عزيزي <b>%s</b>،</p>'
            '<p>لقد انتهت عضويتك في <b>%s</b> منذ <b>%s يوم</b> بتاريخ <b>%s</b>.</p>'
            '<p>يرجى تجديد العضوية في أقرب وقت ممكن.</p>'
        ) % (
            membership.partner_id.name or '',
            membership.club_id.name or '',
            days_overdue,
            membership.expiry_date,
        )

        membership.message_post(
            subject=subject,
            body=body,
            partner_ids=[membership.partner_id.id],
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )

    def _cron_auto_expire_memberships(self):
        """Automatically set active memberships to expired if past expiry."""
        today = fields.Date.today()
        expired = self.search([
            ('state', '=', 'active'),
            ('expiry_date', '<', today),
        ])
        expired.write({'state': 'expired'})

    # ===== SQL Constraints =====

    _sql_constraints = [
        (
            'unique_investor_code_per_club',
            'unique(investor_code, club_id)',
            'Investor code must be unique per club!'
        ),
    ]
