from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    allowed_location_ids = fields.Many2many(
        'stock.location',
        relation='res_users_stock_location_rel',
        column1='user_id',
        column2='location_id',
        string='Allowed Locations',
        help='Warehouse locations this user has access to manage transfers. '
             'Leave empty to see all pickings (admin behavior).',
    )

    @api.model
    def _get_self_readable_fields(self):
        return super()._get_self_readable_fields() | {'allowed_location_ids'}

    @api.model
    def _get_self_writeable_fields(self):
        return super()._get_self_writeable_fields() | {'allowed_location_ids'}
