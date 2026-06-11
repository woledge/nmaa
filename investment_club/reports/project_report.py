# investment_club/reports/project_report.py
from odoo import models, api, fields


class ProjectSummaryReport(models.AbstractModel):
    _name = 'report.investment_club.project_summary'
    _description = 'Project Summary Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        projects = self.env['investment.project'].browse(docids)

        report_data = []
        grand_total = {
            'invested': 0,
            'investors': 0,
            'monthly_return': 0,
            'annual_return': 0,
        }

        for project in projects:
            investments = self.env['investment.subscription'].search([
                ('project_id', '=', project.id),
                ('state', '=', 'active')
            ])

            total_invested = sum(inv.amount for inv in investments)
            investor_count = len(investments)

            # ✅ إصلاح: استبدال expected_monthly_return (غير موجود)
            # بـ expected_period_return (الفيلد الفعلي في الموديل)
            period_return = sum(inv.expected_period_return for inv in investments)

            # ✅ إصلاح: حذف investors_per_branch و expected_customers_min/max
            # (فيلدات غير موجودة في investment.project)
            report_data.append({
                'name': project.name,
                'code': project.code,
                'club': project.club_id.name,
                'analytic_account': project.analytic_account_id.name,
                'share_value': project.share_value,
                'return_type': dict(project._fields['return_calculation_type'].selection).get(
                    project.return_calculation_type, project.return_calculation_type
                ),
                'actual_investors': investor_count,
                'total_invested': total_invested,
                'period_return': period_return,
                'annual_return': period_return * 12,
                'roi': (period_return * 12 / total_invested * 100) if total_invested else 0,
            })

            grand_total['invested'] += total_invested
            grand_total['investors'] += investor_count
            grand_total['monthly_return'] += period_return
            grand_total['annual_return'] += period_return * 12

        return {
            'docs': projects,
            'data': report_data,
            'grand_total': grand_total,
            'date': fields.Date.today(),
        }
