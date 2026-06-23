# -*- coding: utf-8 -*-
{
    "name": "Kitchen Receipt from Quotation",
    "version": "18.0.2.0.0",
    "category": "Sales/Sales",
    "summary": "Print kitchen receipt from sales quotation with customer delivery info auto-fill",
    "author": "Your Company",
    "license": "LGPL-3",
    "depends": [
        "sale",
        "account",
    ],
    "data": [
        "reports/kitchen_receipt.xml",          # يجب أن يكون التقرير أولاً ليتم تعريفه في النظام
        "views/sale_order_views.xml",           # الواجهات ثانياً لتجد الأكستيرنال آي دي جاهزاً
        "views/res_partner_views.xml",          # واجهة الـ Contact لعرض بيانات التوصيل
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
