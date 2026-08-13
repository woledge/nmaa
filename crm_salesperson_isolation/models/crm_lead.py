# -*- coding: utf-8 -*-
# CRM Salesperson Data Isolation — CRM Lead Model

from odoo import api, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # ----------------------------------------------------------
    # Auto-Sync: Lead user_id / partner_id → Contact user_id
    # ----------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        """On create, sync salesperson to the linked contact."""
        leads = super().create(vals_list)
        if not self._context.get('install_mode') and not self.env.su:
            leads._sync_user_id_to_partner()
        return leads

    def write(self, vals):
        """On write, sync salesperson changes to linked contacts.
        Also handles partner_id changes (e.g. linking an existing contact).
        """
        result = super().write(vals)
        if ('user_id' in vals or 'partner_id' in vals) and not self.env.su:
            self._sync_user_id_to_partner()
        return result

    def _sync_user_id_to_partner(self):
        """Propagate lead's salesperson to the linked partner."""
        for lead in self:
            if lead.partner_id:
                try:
                    lead.partner_id.sudo().write({
                        'user_id': lead.user_id.id if lead.user_id else False
                    })
                except Exception:
                    # Silently ignore if we lack rights on the partner
                    pass

    def action_set_won(self):
        """Ensure partner sync when lead is marked as won."""
        result = super().action_set_won()
        self._sync_user_id_to_partner()
        return result
