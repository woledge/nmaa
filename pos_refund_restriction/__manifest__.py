{
    'name': 'POS Refund Restriction',
    'version': '18.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'sequence': 10,
    'summary': 'Restrict refund operations in POS to administrators only',
    'author': 'Ibrahim Elmasry',
    'depends': ['point_of_sale'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_refund_restriction/static/src/js/pos_refund_restriction.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
