# investment_club/models/crm_lead.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # ===== فيلد اختيار المشروع (Dropdown) =====
    interested_project_id = fields.Many2one(
        'investment.project',
        string='Interested Project',
        domain="[('state', '=', 'active')]",
        help='المشروع الاستثماري اللي العميل مهتم بيه'
    )
    
    # ===== النادي (يظهر تلقائياً من المشروع) =====
    club_id = fields.Many2one(
        'investment.club',
        related='interested_project_id.club_id',
        string='Club',
        readonly=True,
        store=True
    )

    def action_create_membership(self):
        """فتح شاشة إنشاء عضوية للعميل"""
        self.ensure_one()
        
        # التحقق من وجود عميل
        if not self.partner_id:
            raise UserError(_('Please select a customer first!'))
        
        # التحقق من وجود مشروع
        if not self.interested_project_id:
            raise UserError(_('Please select an interested project first!'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Membership',
            'res_model': 'investment.membership',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_club_id': self.club_id.id if self.club_id else False,
            },
        }

    def action_view_investment_projects(self):
        """عرض كل المشاريع الاستثمارية"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Investment Projects',
            'res_model': 'investment.project',
            'view_mode': 'list,form',
            'domain': [('state', '=', 'active')],
            'target': 'new',
        }