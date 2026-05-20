# -*- coding: utf-8 -*-
{
    "name": "Kitchen Receipt from Quotation",
    "version": "18.0.1.0.0",
    "category": "Sales/Sales",
    "summary": "Print kitchen receipt from sales quotation",
    "author": "Your Company",
    "license": "LGPL-3",
    "depends": [
        "sale",
        "account",
    ],
    "data": [
        "views/sale_order_views.xml",
        "reports/kitchen_receipt.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}