# Testing — Barcode Price Display

## Test Suite (10 cases — HttpCase)

Uses `HttpCase` because routes are `auth='public'`.

| # | Test | Expected |
|---|------|----------|
| 1 | GET /price-display | 200 + HTML contains "Scan a product barcode" |
| 2 | Search valid barcode | found=True, correct name + price |
| 3 | Search unknown barcode | found=False, barcode returned |
| 4 | Short barcode (< 4 chars) | found=False, error='too_short' |
| 5 | Product without image | placeholder_letter + placeholder_color returned |
| 6 | Placeholder color deterministic | Same product = same color across calls |
| 7 | Product with image | base64 image data returned |
| 8 | Empty barcode | found=False, error='too_short' |
| 9 | Missing barcode param | found=False |
| 10 | Groups exist | User + Manager groups created |
