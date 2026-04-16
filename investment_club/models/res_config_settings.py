# investment_club/models/res_config_settings.py
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # ===== إعدادات العضويات =====
    membership_product_id = fields.Many2one(
        'product.product',
        string='Default Membership Product',
        config_parameter='investment_club.membership_product_id',
        domain="[('type', '=', 'service')]",
    )
    
    subscription_product_id = fields.Many2one(
        'product.product',
        string='Default Subscription Product',
        config_parameter='investment_club.subscription_product_id',
        domain="[('type', '=', 'service')]",
    )
    
    subscription_period = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ], string='Default Subscription Period', 
       config_parameter='investment_club.subscription_period',
       default='yearly')
    
    auto_renewal_days = fields.Integer(
        string='Auto Renewal Days Before',
        config_parameter='investment_club.auto_renewal_days',
        default=7,
    )

    # ===== إعدادات مالية =====
    payment_journal_id = fields.Many2one(
        'account.journal',
        string='Default Payment Journal',
        config_parameter='investment_club.payment_journal_id',
        domain="[('type', 'in', ('bank', 'cash'))]",
    )
    
    return_payment_journal_id = fields.Many2one(
        'account.journal',
        string='Returns Payment Journal',
        config_parameter='investment_club.return_payment_journal_id',
        domain="[('type', 'in', ('bank', 'cash'))]",
    )

    # ===== إعدادات المشاريع =====
    auto_activate_projects = fields.Boolean(
        string='Auto Activate Projects',
        config_parameter='investment_club.auto_activate_projects',
        default=False,
    )
    
    grace_period_months = fields.Integer(
        string='Default Grace Period (Months)',
        config_parameter='investment_club.grace_period_months',
        default=3,
    )

    # ===== إعدادات الإشعارات =====
    enable_renewal_notifications = fields.Boolean(
        string='Enable Renewal Notifications',
        config_parameter='investment_club.enable_renewal_notifications',
        default=True,
    )
    
    enable_payment_notifications = fields.Boolean(
        string='Enable Payment Notifications',
        config_parameter='investment_club.enable_payment_notifications',
        default=True,
    )

    # ===== إعدادات الأمان =====
    restrict_project_creation = fields.Boolean(
        string='Restrict Project Creation to Managers',
        config_parameter='investment_club.restrict_project_creation',
        default=True,
    )
    
    require_approval_for_investment = fields.Boolean(
        string='Require Approval for Investments',
        config_parameter='investment_club.require_approval_for_investment',
        default=False,
    )