# investment_club/models/investment_subscription.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class InvestmentSubscription(models.Model):
    _name = 'investment.subscription'
    _description = 'Investment Subscription'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'customer_membership_number'  # غيرنا من name

    # ===== رقم العضوية للعميل (من Membership) =====
    customer_membership_number = fields.Char(
        string='Customer Membership Number',
        related='membership_id.customer_membership_number',
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
    
    investment_date = fields.Date(
        string='Investment Date',
        default=fields.Date.today,
        required=True
    )
    
    share_count = fields.Integer(string='Number of Shares', default=1, required=True)
    
    share_value = fields.Float(
        string='Share Value',
        related='project_id.share_value',
        readonly=True
    )
    
    amount = fields.Float(
        string='Investment Amount',
        compute='_compute_amount',
        store=True
    )
    
    expected_monthly_return = fields.Float(
        string='Expected Monthly Return',
        compute='_compute_return',
        store=True
    )
    
    # ===== العوائد الفعلية =====
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
        ('paid', 'Paid'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
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

    @api.depends('share_count', 'share_value')
    def _compute_amount(self):
        for sub in self:
            sub.amount = sub.share_count * sub.share_value

    @api.depends('share_count', 'project_id.monthly_return')
    def _compute_return(self):
        for sub in self:
            sub.expected_monthly_return = sub.share_count * (sub.project_id.monthly_return or 0)

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
            sub.last_return_date = max(paid_returns.mapped('date_from')) if paid_returns else False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('investment.subscription') or 'New'
        return super(InvestmentSubscription, self).create(vals_list)

    def action_register_payment(self):
        self.ensure_one()
        
        if not self.payment_journal_id:
            raise UserError(_('Please select payment journal!'))
        
        payment_vals = {
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.partner_id.id,
            'journal_id': self.payment_journal_id.id,
            'amount': self.amount,
            'date': fields.Date.today(),
            'memo': _('Investment %s - %s [%s]') % (self.name, self.project_id.name, self.customer_membership_number),
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
        """فتح شاشة إنشاء عائد جديد"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Return Payment',
            'res_model': 'investment.actual.return',
            'view_mode': 'form',
            'context': {
                'default_subscription_id': self.id,
                'default_expected_amount': self.expected_monthly_return,
                'default_actual_amount': self.expected_monthly_return,
                'default_customer_membership_number': self.customer_membership_number,
            },
            'target': 'current',
        }

    def action_close(self):
        self.write({'state': 'closed'})

    def action_cancel(self):
        if self.payment_id and self.payment_id.state == 'posted':
            self.payment_id.action_cancel()
        self.write({'state': 'cancelled'})

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.customer_membership_number}] {record.project_id.name} ({record.share_count} shares)"
            result.append((record.id, name))
        return result