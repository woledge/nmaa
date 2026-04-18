from odoo import models, fields, api, _


class InvestmentActualReturn(models.Model):
    _name = 'investment.actual.return'
    _inherit = 'investment.actual.return'
    _description = 'Investment Actual Return (with notifications)'

    def _get_config(self, key, default=False):
        """Read a config parameter value."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'investment_club.%s' % key, default
        )

    def _cron_send_payment_notifications(self):
        """Send payment notifications for recently paid returns.

        Reads from settings:
        - investment_club.enable_payment_notifications
        """
        # Check if notifications are enabled
        if not self._get_config('enable_payment_notifications', 'True') == 'True':
            return

        # Find returns that were paid today
        today = fields.Date.today()
        paid_returns = self.search([
            ('state', '=', 'paid'),
            ('write_date', '>=', (fields.Datetime.now()).replace(hour=0, minute=0, second=0)),
        ])

        for ret in paid_returns:
            self._send_payment_notification(ret)

    def _send_payment_notification(self, ret):
        """Send a payment notification via chatter/message system."""
        subscription = ret.subscription_id
        if not subscription or not subscription.partner_id:
            return

        subject = _('Return Payment: %s') % (ret.period_name or ret.date_from)
        body = _(
            '<p>Dear <b>%s</b>,</p>'
            '<p>A return payment has been processed for your investment.</p>'
            '<ul>'
            '<li>Project: <b>%s</b></li>'
            '<li>Period: <b>%s</b></li>'
            '<li>Amount: <b>%s %s</b></li>'
            '</ul>'
        ) % (
            subscription.partner_id.name or '',
            subscription.project_id.name or '',
            ret.period_name or '%s - %s' % (ret.date_from, ret.date_to),
            subscription.currency_id.symbol or '',
            ret.actual_amount,
        )
        ret.message_post(
            subject=subject,
            body=body,
            partner_ids=[subscription.partner_id.id],
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )

    def action_process_return_payment(self):
        """Process the return payment - mark as paid and send notification."""
        self.ensure_one()
        self.write({'state': 'paid'})

        # Send notification if enabled
        if self._get_config('enable_payment_notifications', 'True') == 'True':
            self._send_payment_notification(self)
