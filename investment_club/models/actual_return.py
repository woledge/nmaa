# investment_club/models/actual_return.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class InvestmentActualReturn(models.Model):
    _name = 'investment.actual.return'
    _description = 'Actual Return Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_from desc'

    # ===== رقم العضوية للعميل (من Subscription) =====
    customer_membership_number = fields.Char(
        string='Customer Membership Number',
        related='subscription_id.customer_membership_number',
        store=True,
        readonly=True,
        index=True
    )
    
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
    
    # الفترة
    period_name = fields.Char(
        string='Period',
        required=True,
        help='مثال: يناير 2026 أو الربع الأول 2026'
    )
    
    date_from = fields.Date(string='From Date', required=True)
    date_to = fields.Date(string='To Date', required=True)
    
    # المبالغ
    expected_amount = fields.Float(
        string='Expected Amount',
        related='subscription_id.expected_monthly_return',
        readonly=True
    )
    
    actual_amount = fields.Float(
        string='Actual Amount',
        required=True,
        help='المبلغ الفعلي المدفوع للعميل'
    )
    
    difference = fields.Float(
        string='Difference',
        compute='_compute_difference',
        store=True
    )
    
    # الدفع
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

    @api.depends('expected_amount', 'actual_amount')
    def _compute_difference(self):
        for rec in self:
            rec.difference = rec.actual_amount - rec.expected_amount

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('investment.actual.return') or 'New'
        return super(InvestmentActualReturn, self).create(vals_list)

    def action_register_payment(self):
        """تسجيل دفع العائد للعميل"""
        self.ensure_one()
        
        if not self.payment_journal_id:
            raise UserError(_('Please select payment journal!'))
        
        payment_vals = {
            'payment_type': 'outbound',
            'partner_type': 'customer',
            'partner_id': self.partner_id.id,
            'journal_id': self.payment_journal_id.id,
            'amount': self.actual_amount,
            'date': fields.Date.today(),
            'memo': _('Return Payment - %s - %s [%s]') % (self.period_name, self.subscription_id.name, self.customer_membership_number),
        }
        
        payment = self.env['account.payment'].create(payment_vals)
        payment.action_post()
        
        self.write({
            'payment_id': payment.id,
            'state': 'paid'
        })

    def action_cancel(self):
        """إلغاء العائد"""
        if self.payment_id and self.payment_id.state == 'posted':
            self.payment_id.action_cancel()
        self.write({'state': 'cancelled'})

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.customer_membership_number}] {record.period_name} - {record.actual_amount}"
            result.append((record.id, name))
        return result