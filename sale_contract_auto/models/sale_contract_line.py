from odoo import models, fields, api


class SaleContractLine(models.Model):
    _name = 'sale.contract.line'
    _description = 'Contract Line'

    contract_id = fields.Many2one(
        'sale.contract', string='Contract', ondelete='cascade', tracking=True)
    product_id = fields.Many2one(
        'product.product', string='Product', required=True, tracking=True)
    name = fields.Char(string='Line Description', tracking=True)
    quantity = fields.Float(string='Quantity', default=1.0, tracking=True)
    price_unit = fields.Monetary(string='Unit Price', tracking=True)
    price_subtotal = fields.Monetary(
        string='Line Subtotal', compute='_compute_subtotal', store=True, tracking=True)
    currency_id = fields.Many2one(
        'res.currency', related='contract_id.currency_id', readonly=True, tracking=True)

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.price_subtotal = line.quantity * line.price_unit
