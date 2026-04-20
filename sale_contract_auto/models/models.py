from odoo import models, fields, api
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_count = fields.Integer(string='Contract Count',
                                    compute='_compute_contract_count',
                                    tracking=True)
    contract_template_id = fields.Many2one('contract.template',
                                           string='Contract Template',
                                           tracking=True)
    contract_id = fields.Many2one('sale.contract', string='Contract',
                                  compute='_compute_contract',
                                  store=False, tracking=True)

    contract_title_name = fields.Char(string="Contract Title Name")
    def _compute_contract_count(self):
        for order in self:
            contract = self.env['sale.contract'].search([('sale_order_id', '=',
                                                          order.id)], limit=1)
            order.contract_id = contract

    def _compute_contract(self):
        for order in self:
            contract = self.env['sale.contract'].search([('sale_order_id', '=',
                                                          order.id)], limit=1)
            order.contract_id = contract

    def action_view_contract(self):
        self.ensure_one()
        if self.contract_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Contract',
                'res_model': 'sale.contract',
                'view_mode': 'form',
                'res_id': self.contract_id.id,
                'target': 'current',
            }
        return {'type': 'ir.actions.act_window_close'}

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            if not order.contract_id and order.contract_template_id:
                agreement_text = order.contract_template_id.content or ''
                self.env['sale.contract'].create({
                    'partner_id': order.partner_id.id,
                    'sale_order_id': order.id,
                    'contract_date': fields.Date.today(),
                    'amount_total': order.amount_total,
                    'currency_id': order.currency_id.id,
                    'agreement_terms': agreement_text,
                    'contract_line_ids': [(0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'quantity': line.product_uom_qty,
                        'price_unit': line.price_unit,
                    }) for line in order.order_line if line.product_id]
                })
        return res


class SaleContract(models.Model):
    _name = 'sale.contract'
    _description = 'Customer Sale Contract'
    _inherit = ['mail.thread', 'portal.mixin']

    name = fields.Char(string='Contract Reference', required=True, copy=False, readonly=True, default='New', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', tracking=True)
    contract_date = fields.Date(string='Contract Date', default=fields.Date.context_today, tracking=True)
    amount_total = fields.Monetary(string='Total Amount', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.company.currency_id, tracking=True)
    agreement_terms = fields.Text(string='Agreement Terms', tracking=True)
    contract_line_ids = fields.One2many('sale.contract.line', 'contract_id', string='Contract Lines', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('finished', 'Finished'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    first_party_name = fields.Char(string='First Party', default=lambda self: self.env.company.name, tracking=True)
    second_party_name = fields.Char(string='Second Party', related='partner_id.name', readonly=True)
    first_party_signature = fields.Binary(string='First Party Signature', tracking=True)
    second_party_signature = fields.Binary(string='Second Party Signature', tracking=True)
    first_party_id = fields.Many2one('res.partner', string="First Party")
    second_party_id = fields.Many2one('res.partner', string="Second Party")


    subtotal_total = fields.Monetary(
        string='Subtotal Total',
        compute='_compute_subtotal_total',
        currency_field='currency_id',
        store=True,
        tracking=True
    )

    access_token = fields.Char('Security Token', copy=False, tracking=True)

    @api.depends('contract_line_ids.price_subtotal')
    def _compute_subtotal_total(self):
        for contract in self:
            contract.subtotal_total = sum(contract.contract_line_ids.mapped('price_subtotal'))

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.contract') or 'New'
        return super().create(vals)

    def action_set_active(self):
        for contract in self:
            contract.state = 'active'

    def action_finish(self):
        for contract in self:
            contract.state = 'finished'

    def action_cancel(self):
        for contract in self:
            contract.state = 'cancelled'

    def _compute_access_url(self):
        super(SaleContract, self)._compute_access_url()
        for contract in self:
            contract.access_url = f'/my/contracts/{contract.id}'

    def print_contract_report(self):
        self.ensure_one()
        if self.state == 'cancelled':
            raise UserError("Cannot print a cancelled contract.")
        return self.env.ref('sale_contract_auto.action_print_sale_contract').report_action(self)

    def action_send_contract_link(self):
        for contract in self:
            if not contract.partner_id.email:
                raise UserError(
                    f"لا يمكن إرسال البريد. العميل '{contract.partner_id.name}' ليس لديه عنوان بريد إلكتروني مسجل.")

            template = self.env.ref('sale_contract_auto.email_template_contract_link')
            template.send_mail(contract.id, force_send=True)

        return True

    def get_portal_url(self):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/my/contracts/{self.id}"
#
 #   def write(self, vals):
  #      for contract in self:
   #         if contract.state != ('draft', 'active'):
    #            raise UserError("You can only edit contracts in Draft state.")
     #   return super(SaleContract, self).write(vals)

    def unlink(self):
        for contract in self:
            if contract.state != 'draft':
                raise UserError("You can only delete contracts in Draft state.")
        return super(SaleContract, self).unlink()


class SaleContractLine(models.Model):
    _name = 'sale.contract.line'
    _description = 'Contract Line for Sale Agreement'

    contract_id = fields.Many2one('sale.contract', string='Contract', ondelete='cascade', tracking=True)
    product_id = fields.Many2one('product.product', string='Product', required=True, tracking=True)
    name = fields.Char(string='Description', tracking=True)
    quantity = fields.Float(string='Quantity', default=1.0, tracking=True)
    price_unit = fields.Monetary(string='Unit Price', tracking=True)
    price_subtotal = fields.Monetary(string='Subtotal', compute='_compute_subtotal', store=True, tracking=True)
    currency_id = fields.Many2one('res.currency', related='contract_id.currency_id', readonly=True, tracking=True)

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.price_subtotal = line.quantity * line.price_unit


class ContractTemplate(models.Model):
    _name = 'contract.template'
    _description = 'Contract Terms Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string='Template Name', required=True, tracking=True)
    content = fields.Html(string='Agreement Terms')
