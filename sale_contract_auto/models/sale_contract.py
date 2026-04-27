from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime


class SaleContract(models.Model):
    _name = 'sale.contract'
    _description = 'Contract'
    _inherit = ['mail.thread', 'portal.mixin']

    name = fields.Char(
        string='Contract Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New',
        tracking=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True
    )

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        tracking=True
    )

    contract_date = fields.Date(
        string='Contract Date',
        default=fields.Date.context_today,
        tracking=True
    )

    amount_total = fields.Monetary(
        string='Total Amount',
        tracking=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        tracking=True
    )

    agreement_terms = fields.Text(
        string='Terms and Conditions',
        tracking=True
    )

    contract_line_ids = fields.One2many(
        'sale.contract.line',
        'contract_id',
        string='Contract Lines',
        tracking=True
    )

    contract_title_name = fields.Many2one(
        'sale.contract.title',
        string='Document Title',
        tracking=True
    )

    contract_template_id = fields.Many2one(
        'contract.template',
        string='Contract Template',
        tracking=True
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('financial_approved', 'Financial Approved'),
        ('legal_approved', 'Legal Approved'),
        ('finished', 'Finished'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True)

    first_party_name = fields.Char(
        string='First Party Name',
        default=lambda self: self.env.company.name
    )

    first_party_registry = fields.Char(
        string='First Party Registry',
        default=lambda self: self.env.company.company_registry
    )

    first_party_address = fields.Char(
        string='First Party Address',
        default=lambda self: " - ".join(filter(None, [
            self.env.company.street,
            self.env.company.street2,
            self.env.company.city,
            self.env.company.state_id.name,
            self.env.company.country_id.name
        ]))
    )

    second_party_name = fields.Char(
        string='Second Party Name',
        related='partner_id.name',
        readonly=True
    )

    second_party_address = fields.Char(
        string='Second Party Address',
        compute='_compute_second_party_address'
    )

    second_party_id_card = fields.Char(
        string='Second Party ID',
        related='partner_id.card_id',
        readonly=True
    )

    first_party_signature = fields.Binary(
        string='First Party Signature'
    )

    second_party_signature = fields.Binary(
        string='Second Party Signature'
    )

    first_party_id = fields.Many2one(
        'res.partner',
        string="First Party Contact"
    )

    second_party_id = fields.Many2one(
        'res.partner',
        string="Second Party Contact"
    )

    subtotal_total = fields.Monetary(
        string='Contract Subtotal',
        compute='_compute_subtotal_total',
        currency_field='currency_id',
        store=True,
    )

    company_representative = fields.Char(string='Authorized Signatory')

    access_token = fields.Char(
        'Security Token',
        copy=False
    )
    note = fields.Text(string='Internal Notes')

    # -------------------------
    # ONCHANGE TEMPLATE
    # -------------------------
    @api.onchange('contract_template_id')
    def _onchange_contract_template(self):
        if self.contract_template_id:
            self.agreement_terms = self.contract_template_id.content

    # -------------------------
    # COMPUTE TOTAL
    # -------------------------
    @api.depends('contract_line_ids.price_subtotal')
    def _compute_subtotal_total(self):
        for contract in self:
            contract.subtotal_total = sum(
                contract.contract_line_ids.mapped('price_subtotal')
            )

    # -------------------------
    # CREATE
    # -------------------------
    @api.model
    def create(self, vals):

        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'sale.contract') or 'New'

        # إضافة نص التمبلت تلقائي
        if vals.get('contract_template_id') and not vals.get('agreement_terms'):
            template = self.env['contract.template'].browse(
                vals['contract_template_id'])
            vals['agreement_terms'] = template.content

        return super().create(vals)

    # -------------------------
    # WRITE
    # -------------------------
    def write(self, vals):

        if vals.get('contract_template_id'):
            template = self.env['contract.template'].browse(
                vals['contract_template_id'])
            vals['agreement_terms'] = template.content

        return super(SaleContract, self).write(vals)

    # -------------------------
    # STATE ACTIONS
    # -------------------------
    def action_set_active(self):
        """Set contract to Active"""
        for contract in self:
            contract.state = 'confirmed'

    def action_financial_approve(self):
        """Financial accountant approves"""
        for contract in self:
            contract.state = 'financial_approved'

    def action_legal_approve(self):
        """Legal accountant approves"""
        for contract in self:
            contract.state = 'legal_approved'

    def action_finish(self):
        """Finish contract"""
        for contract in self:
            contract.state = 'finished'

    def action_cancel(self):
        """Cancel contract"""
        for contract in self:
            contract.state = 'cancelled'

    def action_reset_to_draft(self):
        """Reset contract to draft"""
        for contract in self:
            contract.state = 'draft'

    # -------------------------
    # PORTAL URL
    # -------------------------
    def _compute_access_url(self):
        super(SaleContract, self)._compute_access_url()
        for contract in self:
            contract.access_url = f'/my/contracts/{contract.id}'

    def get_portal_url(self):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/my/contracts/{self.id}"

    # -------------------------
    # REPORT
    # -------------------------
    def print_contract_report(self):
        self.ensure_one()
        if self.state == 'cancelled':
            raise UserError("Cannot print a cancelled contract.")
        return self.env.ref(
            'sale_contract_auto.action_print_sale_contract'
        ).report_action(self)

    # -------------------------
    # EMAIL
    # -------------------------
    def action_send_contract_link(self):
        for contract in self:

            if not contract.partner_id.email:
                raise UserError(
                    f"لا يمكن إرسال البريد. العميل '{contract.partner_id.name}' ليس لديه بريد إلكتروني."
                )

            template = self.env.ref(
                'sale_contract_auto.email_template_contract_link'
            )

            template.send_mail(contract.id, force_send=True)

        return True

    # -------------------------
    # ADDRESS COMPUTE
    # -------------------------
    @api.depends('partner_id')
    def _compute_second_party_address(self):
        for rec in self:
            p = rec.partner_id
            if p:
                address_parts = [
                    p.street,
                    p.street2,
                    p.city,
                    p.state_id.name,
                    p.country_id.name
                ]
                rec.second_party_address = " - ".join(
                    filter(None, address_parts)
                )
            else:
                rec.second_party_address = ""

    # -------------------------
    # ARABIC DATE
    # -------------------------
    def get_arabic_date(self):

        days = {
            'Sunday': 'الاحد',
            'Monday': 'الاثنين',
            'Tuesday': 'الثلاثاء',
            'Wednesday': 'الاربعاء',
            'Thursday': 'الخميس',
            'Friday': 'الجمعة',
            'Saturday': 'السبت'
        }

        d = self.contract_date
        day = days[d.strftime('%A')]

        return f"انه فى يوم {day} الموافق {d.strftime('%d-%m-%Y')}"

    # -------------------------
    # DELETE RULE
    # -------------------------
    def unlink(self):
        for contract in self:
            if contract.state != 'draft':
                raise UserError(
                    "You can only delete contracts in Draft state."
                )
        return super(SaleContract, self).unlink()
