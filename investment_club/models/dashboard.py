from odoo import models, fields, api


class InvestmentDashboard(models.TransientModel):
    _name = 'investment.dashboard'
    _description = 'Investment Dashboard'

    total_clubs = fields.Integer(string='Total Active Clubs')
    total_projects = fields.Integer(string='Active Projects')
    total_memberships = fields.Integer(string='Total Memberships')
    active_memberships = fields.Integer(string='Active Memberships')
    terminated_memberships = fields.Integer(string='Terminated')
    expired_memberships = fields.Integer(string='Expired')
    total_subscriptions = fields.Integer(string='Total Investments')
    active_subscriptions = fields.Integer(string='Active')
    terminated_subscriptions = fields.Integer(string='Terminated')
    total_returns = fields.Integer(string='Total Returns')
    paid_returns = fields.Integer(string='Paid')
    due_returns = fields.Integer(string='Due')
    total_invested = fields.Float(string='Total Invested Amount')
    overdue_renewals = fields.Integer(string='Overdue Renewals')

    @api.model
    def create(self, vals):
        vals = self._compute_stats_vals(vals)
        return super().create(vals)

    def write(self, vals):
        vals = self._compute_stats_vals(vals)
        return super().write(vals)

    def _compute_stats_vals(self, vals):
        Membership = self.env['investment.membership']
        Subscription = self.env['investment.subscription']
        Return = self.env['investment.actual.return']
        Club = self.env['investment.club']
        Project = self.env['investment.project']

        vals['total_clubs'] = Club.search_count([('active', '=', True)])
        vals['total_projects'] = Project.search_count([('state', '!=', 'closed')])
        vals['total_memberships'] = Membership.search_count([])
        vals['active_memberships'] = Membership.search_count([('state', '=', 'active')])
        vals['terminated_memberships'] = Membership.search_count([('state', '=', 'terminated')])
        vals['expired_memberships'] = Membership.search_count([('state', '=', 'expired')])
        vals['total_subscriptions'] = Subscription.search_count([])
        vals['active_subscriptions'] = Subscription.search_count([('state', '=', 'active')])
        vals['terminated_subscriptions'] = Subscription.search_count([('state', '=', 'terminated')])
        vals['total_returns'] = Return.search_count([])
        vals['paid_returns'] = Return.search_count([('state', '=', 'paid')])
        vals['due_returns'] = Return.search_count([('state', '=', 'draft')])
        vals['total_invested'] = sum(Subscription.search([('state', 'in', ('paid', 'active'))]).mapped('amount'))
        vals['overdue_renewals'] = Membership.search_count([('renewal_status', 'in', ('due', 'overdue')), ('state', '=', 'active')])

        return vals

    def action_refresh(self):
        self.write(self._compute_stats_vals({}))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'investment.dashboard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'main',
        }
