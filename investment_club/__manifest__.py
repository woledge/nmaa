# investment_club/__manifest__.py
{
    'name': 'Investment Clubs Management',
    'version': '18.0.9.0.0',
    'category': 'Investment',
    'summary': 'Complete investment management system with Unified Return System',
    'description': """
        Investment Clubs Management for Al-Namaa - Complete System

        Features:
        1. Customer Membership Number - رقم عضوية فريد للعميل
        2. Clubs Management - إدارة النوادي
        3. Projects Management - إدارة المشاريع
        4. Memberships - العضويات
        5. Investments - الاستثمارات (تظهر برقم العضوية)
        6. Return Payments - دفع العوائد (تظهر برقم العضوية)

        Unified Return System (New):
        - Return 1: One-time return (عائد مرة واحدة)
        - Return 2: Recurring return (عائد متكرر)
        - All fields available per project - fill what you need
        - Grace periods, durations, and dates fully configurable

        Customer Membership Number:
        - فريد (Unique) - لا يتكرر
        - يظهر في جميع الشاشات (Membership, Investment, Returns)
        - يستخدم في البحث والتصفية
        - يظهر في التقارير والفواتير
    """,
    'author': 'Woledge',
    'website': '',
    'depends': ['base', 'mail', 'account', 'analytic', 'product', 'contacts', 'crm', 'sale_contract_auto'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'data/cron_data.xml',
        'views/contact_view.xml',
        'views/investment_club_views.xml',
        'views/investment_project_views.xml',
        'views/membership_views.xml',
        'views/investment_subscription_views.xml',
        'views/actual_return_views.xml',
        'views/crm_lead_views.xml',
        'views/contact_codes_view.xml',
        'views/res_config_settings_views.xml',
        'views/account_payment_inherit_views.xml',
        'views/sale_contract_inherit_views.xml',
        'views/menu.xml',
        'views/terminate_wizards_views.xml',
        'security/investment_club_security.xml',  # Rules loaded AFTER models
        'reports/project_report.xml',
        'reports/returns_report.xml',
        'reports/renewal_due_report.xml',
        'reports/investor_report.xml',
        'reports/project_profit_report.xml',
        'reports/reports_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
