{
    'name': 'Stock Split Transfer',
    'version': '18.0.1.0.0',
    'author': 'Ibrahim Elmasry',
    'category': 'Inventory/Warehouse',
    'summary': 'Two-step internal transfers with per-user location visibility',
    'description': """
        Splits internal transfers into two legs (Source → Transit → Destination).
        Each leg is visible only to the user with access to its respective location.
        The second leg appears only after the first leg is validated.
    """,
    'depends': ['base', 'stock'],
    'data': [
        'views/views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
    'application': True,
}
