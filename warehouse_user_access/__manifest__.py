{
    'name': 'Warehouse User Access',
    'version': '18.0.1.0.0',
    'category': 'Sales/Warehouse',
    'summary': 'Restrict sales users to specific warehouses',
    'description': """
        Allows assigning warehouses to users so they only see
        sales orders and quotations linked to their assigned warehouses.
    """,
    'author': 'Custom',
    'depends': ['sale', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'security/warehouse_user_access_security.xml',
        'views/res_users_views.xml',
    ],
    'installable': True,
    'application': True,
}