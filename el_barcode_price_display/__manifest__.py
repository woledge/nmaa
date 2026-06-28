# -*- coding: utf-8 -*-
{
    'name': 'Barcode Price Display',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Standalone barcode scanner price display page — no login needed',
    'description': """
Barcode Price Display
=======================

A standalone web page served at /price-display that listens to barcode scanner
input (no input field, no buttons, no Enter needed — 200ms debounce).

When a barcode is scanned:
- Product found → shows name + price (large) + image or colored placeholder
- Product not found → shows red "Product Not Found"
- Result auto-clears after 3 seconds, ready for next scan

Features:
- auth='public' — no Odoo login required
- Works on any tablet/screen with USB barcode scanner
- Placeholder: colored circle with first letter (for products without image)
- Vanilla JS + CSS (no framework, fast loading)
- RTL Arabic support

Author: Ibrahim Elmasry
License: LGPL-3
    """,
    'author': 'Ibrahim Elmasry',
    'website': 'https://github.com/ibrahimelmasry',
    'depends': ['base', 'product'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/templates.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
