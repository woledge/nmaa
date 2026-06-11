# investment_club/models/investment_club.py
from odoo import models, fields, api


class InvestmentClub(models.Model):
    _name = 'investment.club'
    _description = 'Investment Club'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Club Name', required=True, tracking=True)
    code = fields.Char(string='Club Code', readonly=True, copy=False)
    
    # بس active ولا لأ
    active = fields.Boolean(default=True)
    
    # المشاريع المرتبطة
    project_ids = fields.One2many(
        'investment.project', 
        'club_id', 
        string='Projects'
    )
    
    member_ids = fields.One2many(
        'investment.membership', 
        'club_id', 
        string='Members'
    )
    
    active_members_count = fields.Integer(
        string='Active Members',
        compute='_compute_counts',
        store=True
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    
    notes = fields.Text(string='Notes')

    @api.depends('member_ids.state')
    def _compute_counts(self):
        for club in self:
            club.active_members_count = len(club.member_ids.filtered(lambda m: m.state == 'active'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('investment.club') or 'New'
        return super(InvestmentClub, self).create(vals_list)