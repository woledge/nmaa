# investment_club/models/actual_return.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class InvestmentActualReturn(models.Model):
    _name = 'investment.actual.return'
    _description = 'Actual Return Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_from desc'


    
    name = fields.Char(
        string='Reference',
        readonly=True,
        copy=False,
        default='New'
    )
    
    subscription_id = fields.Many2one(
        'investment.subscription',
        string='Investment',
        required=True,
        ondelete='cascade'
    )
    
    membership_id = fields.Many2one(
        'investment.membership',
        related='subscription_id.membership_id',
        string='Membership',
        store=True,
        readonly=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        related='subscription_id.partner_id',
        string='Investor',
        store=True,
        readonly=True
    )
    
    project_id = fields.Many2one(
        'investment.project',
        related='subscription_id.project_id',
        string='Project',
        store=True,
        readonly=True
    )
    
    period_name = fields.Char(
        string='Period',
        compute='_compute_period_name',
        store=True
    )
    
    date_from = fields.Date(string='From Date', required=True)
    date_to = fields.Date(string='To Date', required=True)
    
    expected_amount = fields.Float(
        string='Expected Amount',
        compute='_compute_expected_amount',
        store=True,
        readonly=True
    )
    
    actual_amount = fields.Float(
        string='Actual Amount',
        required=True,
        help='المبلغ الفعلي المدفوع للعميل',
        default=0.0
    )
    
    difference = fields.Float(
        string='Difference',
        compute='_compute_difference',
        store=True
    )
    
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
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    notes = fields.Text(string='Notes')
    
    company_id = fields.Many2one(
        'res.company',
        related='subscription_id.company_id',
        store=True
    )


    @api.depends('subscription_id', 'date_from', 'date_to')
    def _compute_expected_amount(self):
        for rec in self:
            if not rec.subscription_id:
                rec.expected_amount = 0.0
                continue
            
            sub = rec.subscription_id
            
            if sub.fixed_return_amount > 0:
                rec.expected_amount = sub.fixed_return_amount
            else:
                rec.expected_amount = sub.expected_period_return or 0.0

    @api.depends('expected_amount', 'actual_amount')
    def _compute_difference(self):
        for rec in self:
            rec.difference = rec.actual_amount - rec.expected_amount

    @api.onchange('subscription_id')
    def _onchange_subscription(self):
        if not self.subscription_id:
            return
        
        sub = self.subscription_id
        today = fields.Date.today()
        
        # ===== التحقق من فترة السكون =====
        if not sub.grace_period_passed:
            # حساب الوقت المتبقي بالشهور والأيام
            diff = relativedelta(sub.returns_start_date, today)
            months_remaining = diff.months + (diff.years * 12)
            days_remaining = (sub.returns_start_date - today).days  # إجمالي الأيام
            
            # ⚠️ التصحيح: عرض الشهور والأيام الإجمالية بين قوسين
            raise UserError(_(
                '⛔ لا يمكن إنشاء دفع عائد الآن!\n\n'
                'فترة السكون: %s شهور\n'
                'تاريخ الاستثمار: %s\n'
                'تاريخ بدء العوائد: %s\n\n'
                'الوقت المتبقي: %s شهر (%s يوم)\n\n'
                'يمكنك إنشاء دفع العائد بعد: %s'
            ) % (
                sub.grace_period_months or 0,
                sub.investment_date,
                sub.returns_start_date,
                months_remaining,
                days_remaining,  # ⚠️ إجمالي الأيام مش الأيام الزيادة
                sub.returns_start_date.strftime('%Y-%m-%d') if sub.returns_start_date else 'N/A'
            ))
        
        # ===== حساب تاريخ العائد القادم =====
        if sub.actual_return_ids:
            last_return = sub.actual_return_ids.sorted('date_to', reverse=True)[0]
            next_date_from = last_return.date_to + timedelta(days=1)
        else:
            next_date_from = sub.returns_start_date
        
        if not next_date_from:
            raise UserError(_('خطأ: تاريخ بدء العوائد غير محدد!'))
        
        if next_date_from > today:
            raise UserError(_(
                '⏳ تاريخ العائد القادم (%s) في المستقبل!'
            ) % next_date_from.strftime('%Y-%m-%d'))
        
        # ===== تعبئة التواريخ تلقائياً =====
        self.date_from = next_date_from
        self.date_to = next_date_from + relativedelta(months=1, days=-1)
        
        # ===== تعبئة المبلغ المتوقع =====
        if sub.fixed_return_amount > 0:
            self.expected_amount = sub.fixed_return_amount
            self.actual_amount = sub.fixed_return_amount
        else:
            self.expected_amount = sub.expected_period_return or 0.0
            self.actual_amount = sub.expected_period_return or 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('investment.actual.return') or 'New'
        return super(InvestmentActualReturn, self).create(vals_list)

    def action_register_payment(self):
        self.ensure_one()
        
        if not self.payment_journal_id:
            raise UserError(_('Please select payment journal!'))
        
        if self.actual_amount <= 0:
            raise UserError(_('Actual amount must be greater than zero!'))
        
        payment_vals = {
            'payment_type': 'outbound',
            'partner_type': 'customer',
            'partner_id': self.partner_id.id,
            'journal_id': self.payment_journal_id.id,
            'amount': self.actual_amount,
            'date': fields.Date.today(),
            'memo': _('Return Payment - %s - %s [%s]') % (self.period_name, self.subscription_id.name),
        }
        
        payment = self.env['account.payment'].create(payment_vals)
        payment.action_post()
        
        self.write({
            'payment_id': payment.id,
            'state': 'paid'
        })

    def action_cancel(self):
        if self.payment_id and self.payment_id.state == 'posted':
            self.payment_id.action_cancel()
        self.write({'state': 'cancelled'})

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.period_name} - {record.actual_amount:,.2f}"
            result.append((record.id, name))
        return result