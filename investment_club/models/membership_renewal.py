from odoo import models, fields, api


class MembershipRenewal(models.Model):
    _name = 'membership.renewal'
    _description = 'Membership Renewal History'
    _order = 'renewal_date desc'
    _rec_name = 'membership_id'

    membership_id = fields.Many2one(
        'investment.membership',
        string='Membership',
        required=True,
        ondelete='cascade'
    )

    partner_id = fields.Many2one(
        'res.partner',
        related='membership_id.partner_id',
        string='Customer',
        readonly=True
    )

    club_id = fields.Many2one(
        'investment.club',
        related='membership_id.club_id',
        string='Club',
        readonly=True
    )

    renewal_date = fields.Date(
        string='Renewal Date',
        required=True,
        default=fields.Date.today
    )

    amount = fields.Float(string='Amount', required=True)

    period = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ], string='Period', required=True)

    old_expiry_date = fields.Date(string='Previous Expiry')

    new_expiry_date = fields.Date(string='New Expiry')

    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        readonly=True,
        copy=False
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    notes = fields.Text(string='Notes', tracking=True)

    company_id = fields.Many2one(
        'res.company',
        related='membership_id.company_id',
        string='Company',
        store=True,
        readonly=True
    )

    def name_get(self):
        result = []
        for rec in self:
            name = '%s - %s' % (
                rec.membership_id.investor_code or rec.membership_id.membership_number or '',
                rec.renewal_date or ''
            )
            result.append((rec.id, name))
        return result
