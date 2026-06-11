# investment_club/reports/investor_report.py
from odoo import models, api, fields


class InvestorSummaryReport(models.AbstractModel):
    _name = 'report.investment_club.investor_summary'
    _description = 'Investor Summary Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        # كل الأعضاء النشطاء
        memberships = self.env['investment.membership'].search([
            ('state', '=', 'active')
        ])
        
        report_data = []
        total_membership = 0
        total_investment = 0
        
        for mem in memberships:
            # استثمارات العضو
            investments = mem.investment_ids.filtered(lambda i: i.state == 'active')
            
            # ✅ إصلاح: expected_period_return هو الفيلد الصحيح الموجود في الموديل
            period_return = sum(inv.expected_period_return for inv in investments)

            report_data.append({
                'membership': mem.membership_number,
                'partner': mem.partner_id.name,
                'phone': mem.partner_id.phone or '',
                'club': mem.club_id.name,
                'expiry_date': mem.expiry_date,
                'membership_fee': mem.annual_subscription_fee,
                'investment_count': len(investments),
                'total_invested': sum(inv.amount for inv in investments),
                'monthly_return': period_return,
            })
            
            total_membership += mem.annual_subscription_fee
            total_investment += sum(inv.amount for inv in investments)
        
        return {
            'date': fields.Date.today(),
            'investors': report_data,
            'total_membership': total_membership,
            'total_investment': total_investment,
            'count': len(memberships),
        }