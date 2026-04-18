# investment_club/models/membership.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta
from psycopg2 import IntegrityError


class InvestmentMembership(models.Model):
    _name = 'investment.membership'
    _description = 'Investment Membership'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ===== رقم العضوية الفريد للعميل =====

    
    membership_number = fields.Char(
        string='Internal Reference',
        readonly=True,
        copy=False,
        default='New'
    )
    
    # ⚠️ التصحيح: شلت required=True و compute مع بعض
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        tracking=True,
        store=True,  # أضفت store=True عشان يتخزن
        readonly=False,  # يسمح بالتعديل اليدوي
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


    investor_code = fields.Char(string='Investor code',store=True)

    invoice_id = fields.Many2one('account.move', string='invoice')
    invoice_count = fields.Integer(compute='_compute_invoice_count')




    @api.onchange('subscription_product_id')
    def _onchange_subscription_product(self):
        if self.subscription_product_id and not self.annual_subscription_fee:
            self.annual_subscription_fee = self.subscription_product_id.lst_price

    @api.depends('membership_date', 'subscription_period', 'renewal_ids')
    def _compute_dates(self):
        """حساب تاريخ الانتهاء - نهاية المدة (يوم قبل بداية الفترة الجديدة)"""
        for membership in self:
            if membership.membership_date:
                if membership.renewal_ids:
                    last_renewal = membership.renewal_ids.sorted('renewal_date', reverse=True)[0]
                    membership.expiry_date = last_renewal.new_expiry_date
                    # نبدأ من اليوم اللي بعد الـ expiry date القديم
                else:
                    # حساب من membership_date فقط لو مافي تجديدات
                    if membership.subscription_period == 'monthly':
                        membership.expiry_date = membership.membership_date + timedelta(days=29)
                    elif membership.subscription_period == 'quarterly':
                        membership.expiry_date = membership.membership_date + timedelta(days=89)
                    else:
                        membership.expiry_date = membership.membership_date + timedelta(days=364)
            else:
                membership.expiry_date = False

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

        # ✅ الربط + تغيير الحالة
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

    @api.depends('initial_invoice_id', 'current_invoice_id')
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = sum([
                bool(rec.initial_invoice_id),
            ])

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
                'name': _('Annual Subscription - %s - %s') % (self.club_id.name, ),
                'quantity': 1,
                'price_unit': self.annual_subscription_fee,
            })],
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        renewal.write({'invoice_id': invoice.id, 'state': 'invoiced'})
        
        self.write({
            'current_invoice_id': invoice.id,
            'state': 'initial_invoiced'
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
            self.write({'state': 'active'})
            last_renewal = self.renewal_ids.sorted('renewal_date', reverse=True)[:1]
            if last_renewal:
                last_renewal.write({'state': 'paid'})
        else:
            raise UserError(_('Invoice is not paid yet!'))

    def _calculate_new_expiry(self):
        """حساب تاريخ الانتهاء الجديد - نهاية المدة (يوم قبل بداية الفترة الجديدة)"""
        if not self.expiry_date:
            return fields.Date.today()
        
        # نبدأ من اليوم اللي بعد الـ expiry date
        new_start = self.expiry_date + timedelta(days=1)
        
        if self.subscription_period == 'monthly':
            return new_start + timedelta(days=29)  # 30 يوم - 1
        elif self.subscription_period == 'quarterly':
            return new_start + timedelta(days=89)  # 90 يوم - 1
        else:  # yearly
            return new_start + timedelta(days=364)  # 365 يوم - 1

    def action_cancel(self):
        if self.current_invoice_id and self.current_invoice_id.payment_state != 'paid':
            self.current_invoice_id.button_cancel()
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

    # =============================================
    # 1) يجيب أو ينشئ sequence للنادي
    # =============================================
    def _get_club_sequence(self):
        """Get or create a dedicated sequence for this club"""
        self.ensure_one()
        if not self.club_id:
            return False

        club_name = self.club_id.name.replace(' ', '')
        sequence_code = f'investor.code.{self.club_id.id}'

        # هل فيه sequence لهذا النادي؟
        sequence = self.env['ir.sequence'].sudo().search([
            ('code', '=', sequence_code),
        ], limit=1)

        if not sequence:
            # أول مرة → أنشئ sequence خاص بالنادي
            sequence = self.env['ir.sequence'].sudo().create({
                'name': f'Investor Code - {self.club_id.name}',
                'code': sequence_code,
                'prefix': f'INVS-{club_name}-',
                'padding': 5,
                'number_increment': 1,
            })

        return sequence

    # =============================================
    # 2) توليد الكود من sequence النادي
    # =============================================
    def _generate_investor_code(self):
        """Generate: INVS-ElAhly-00001 (per club)"""
        self.ensure_one()
        sequence = self._get_club_sequence()
        if sequence:
            return sequence.next_by_id()
        return False



    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # membership number
            if not vals.get('membership_number') or vals.get('membership_number') == 'New':
                vals['membership_number'] = self.env['ir.sequence'].next_by_code('investment.membership')

            # investor code generation BEFORE create
            if vals.get('club_id') and not vals.get('investor_code'):
                vals['investor_code'] = self._generate_code_for_vals(vals['club_id'])

        try:
            return super().create(vals_list)

        except IntegrityError:
            # retry مرة كمان في حالة race condition نادرة
            for vals in vals_list:
                if vals.get('club_id'):
                    vals['investor_code'] = self._generate_code_for_vals(vals['club_id'])

            return super().create(vals_list)

    # =========================================
    # COPY (Duplicate Safe)
    # =========================================
    def copy(self, default=None):
        default = dict(default or {})

        default['investor_code'] = False
        default['membership_number'] = 'New'

        return super().copy(default)

    # =========================================
    # NO WRITE OVERRIDE ❌
    # =========================================
    # احنا intentionally مش بنعدل في write
    # علشان نحافظ على stability

    # =========================================
    # INTERNAL GENERATOR (Clean + Reusable)
    # =========================================
    def _generate_code_for_vals(self, club_id):
        club = self.env['investment.club'].browse(club_id)

        sequence_code = f'investor.code.{club.id}'

        sequence = self.env['ir.sequence'].sudo().search([
            ('code', '=', sequence_code)
        ], limit=1)

        if not sequence:
            sequence = self.env['ir.sequence'].sudo().create({
                'name': f'Investor Code - {club.name}',
                'code': sequence_code,
                'prefix': f'INVS-{club.name.replace(" ", "")}-',
                'padding': 5,
                'number_increment': 1,
            })

        return sequence.next_by_id()
    _sql_constraints = [
        (
            'unique_investor_code_per_club',
            'unique(investor_code, club_id)',
            'Investor code must be unique per club!'
        ),
    ]