# Requirements — el_kitchen_receipt (rebuilt from sale_kitchen_receipt)

## Summary
Print kitchen receipt (80mm thermal) from sales quotation + pilot (driver) report + delivery info auto-fill.

## Models Extended
- res.partner: x_building_floor, x_landmark, x_driver_name
- sale.order: same fields + onchange auto-fill from partner + sync back to partner + sync to picking/invoice
- stock.picking: x_driver_name (bidirectional sync with sale.order)
- account.move: x_driver_name (passed from sale.order)
- pilot.report.wizard: TransientModel for pilot report generation

## Reports
1. Kitchen Receipt (80mm QWeb HTML, auto-print)
2. Pilot Report (A4 QWeb PDF)

## Fixes Applied (vs original)
- Version 18→19, removed utf-8 headers, fixed duplicate view ID, added ACL, fixed QWeb directives, added i18n, icon, tests
