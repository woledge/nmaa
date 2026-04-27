from odoo import models, fields


class ContractClause(models.Model):
    _name = 'contract.clause'
    _description = 'Contract Clause'

    name = fields.Char(
        string='Clause Title', required=True, tracking=True
    )
    clause_type = fields.Selection([
        ('payment', 'Payment Terms'),
        ('warranty', 'Warranty'),
        ('penalty', 'Penalty/Late Fee'),
        ('termination', 'Termination'),
        ('confidentiality', 'Confidentiality'),
        ('liability', 'Liability'),
        ('dispute', 'Dispute Resolution'),
        ('general', 'General'),
        ('custom', 'Custom'),
    ], string='Clause Category', required=True, tracking=True)
    content = fields.Html(
        string='Clause Content', required=True, tracking=True
    )
    active = fields.Boolean(default=True)
    notes = fields.Text(string='Notes')
