# investment_club/reports/project_profit_report.py
from odoo import models, api, fields


class ProjectProfitReport(models.AbstractModel):
    _name = 'report.investment_club.project_profit'
    _description = 'Project Profit & Loss Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        projects = self.env['investment.project'].browse(docids)
        
        report_data = []
        
        for project in projects:
            # إجمالي الاستثمارات (إيرادات)
            investments = self.env['investment.subscription'].search([
                ('project_id', '=', project.id),
                ('state', '=', 'active')
            ])
            total_revenue = sum(inv.amount for inv in investments)
            
            # العوائد المتوقعة (مصروفات)
            monthly_returns = sum(inv.expected_period_return for inv in investments)
            annual_returns = monthly_returns * 12
            
            # من Analytic Account (لو فيه مصروفات حقيقية)
            analytic_lines = self.env['account.analytic.line'].search([
                ('account_id', '=', project.analytic_account_id.id)
            ])
            actual_expenses = sum(line.amount for line in analytic_lines if line.amount < 0)
            
            report_data.append({
                'name': project.name,
                'code': project.code,
                'investors': len(investments),
                'total_revenue': total_revenue,
                'annual_returns': annual_returns,
                'actual_expenses': abs(actual_expenses),
                'net_profit': total_revenue - annual_returns + actual_expenses,
                'profit_margin': ((total_revenue - annual_returns) / total_revenue * 100) if total_revenue else 0,
            })
        
        return {
            'date': fields.Date.today(),
            'projects': report_data,
        }
