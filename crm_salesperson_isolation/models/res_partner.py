# -*- coding: utf-8 -*-
# CRM Salesperson Data Isolation — Res Partner Model

from odoo import api, models, _
from odoo.exceptions import AccessError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ----------------------------------------------------------
    # Record Rule: Search Isolation
    # ----------------------------------------------------------

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, **kwargs):
        """
        Override _search to restrict salespersons to their own contacts only.

        A salesperson can see a contact ONLY if:
        - They are assigned as the Salesperson (user_id), OR
        - They created the contact (create_uid), OR
        - The contact is linked to one of their CRM leads

        Managers and Administrators bypass this restriction entirely.
        """
        if self._should_apply_isolation():
            # Build isolation domain: my contacts + contacts from my leads
            isolation_domain = [
                '|',
                ('user_id', '=', self.env.uid),
                ('create_uid', '=', self.env.uid),
            ]

            # Also include partners linked to current user's leads
            lead_partner_ids = self._get_lead_partner_ids()
            if lead_partner_ids:
                isolation_domain = [
                    '|',
                ] + isolation_domain + [
                    ('id', 'in', lead_partner_ids),
                ]

            # Combine: isolation AND whatever the caller requested
            domain = ['&'] + isolation_domain + domain if domain else isolation_domain

        return super()._search(
            domain, offset=offset, limit=limit, order=order, **kwargs
        )

    # ----------------------------------------------------------
    # Record Rule: Direct Access Protection
    # ----------------------------------------------------------

    def check_access_rule(self, operation):
        """
        Override check_access_rule to prevent direct record access by ID
        (write / unlink).  Read access is already governed by _search above.
        """
        if self._should_apply_isolation():
            for record in self.sudo():
                if not self._partner_belongs_to_user(record):
                    raise AccessError(
                        _("You are not allowed to access this contact. "
                          "It belongs to another salesperson.")
                    )

        return super().check_access_rule(operation)

    # ----------------------------------------------------------
    # Helper: Safe check — only apply isolation in normal use
    # ----------------------------------------------------------

    @api.model
    def _should_apply_isolation(self):
        """
        Returns True ONLY during normal user operations.
        Returns False during:
        - Module installation/update (install_mode, su=True)
        - Cron jobs and automated processes
        - When no proper user session exists
        """
        # Never apply during module install/update or SUPERUSER access
        if self.env.su or self.env.uid <= 2:
            return False

        # Never apply during module loading
        if self._context.get('install_mode'):
            return False

        # Only apply for regular salespersons (not managers/admins)
        is_salesperson = self.env.user.has_group('sales_team.group_sale_salesman')
        is_manager = self.env.user.has_group('sales_team.group_sale_salesman_all_leads')
        return is_salesperson and not is_manager

    # ----------------------------------------------------------
    # Helper: Check if a partner belongs to the current user
    # ----------------------------------------------------------

    def _partner_belongs_to_user(self, partner):
        """
        Check if a partner belongs to the current salesperson.
        """
        if partner.user_id.id == self.env.uid:
            return True
        if partner.create_uid.id == self.env.uid:
            return True

        # Check if partner is linked to any of the user's leads
        lead_count = self.env['crm.lead'].sudo().search_count([
            '|',
            ('user_id', '=', self.env.uid),
            ('create_uid', '=', self.env.uid),
            ('partner_id', '=', partner.id),
        ])
        return lead_count > 0

    # ----------------------------------------------------------
    # Helper: Get partner IDs from current user's leads
    # ----------------------------------------------------------

    @api.model
    def _get_lead_partner_ids(self):
        """
        Get partner IDs that are linked to the current user's CRM leads.
        Uses sudo() to bypass isolation rules when querying leads.
        """
        try:
            leads = self.env['crm.lead'].sudo().search([
                '|',
                ('user_id', '=', self.env.uid),
                ('create_uid', '=', self.env.uid),
                ('partner_id', '!=', False),
            ])
            return leads.mapped('partner_id.id')
        except Exception:
            # If crm.lead is not available (module not loaded yet), return empty
            return []
