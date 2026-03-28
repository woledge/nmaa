# investment_club/__manifest__.py
{
    'name': 'Investment Clubs Management',
    'version': '18.0.8.0.0',
    'category': 'Investment',
    'summary': 'Complete investment management system',
    'description': """
        Investment Clubs Management for Al-Namaa - Complete System
        
        Modules:
        1. Clubs - إدارة النوادي (Elite & Retail)
        2. Projects - إدارة المشاريع مع Analytic Accounts
        3. Memberships - العضويات (سعر أولي + اشتراك سنوي منفصل)
        4. Investments - الاستثمارات (دفع مباشر بدون فاتورة)
        5. Return Payments - دفع العوائد الفعلية للعملاء
        
        Accounting:
        - General Ledger integration
        - Analytic Accounting per project
        - Partner Ledger tracking
        - Automated payment registration
        
        Reports:
        1. Renewal Due - التجديدات المستحقة
        2. Monthly Returns - العوائد المتوقعة
        3. Investor Summary - ملخص المستثمرين
        4. Active Investments - الاستثمارات النشطة
        5. All Investors - كل المستثمرين
        6. Return Payments - سجل دفع العوائد
    """,
    'author': 'Woledge',
    'website': 'https://woledge.com',
    'depends': ['base', 'mail', 'account', 'analytic'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/investment_club_views.xml',
        'views/investment_project_views.xml',
        'views/membership_views.xml',
        'views/investment_subscription_views.xml',
        'views/actual_return_views.xml',
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