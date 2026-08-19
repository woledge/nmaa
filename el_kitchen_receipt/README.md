# Kitchen Receipt from Quotation (`el_kitchen_receipt`)

> Print 80mm thermal kitchen receipt from sales quotation + pilot report + delivery info management.

## Features
1. **Kitchen Receipt** — 80mm thermal print from quotation/invoice
2. **Pilot Report** — A4 PDF of all orders by driver name
3. **Delivery Fields** — building/floor, landmark, driver name on partner/sale order/picking/invoice
4. **Auto-fill** — delivery info auto-fills from contact to quotation
5. **Sync Back** — editing delivery info on quotation syncs back to contact + logs in chatter
6. **Driver Sync** — bidirectional sync between sale.order and stock.picking
7. **Invoice Sync** — driver name passes from sale order to invoice

## Installation
1. Copy to `addons/`
2. Restart Odoo → Update Apps List → Install

## LAW 26 Waiver
Run on real Odoo 19 before production:
```bash
odoo -d <db> -i el_kitchen_receipt --test-enable --test-tags=/el_kitchen_receipt --stop-after-init
```
