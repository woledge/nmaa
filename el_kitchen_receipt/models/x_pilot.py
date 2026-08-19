# -*- coding: utf-8 -*-
from odoo import fields, models


class XPilot(models.Model):
    _name = 'x.pilot'
    _description = 'الطيارين'
    _order = 'name asc'

    name = fields.Char(
        string='اسم الطيار',
        required=True,
        translate=False,
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)', 'اسم الطيار موجود بالفعل!'),
    ]
