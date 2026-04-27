from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    contract_id = fields.Many2one(
        'sale.contract', string='Related Contract',
        tracking=True, copy=False
    )
