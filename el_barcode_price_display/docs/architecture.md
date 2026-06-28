# Architecture — Barcode Price Display

## No Custom Models
This module has no custom models. It reads from `product.product` via controller.

## Controller
`BarcodePriceDisplay(http.Controller)` with two routes:
- `GET /price-display` → serves HTML page (QWeb template)
- `POST /price-display/search` → JSON-RPC endpoint for product lookup

## Barcode Capture Flow
```
Scanner sends digits → window.addEventListener('keydown')
  → buffer collects digits (0-9 only)
  → 200ms debounce (no new digit = barcode complete)
  → fetch('/price-display/search', {barcode: buffer})
  → Controller: search product.product by barcode
  → Found: return {name, price, currency, image or placeholder}
  → Not found: return {found: false}
  → JS: display result for 3 seconds
  → setTimeout 3000ms → clearAll() → ready for next scan
```

## Placeholder Logic
```
Product has image_128?
  YES → return base64 image
  NO  → generate placeholder:
        - first_letter = product.name[0].upper()
        - color = PLACEHOLDER_COLORS[md5(name) % 8]
        → return {placeholder_letter, placeholder_color}
```

## Security
- `auth='public'` — no login required (kiosk/tablet use case)
- `.sudo()` on search — bypass access rights for public user
- `csrf=False` — scanner device doesn't send CSRF tokens
- XSS protection: `escapeHtml()` on all user-returned text in JS
