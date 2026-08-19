# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_driver_name = fields.Many2one(
        'x.pilot',
        string='اسم الطيار',
        ondelete='restrict',
    )
