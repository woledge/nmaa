from odoo import models, fields, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    investment_subscription_id = fields.Many2one(
        'investment.subscription',
        string='Investment Subscription',
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
