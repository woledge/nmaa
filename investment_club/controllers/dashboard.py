from odoo import http
from odoo.http import request
from datetime import datetime


class InvestmentDashboardController(http.Controller):

    @http.route('/investment/dashboard/stats', type='json', auth='user')
    def dashboard_stats(self):
        Membership = request.env['investment.membership']
        Subscription = request.env['investment.subscription']
        Return = request.env['investment.actual.return']
        Club = request.env['investment.club']
        Project = request.env['investment.project']
        Partner = request.env['res.partner']
        currency = request.env.company.currency_id

        # Core stats
        total_clubs = Club.search_count([('active', '=', True)])
        total_memberships = Membership.search_count([])
        active_memberships = Membership.search_count([('state', '=', 'active')])
        terminated_memberships = Membership.search_count([('state', '=', 'terminated')])
        expired_memberships = Membership.search_count([('state', '=', 'expired')])
        total_subscriptions = Subscription.search_count([])
        active_subscriptions = Subscription.search_count([('state', '=', 'active')])
        terminated_subscriptions = Subscription.search_count([('state', '=', 'terminated')])
        total_returns = Return.search_count([])
        paid_returns = Return.search_count([('state', '=', 'paid')])
        due_returns = Return.search_count([('state', '=', 'draft')])

        # Financial
        total_invested = sum(Subscription.search([('state', 'in', ('paid', 'active'))]).mapped('amount'))
        paid_returns_ids = Return.search([('state', '=', 'paid')])
        total_paid_amount = sum(paid_returns_ids.mapped('actual_amount'))
        due_return_ids = Return.search([('state', '=', 'draft')])
        total_due_amount = sum(due_return_ids.mapped('expected_amount'))

        # People & partners
        membership_partners = Membership.search([]).mapped('partner_id')
        subscription_partners = Subscription.search([]).mapped('partner_id')
        all_partners = set(membership_partners.ids + subscription_partners.ids)
        total_partners = len(all_partners)

        # Projects by state
        project_states = {
            'draft': Project.search_count([('state', '=', 'draft')]),
            'active': Project.search_count([('state', '=', 'active')]),
            'closed': Project.search_count([('state', '=', 'closed')]),
        }

        # Renewals forecast (this month)
        now = datetime.now()
        first_of_month = now.replace(day=1)
        if now.month == 12:
            first_of_next = now.replace(year=now.year + 1, month=1, day=1)
        else:
            first_of_next = now.replace(month=now.month + 1, day=1)
        renewals_this_month = Membership.search_count([
            ('next_renewal_date', '>=', first_of_month.strftime('%Y-%m-%d')),
            ('next_renewal_date', '<', first_of_next.strftime('%Y-%m-%d')),
            ('state', '=', 'active'),
        ])

        # Overdue renewals
        overdue_renewals = Membership.search_count([
            ('renewal_status', 'in', ('due', 'overdue')),
            ('state', '=', 'active'),
        ])

        # Recent memberships (last 5)
        recent_memberships = Membership.search([], order='create_date desc', limit=5)
        recent_membership_data = []
        for m in recent_memberships:
            recent_membership_data.append({
                'id': m.id,
                'name': m.membership_number or m.display_name,
                'partner': m.partner_id.display_name or m.partner_id.name or '',
                'state': m.state,
                'date': m.membership_date.strftime('%Y-%m-%d') if m.membership_date else '',
            })

        # Recent subscriptions (last 5)
        recent_subscriptions = Subscription.search([], order='create_date desc', limit=5)
        recent_subscription_data = []
        for s in recent_subscriptions:
            recent_subscription_data.append({
                'id': s.id,
                'name': s.name or s.display_name,
                'partner': s.partner_id.display_name or s.partner_id.name or '',
                'state': s.state,
                'amount': s.amount,
                'date': s.investment_date.strftime('%Y-%m-%d') if s.investment_date else '',
            })

        # Top projects by invested amount
        project_agg = request.env['investment.subscription'].read_group(
            [('state', 'in', ('paid', 'active'))],
            ['project_id', 'amount:sum'],
            ['project_id']
        )
        project_agg = sorted(project_agg, key=lambda x: x['amount'], reverse=True)[:5]
        top_projects = []
        for p in project_agg:
            if p['project_id']:
                project = request.env['investment.project'].browse(p['project_id'][0])
                top_projects.append({
                    'id': project.id,
                    'name': project.display_name,
                    'total_amount': p['amount'],
                })

        return {
            # Core
            'total_clubs': total_clubs,
            'total_projects': Project.search_count([('state', '!=', 'closed')]),
            'total_memberships': total_memberships,
            'active_memberships': active_memberships,
            'terminated_memberships': terminated_memberships,
            'expired_memberships': expired_memberships,
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'terminated_subscriptions': terminated_subscriptions,
            'total_returns': total_returns,
            'paid_returns': paid_returns,
            'due_returns': due_returns,
            'total_invested': total_invested,
            'overdue_renewals': overdue_renewals,
            # New financial
            'total_paid_amount': total_paid_amount,
            'total_due_amount': total_due_amount,
            # People
            'total_partners': total_partners,
            # Projects
            'project_states': project_states,
            # Renewals
            'renewals_this_month': renewals_this_month,
            # Recent records
            'recent_memberships': recent_membership_data,
            'recent_subscriptions': recent_subscription_data,
            # Top projects
            'top_projects': top_projects,
            # Currency
            'currency_symbol': currency.symbol if currency else '$',
            'currency_position': currency.position if currency else 'after',
        }
