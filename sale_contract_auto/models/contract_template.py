from odoo import models, fields


class ContractTemplate(models.Model):
    _name = 'contract.template'
    _description = 'Contract Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Template Name', required=True, tracking=True)
    content = fields.Html(string='Template Content')
