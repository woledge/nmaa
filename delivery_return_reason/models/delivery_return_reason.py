# -*- coding: utf-8 -*-
from odoo import fields, models


class DeliveryReturnReason(models.Model):
    _name = 'delivery.return.reason'
    _description = 'أسباب رجوع التسليم'
    _order = 'sequence, name'
    _rec_name = 'name'

    name = fields.Char(string="السبب", required=True, translate=True)
    sequence = fields.Integer(string="الترتيب", default=10)
    active = fields.Boolean(string="نشط", default=True)
    company_id = fields.Many2one(
        'res.company',
        string="الشركة",
        default=lambda self: self.env.company,
    )