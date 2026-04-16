from odoo import api, fields, models

class Contact(models.Model):
    _inherit = "res.partner"


    code = fields.Char(string="Code")





class AccountMove(models.Model):
    _inherit = "account.move"

    investor_code_id = fields.Many2one("investment.membership")

    investor_code = fields.Char(
        related="investor_code_id.investor_code",
        store=True,
        readonly=True
    )

    @api.depends('investor_code_id')
    def _compute_investor_code(self):
        for rec in self:
            rec.investor_code = rec.investor_code_id.investor_code if rec.investor_code_id else False