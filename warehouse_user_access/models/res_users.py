from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    warehouse_ids = fields.Many2many(
        comodel_name='stock.warehouse',
        relation='user_warehouse_rel',
        column1='user_id',
        column2='warehouse_id',
        string='Warehouses',
        groups='stock.group_stock_user',
    )