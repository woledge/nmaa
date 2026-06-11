from odoo import models, fields, _


class SaleContract(models.Model):
    _inherit = 'sale.contract'

    investment_subscription_id = fields.Many2one(
        'investment.subscription',
        string='Investment Subscription',
        readonly=True,
        copy=False,
    )

    investment_membership_id = fields.Many2one(
        'investment.membership',
        string='Investment Membership',
        readonly=True,
        copy=False,
    )

    def action_view_investment_subscription(self):
        self.ensure_one()
        if not self.investment_subscription_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Investment'),
            'res_model': 'investment.subscription',
            'res_id': self.investment_subscription_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_investment_membership(self):
        self.ensure_one()
        if not self.investment_membership_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Membership'),
            'res_model': 'investment.membership',
            'res_id': self.investment_membership_id.id,
            'view_mode': 'form',
            'target': 'current',
        }