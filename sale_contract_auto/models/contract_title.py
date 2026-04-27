from odoo import models, fields


class ContractTitle(models.Model):
    _name = 'sale.contract.title'
    _description = 'Contract Document Title'
    _rec_name = "name"

    name = fields.Char(string='Document Title', required=True, tracking=True)
