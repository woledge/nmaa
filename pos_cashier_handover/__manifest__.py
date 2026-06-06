{
    'name': 'POS Cashier Handover Report',
    'version': '18.0.1.0.0',
    'summary': 'طباعة تسليم الخزينة عند إغلاق جلسة نقطة البيع',
    'author': 'Ibrahim Elmasry',
    'category': 'Point of Sale',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'report/report_cashier_handover.xml',
        'report/report_cashier_handover_template.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_cashier_handover/static/src/js/pos_cashier_handover.js',
            'pos_cashier_handover/static/src/xml/pos_cashier_handover.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
