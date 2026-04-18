from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # ===== Membership Settings =====
    membership_product_id = fields.Many2one(
        'product.product',
        string='Default Membership Product',
        config_parameter='investment_club.membership_product_id',
        domain="[('type', '=', 'service')]",
        help='Default product used when creating a new membership invoice.',
    )

    subscription_product_id = fields.Many2one(
        'product.product',
        string='Default Subscription Product',
        config_parameter='investment_club.subscription_product_id',
        domain="[('type', '=', 'service')]",
        help='Default product used when creating a renewal subscription invoice.',
    )

    subscription_period = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ], string='Default Subscription Period',
       config_parameter='investment_club.subscription_period',
       default='yearly',
       help='Default subscription period applied to new memberships.')

    auto_renewal_days = fields.Integer(
        string='Auto Renewal Days Before Expiry',
        config_parameter='investment_club.auto_renewal_days',
        default=7,
        help='Number of days before membership expiry to send renewal reminder.',
    )

    # ===== Payment Settings =====
    payment_journal_id = fields.Many2one(
        'account.journal',
        string='Default Payment Journal',
        config_parameter='investment_club.payment_journal_id',
        domain="[('type', 'in', ('bank', 'cash'))]",
        help='Default journal for membership and investment payments.',
    )

    return_payment_journal_id = fields.Many2one(
        'account.journal',
        string='Returns Payment Journal',
        config_parameter='investment_club.return_payment_journal_id',
        domain="[('type', 'in', ('bank', 'cash'))]",
        help='Default journal for paying out investment returns to investors.',
    )

    # ===== Project Settings =====
    auto_activate_projects = fields.Boolean(
        string='Auto Activate Projects',
        config_parameter='investment_club.auto_activate_projects',
        default=False,
        help='Automatically set new projects to active status upon creation.',
    )

    grace_period_months = fields.Integer(
        string='Default Grace Period (Months)',
        config_parameter='investment_club.grace_period_months',
        default=3,
        help='Default grace period before investment returns start accruing.',
    )

    # ===== Notification Settings =====
    enable_renewal_notifications = fields.Boolean(
        string='Enable Renewal Notifications',
        config_parameter='investment_club.enable_renewal_notifications',
        default=True,
        help='Send automated notifications before membership expiry.',
    )

    enable_payment_notifications = fields.Boolean(
        string='Enable Payment Notifications',
        config_parameter='investment_club.enable_payment_notifications',
        default=True,
        help='Send notifications when investment returns are paid.',
    )

    # ===== Access Settings =====
    restrict_project_creation = fields.Boolean(
        string='Restrict Project Creation to Managers',
        config_parameter='investment_club.restrict_project_creation',
        default=True,
        help='Only users with manager role can create new investment projects.',
    )

    require_approval_for_investment = fields.Boolean(
        string='Require Approval for Investments',
        config_parameter='investment_club.require_approval_for_investment',
        default=False,
        help='Investments require manager approval before activation.',
    )
