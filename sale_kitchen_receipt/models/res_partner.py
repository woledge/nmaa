# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_building_floor = fields.Char(string="العمارة / الدور")
    x_landmark = fields.Char(string="علامة مميزة")
    x_driver_name = fields.Char(string="اسم الطيار")
