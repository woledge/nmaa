# -*- coding: utf-8 -*-
from odoo import fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_building_floor = fields.Char(string="العمارة / الدور")
    x_landmark = fields.Char(string="علامة مميزة")
    x_driver_name = fields.Char(string="اسم الطيار")