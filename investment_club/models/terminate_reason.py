from odoo import models, fields


class TerminateReason(models.Model):
    _name = 'terminate.reason'
    _description = 'Termination Reason'
    _order = 'sequence, id'

    name = fields.Char(string='Reason', required=True, translate=True)
    type = fields.Selection([
        ('membership', 'Membership'),
        ('subscription', 'Subscription'),
        ('both', 'Both'),
    ], string='Apply To', required=True, default='both')
    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(string='Sequence', default=10)
