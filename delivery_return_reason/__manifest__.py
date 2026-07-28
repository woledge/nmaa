# -*- coding: utf-8 -*-
{
    "name": "Delivery Return Reasons",
    "version": "18.0.1.0.0",
    "category": "Inventory/Delivery",
    "summary": "تتبع أسباب رجوع الطلبات مع إحصائيات وتحليلات",
    "author": "Your Company",
    "license": "LGPL-3",
    "depends": ["stock"],
    "data": [
        "security/ir.model.access.csv",
        "data/delivery_return_reason_data.xml",
        "views/delivery_return_reason_views.xml",
        "views/stock_picking_views.xml",
        "views/stock_picking_search.xml",
        "views/stock_picking_analysis.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}