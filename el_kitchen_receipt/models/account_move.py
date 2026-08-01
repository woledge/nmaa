from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_driver_name = fields.Char(string="اسم الطيار")
