{
    'name': "Sale Contract Auto",
    'version': '1.0',
    'category': 'Sales',
    'summary': "Automatically generate contracts from sale orders",
    'description': """
Sale Contract Auto
==================

This module allows you to:

• Create customer contracts
• Link contracts with sale orders
• Generate contract reports (PDF)
• Send contract link to customers via email
• Allow customers to access contracts from portal
""",

    'author': "Ibrahim Elmasry",
    'website': "https://www.woledge.com",
    'license': 'LGPL-3',

    'depends': [
        'base',
        'sale_management',
        'account',
        'portal',
        'mail',
    ],

    'data': [
        # Security
        'security/ir.model.access.csv',

        # Data
        'data/mail_templates.xml',

        # Sequences
        'views/ir_sequence.xml',

        # Views
        'views/res_partner_view.xml',
        'views/sale_contract_views.xml',
        'views/contract_template_views.xml',
        'views/templates.xml',
        # Reports
        'report/contract_report.xml',
        'report/contract_print_template.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}
