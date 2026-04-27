# investment_club/models/investment_project.py
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class InvestmentProject(models.Model):
    _name = 'investment.project'
    _description = 'Investment Project'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Project Name', required=True, tracking=True)
    code = fields.Char(string='Project Code', readonly=True, copy=False)

    club_id = fields.Many2one(
        'investment.club',
        string='Club',
        required=True,
        ondelete='cascade'
    )

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        required=True
    )

    share_value = fields.Float(string='Share Value', required=True)

    # ===== Contract Settings =====
    contract_start_date = fields.Date(
        string='Contract Start Date',
        default=fields.Date.today,
        help='تاريخ بدء التعاقد'
    )

    contract_end_date = fields.Date(
        string='Contract End Date',
        help='تاريخ انتهاء التعاقد'
    )

    max_shares_per_investor = fields.Integer(
        string='Max Shares per Investor',
        default=0,
        help='حد أقصى عدد حصص لكل مستثمر (0 = لا يوجد حد)'
    )

    # ===== Return 1 - One-time Return =====
    return_1_amount = fields.Float(
        string='Return 1 Amount',
        default=0.0,
        help='عائد الاستثمار الأول (مرة واحدة)'
    )

    return_1_grace_months = fields.Integer(
        string='Return 1 Grace Period (Months)',
        default=0,
        help='شهور السكون قبل صرف العائد الأول'
    )

    return_1_date = fields.Date(
        string='Return 1 Payment Date',
        help='تاريخ صرف العائد الأول'
    )

    # ===== Return 2 - Recurring Return =====
    return_2_amount = fields.Float(
        string='Return 2 Amount',
        default=0.0,
        help='مبلغ العائد الثاني (المتكرر)'
    )

    return_2_percentage = fields.Float(
        string='Return 2 Percentage (%)',
        default=0.0,
        help='نسبة العائد الثاني على الاستثمار'
    )

    return_2_partner_share = fields.Char(
        string='Partner Share Ratio',
        help='نسبة المشاركة مثلاً 60:40',
        default=''
    )

    return_2_grace_months = fields.Integer(
        string='Return 2 Grace Period (Months)',
        default=0,
        help='شهور السكون قبل بدء العائد الثاني'
    )

    return_2_period_months = fields.Integer(
        string='Return 2 Period (Months)',
        default=1,
        help='دورية صرف العائد الثاني (كل كم شهر) - 0 = لا يوجد'
    )

    return_2_duration_years = fields.Integer(
        string='Return 2 Duration (Years)',
        default=0,
        help='مدة تكرار صرف العائد الثاني (سنوات) - 0 = لا يوجد'
    )

    return_2_first_date = fields.Date(
        string='Return 2 First Payment Date',
        help='تاريخ أول صرف للعائد الثاني'
    )

    return_2_last_date = fields.Date(
        string='Return 2 Last Payment Date',
        help='تاريخ آخر صرف للعائد الثاني'
    )

    # ===== Legacy fields (kept for compatibility, computed from new fields) =====
    grace_period_months = fields.Integer(
        string='Grace Period (Months)',
        compute='_compute_grace_period',
        store=True,
        help='فترة السكون العامة (تأخذ من العائد الثاني)'
    )

    return_percentage = fields.Float(
        string='Return Percentage (%)',
        compute='_compute_return_percentage',
        store=True,
        help='نسبة العائد (من العائد الثاني)'
    )

    fixed_return_amount = fields.Float(
        string='Fixed Return Amount per Period',
        compute='_compute_fixed_return',
        store=True,
        help='المبلغ الثابت للعائد (من العائد الثاني)'
    )

    capital_return_period = fields.Integer(
        string='Capital Return Period (Months)',
        default=0,
        help='بعد كم شهر يرجع رأس المال كامل'
    )

    # ===== Status =====
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed')
    ], string='Status', default='draft', tracking=True)

    active = fields.Boolean(default=True)

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    description = fields.Text(string='Description')

    # ===== Compute Methods =====
    @api.depends('return_2_grace_months')
    def _compute_grace_period(self):
        for project in self:
            project.grace_period_months = project.return_2_grace_months

    @api.depends('return_2_percentage')
    def _compute_return_percentage(self):
        for project in self:
            project.return_percentage = project.return_2_percentage

    @api.depends('return_2_amount')
    def _compute_fixed_return(self):
        for project in self:
            project.fixed_return_amount = project.return_2_amount

    # ===== Validation =====
    @api.constrains('return_2_period_months')
    def _check_return_2_period(self):
        for project in self:
            if project.return_2_amount > 0 or project.return_2_percentage > 0:
                if project.return_2_period_months <= 0:
                    raise ValidationError(_(
                        'Return 2 Period must be greater than 0 when Return 2 Amount or Percentage is set!'
                    ))

    @api.constrains('return_1_amount', 'return_1_date')
    def _check_return_1(self):
        for project in self:
            if project.return_1_amount > 0 and not project.return_1_date:
                raise ValidationError(_(
                    'Return 1 Payment Date is required when Return 1 Amount is set!'
                ))

    @api.constrains('contract_start_date', 'contract_end_date')
    def _check_contract_dates(self):
        for project in self:
            if project.contract_start_date and project.contract_end_date:
                if project.contract_end_date < project.contract_start_date:
                    raise ValidationError(_(
                        'Contract End Date must be after Contract Start Date!'
                    ))

    # ===== CRUD =====
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('investment.project') or 'New'
        return super(InvestmentProject, self).create(vals_list)

    def action_activate(self):
        self.write({'state': 'active'})

    def action_close(self):
        self.write({'state': 'closed'})