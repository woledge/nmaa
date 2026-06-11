# investment_club/reports/returns_report.py
from odoo import models, api, fields


class MonthlyReturnsReport(models.AbstractModel):
    _name = 'report.investment_club.monthly_returns'
    _description = 'Monthly Returns Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        investments = self.env['investment.subscription'].search([
            ('state', '=', 'active'),
            ('payment_state', '=', 'paid')
        ])

        by_project = {}
        by_club = {}
        total = 0

        for inv in investments:
            proj_name = inv.project_id.name

            if proj_name not in by_project:
                by_project[proj_name] = {
                    'investors': 0,
                    'shares': 0,
                    'invested': 0,
                    'monthly_return': 0,
                }
            by_project[proj_name]['investors'] += 1
            by_project[proj_name]['shares'] += inv.share_count
            by_project[proj_name]['invested'] += inv.amount

            # ✅ إصلاح: expected_period_return بدل expected_monthly_return (غير موجود)
            by_project[proj_name]['monthly_return'] += inv.expected_period_return

            club_name = inv.club_id.name
            if club_name not in by_club:
                by_club[club_name] = 0

            # ✅ إصلاح نفس الفيلد هنا
            by_club[club_name] += inv.expected_period_return

            total += inv.expected_period_return

        return {
            'date': fields.Date.today(),
            'month': fields.Date.today().strftime('%B %Y'),
            'investments': investments,
            'by_project': by_project,
            'by_club': by_club,
            'total_monthly': total,
            'total_annual': total * 12,
            'count': len(investments),
        }
