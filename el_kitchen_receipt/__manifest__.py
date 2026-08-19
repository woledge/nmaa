{
    "name": "Kitchen Receipt from Quotation",
    "version": "18.0.4.0.0",
    "category": "Sales/Sales",
    "summary": "Print kitchen receipt from sales quotation with customer delivery info auto-fill + pilot name sync with delivery",
    "description": """
    Kitchen Receipt from Quotation
    ================================
    - Print 80mm thermal kitchen receipt from sales quotation
    - Pilot (driver) report — A4 PDF grouped by driver name
    - Delivery info fields on partner, sale order, picking, invoice
    - Auto-fill delivery info from contact to quotation
    - Sync delivery info back to contact (with chatter log)
    - Bidirectional driver name sync between sale.order and stock.picking
    - Pilot names as dropdown selection (Many2one to x.pilot)
    """,
    "author": "Ibrahim Elmasry",
    "license": "LGPL-3",
    "depends": [
        "sale",
        "account",
        "stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "reports/kitchen_receipt.xml",
        "reports/pilot_report.xml",
        "views/x_pilot_views.xml",
        "views/sale_order_views.xml",
        "views/res_partner_views.xml",
        "views/sale_order_search.xml",
        "views/pilot_report_wizard.xml",
        "views/pilot_report_buttons.xml",
        "views/stock_picking_views.xml",
        "views/account_move_views.xml",
    ],
    "pre_init_hook": "_pre_init_hook",
    "post_init_hook": "_post_init_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
}
