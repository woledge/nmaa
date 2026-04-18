from odoo import models, api


class InvestmentProject(models.Model):
    _name = 'investment.project'
    _inherit = ['investment.project', 'mail.thread', 'mail.activity.mixin']

    def _get_config(self, key, default=False):
        """Read a config parameter value."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'investment_club.%s' % key, default
        )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        # Auto activate projects if setting is enabled
        if self._get_config('auto_activate_projects', 'False') == 'True':
            for record in records:
                if record.state == 'draft':
                    record.write({'state': 'active'})

        return records
