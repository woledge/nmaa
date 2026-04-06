# investment_club/__manifest__.py
{
    'name': 'Investment Clubs Management',
    'version': '18.0.8.0.0', 
    'category': 'Investment',
    'summary': 'Complete investment management system with Customer Membership Number',
    'description': """
        Investment Clubs Management for Al-Namaa - Complete System
        
        Features:
        1. Customer Membership Number - رقم عضوية فريد للعميل
        2. Clubs Management - إدارة النوادي
        3. Projects Management - إدارة المشاريع
        4. Memberships - العضويات
        5. Investments - الاستثمارات (تظهر برقم العضوية)
        6. Return Payments - دفع العوائد (تظهر برقم العضوية)
        
        Customer Membership Number:
        - فريد (Unique) - لا يتكرر
        - يظهر في جميع الشاشات (Membership, Investment, Returns)
        - يستخدم في البحث والتصفية
        - يظهر في التقارير والفواتير
    """,
    'author': 'Al-Namaa Investment',
    'website': '',
    'depends': ['base', 'mail', 'account', 'analytic', 'product'],
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