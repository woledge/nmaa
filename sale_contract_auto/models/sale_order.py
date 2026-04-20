from odoo import models, fields,api
from odoo.exceptions import ValidationError




class ContractTitle(models.Model):
    _name = 'sale.contract.title'
    _rec_name = "name"

    name = fields.Char(string='Contract Title')



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_count = fields.Integer(
        string='Contract Count', compute='_compute_contract_count', tracking=True)
    contract_template_id = fields.Many2one(
        'contract.template', string='Contract Template', tracking=True)
    contract_id = fields.Many2one(
        'sale.contract', string='Contract', compute='_compute_contract', store=False, tracking=True)
    contract_title_name = fields.Many2one( 'sale.contract.title',string="Contract Title Name")

    def _compute_contract_count(self):
        for order in self:
            contract = self.env['sale.contract'].search(
                [('sale_order_id', '=', order.id)], limit=1)
            order.contract_id = contract

    def _compute_contract(self):
        for order in self:
            contract = self.env['sale.contract'].search(
                [('sale_order_id', '=', order.id)], limit=1)
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



class ResPartner(models.Model):
    _inherit = 'res.partner'

    card_id = fields.Char(string='Card ID')


    @api.constrains("card_id")
    def _check_code(self):
        for rec in self:
            if rec.card_id and len(rec.card_id) != 14:
                raise ValidationError("Code must be 14 digits")