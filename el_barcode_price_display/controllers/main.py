# -*- coding: utf-8 -*-
"""Controller for standalone barcode price display page.

Two routes:
  /price-display         → serves HTML page (auth='public')
  /price-display/search  → JSON endpoint for product lookup (auth='public')
"""

import hashlib
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

# 8-color palette for placeholder backgrounds
PLACEHOLDER_COLORS = [
    '#714B67',  # Odoo purple
    '#017E84',  # Teal
    '#F4A261',  # Orange
    '#E76F51',  # Coral
    '#2A9D8F',  # Green
    '#264653',  # Dark blue
    '#E63946',  # Red
    '#457B9D',  # Blue
]


class BarcodePriceDisplay(http.Controller):

    @http.route('/price-display', type='http', auth='public', csrf=False, sitemap=False)
    def price_display_page(self, **kw):
        """Serve the standalone HTML page."""
        return request.render('el_barcode_price_display.price_page', {})

    @http.route('/price-display/search', type='json', auth='public', csrf=False)
    def price_display_search(self, barcode=False, **kw):
        """Search product by barcode. Returns JSON with product info or not_found.

        If product has no image, generates a placeholder:
        - Colored circle with first letter of product name
        - Color is deterministic (same product = same color via MD5 hash)
        """
        if not barcode or len(str(barcode)) < 4:
            return {'found': False, 'barcode': barcode or '', 'error': 'too_short'}

        barcode = str(barcode).strip()
        product = request.env['product.product'].sudo().search(
            [('barcode', '=', barcode)], limit=1
        )

        if not product:
            return {'found': False, 'barcode': barcode}

        # Image / placeholder logic
        image_data = False
        placeholder_letter = False
        placeholder_color = False

        if product.image_128:
            import base64
            image_data = 'data:image/png;base64,' + base64.b64encode(
                product.image_128
            ).decode('utf-8')
        else:
            # Generate placeholder: first letter + deterministic color
            name = product.name or '?'
            placeholder_letter = name[0].upper()
            color_index = int(
                hashlib.md5(name.encode('utf-8')).hexdigest(), 16
            ) % len(PLACEHOLDER_COLORS)
            placeholder_color = PLACEHOLDER_COLORS[color_index]

        return {
            'found': True,
            'name': product.name or 'Unknown',
            'price': product.list_price or 0.0,
            'currency': product.currency_id.symbol or '',
            'barcode': product.barcode or barcode,
            'image': image_data,
            'placeholder_letter': placeholder_letter,
            'placeholder_color': placeholder_color,
        }
