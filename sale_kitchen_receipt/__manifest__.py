# -*- coding: utf-8 -*-
{
    "name": "Kitchen Receipt from Quotation",
    "version": "18.0.3.0.0",
    "category": "Sales/Sales",
    "summary": "Print kitchen receipt from sales quotation with customer delivery info auto-fill + pilot name sync with delivery",
    "author": "Your Company",
    "license": "LGPL-3",
    "depends": [
        "sale",
        "account",
        "stock",                              # ضروري لربط اسم الطيار مع شاشة الدليفري (stock.picking)
    ],
    "data": [
        "reports/kitchen_receipt.xml",          # يجب أن يكون التقرير أولاً ليتم تعريفه في النظام
        "reports/pilot_report.xml",             # تقرير الطيار
        "views/sale_order_views.xml",           # الواجهات ثانياً لتجد الأكستيرنال آي دي جاهزاً
        "views/res_partner_views.xml",          # واجهة الـ Contact لعرض بيانات التوصيل
        "views/sale_order_search.xml",          # فلتر البحث باسم الطيار
        "views/pilot_report_wizard.xml",        # ويزارد تقرير الطيار
        "views/stock_picking_views.xml",        # شاشة الدليفري: عرض + تعديل اسم الطيار
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
