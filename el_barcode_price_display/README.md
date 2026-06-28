# Barcode Price Display

**Odoo 18 — Standalone barcode scanner price display page**

## What It Does
A standalone web page at `/price-display` that listens to barcode scanner input.
No login, no buttons, no input fields — just scan and see the price.

## Features
1. **No Odoo login** — `auth='public'`, accessible from any device on the network
2. **No input field** — listens to `window.addEventListener('keydown')`
3. **No Enter needed** — 200ms debounce detects end of barcode automatically
4. **Product found** → shows image (or colored placeholder) + name + price (large)
5. **Product not found** → shows red "Product Not Found"
6. **Auto-clear after 3 seconds** — ready for next scan
7. **Placeholder** — colored circle with first letter (for products without image)
8. **Vanilla JS + CSS** — no framework, fast loading, works on tablets

## Installation
```bash
cp -r el_barcode_price_display /path/to/odoo/custom_addons/
odoo -d yourdb -i el_barcode_price_display --stop-after-init
```

## Usage
1. Open `http://your-odoo:8069/price-display` on any tablet/screen
2. Scan a product barcode with your USB scanner
3. Price appears for 3 seconds, then clears automatically

## Routes
| Route | Method | Auth | Purpose |
|-------|--------|------|---------|
| `/price-display` | GET | public | HTML page |
| `/price-display/search` | POST (JSON) | public | Product lookup |

## License
LGPL-3 — Ibrahim Elmasry
