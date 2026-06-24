# -*- coding: utf-8 -*-
{
    'name': 'Sale Order Barcode Scanner',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Scan products by Barcode/QRCode in sales orders using mobile camera or webcam',
    'author': 'Mohamed Helmy',
    'website': 'https://github.com/mohamed-helmy/sale_barcode_scanner',
    'depends': ['sale_management', 'product', 'barcodes'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
    ],
    # Cover image for Odoo Apps
    'images': ['static/description/main_screenshot.png'],
    'assets': {
        'web.assets_backend': [
            'sale_barcode_scanner/static/src/js/scanner_audio.js',
            'sale_barcode_scanner/static/src/js/barcode_scanner_widget.js',
            'sale_barcode_scanner/static/src/xml/barcode_scanner_templates.xml',
            'sale_barcode_scanner/static/src/css/barcode_scanner.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    # License must match LICENSE file in repository root
    'license': 'LGPL-3',
}
