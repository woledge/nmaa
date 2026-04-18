from odoo import models, fields, api, _
from odoo.exceptions import UserError


class InvestmentSubscriptionRejectWizard(models.TransientModel):
    _name = 'investment.subscription.reject.wizard'
    _description = 'Reject Investment Wizard'

    subscription_id = fields.Many2one(
        'investment.subscription',
        string='Investment',
        required=True
    )

    rejection_reason = fields.Text(
        string='Rejection Reason',
        required=True
    )

    def action_confirm_rejection(self):
        self.ensure_one()
        if not self.rejection_reason:
            raise UserError(_('Please provide a rejection reason!'))

        subscription = self.subscription_id
        subscription.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason,
        })
        subscription.message_post(
            body=_('Investment rejected by %s.\nReason: %s') % (
                self.env.user.name, self.rejection_reason
            ),
            partner_ids=[],
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )
