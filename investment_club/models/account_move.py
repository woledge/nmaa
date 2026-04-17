from odoo import fields, models

class AccountMove(models.Model):
    _inherit = "account.move"

    investor_code_id = fields.Many2one("investment.membership")

    investor_code = fields.Char(
        related="investor_code_id.investor_code",
        store=True,
        readonly=True
    )

    _rec_name = "investor_code"

    # def action_open_membership(self):
    #     pass