from odoo import models, fields, api


class ContractDocument(models.Model):
    _name = 'contract.document'
    _description = 'Contract Supporting Document'

    contract_id = fields.Many2one(
        'sale.contract', string='Contract',
        ondelete='cascade', tracking=True
    )
    name = fields.Char(
        string='Document Name', required=True, tracking=True
    )
    required = fields.Boolean(
        string='Required', default=False, tracking=True
    )
    document_type = fields.Selection([
        ('id_copy', 'ID Copy'),
        ('commercial_register', 'Commercial Register'),
        ('tax_card', 'Tax Card'),
        ('bank_statement', 'Bank Statement'),
        ('other', 'Other'),
    ], string='Document Type', tracking=True)
    attachment_id = fields.Many2one(
        'ir.attachment', string='File',
        ondelete='set null'
    )
    uploaded = fields.Boolean(
        string='Uploaded', compute='_compute_uploaded'
    )
    notes = fields.Text(string='Notes')

    @api.depends('attachment_id')
    def _compute_uploaded(self):
        for doc in self:
            doc.uploaded = bool(doc.attachment_id)
