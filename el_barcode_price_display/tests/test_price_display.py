# -*- coding: utf-8 -*-
"""Test suite for Barcode Price Display controller."""

from odoo.tests import HttpCase, tagged
import json


@tagged('post_install', '-at_install')
class TestBarcodePriceDisplay(HttpCase):
    """Tests use HttpCase because routes are auth='public'."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 25.50,
            'barcode': '1234567890123',
        })
        cls.product_no_img = cls.env['product.product'].create({
            'name': 'No Image Product',
            'list_price': 10.00,
            'barcode': '9876543210987',
        })

    def test_01_page_loads(self):
        """GET /price-display should return HTML with 200 status."""
        response = self.url_open('/price-display')
        self.assertEqual(response.status_code, 200)
        content = response.text
        self.assertIn('Scan a product barcode', content)

    def test_02_product_found(self):
        """POST /price-display/search with valid barcode should return product."""
        response = self.url_open('/price-display/search', data=json.dumps({
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'barcode': '1234567890123'}, 'id': 1,
        }), headers={'Content-Type': 'application/json'})
        data = response.json()
        self.assertTrue(data['result']['found'])
        self.assertEqual(data['result']['name'], 'Test Product')
        self.assertEqual(data['result']['price'], 25.50)

    def test_03_product_not_found(self):
        """POST /price-display/search with unknown barcode should return not found."""
        response = self.url_open('/price-display/search', data=json.dumps({
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'barcode': 'UNKNOWN123'}, 'id': 1,
        }), headers={'Content-Type': 'application/json'})
        data = response.json()
        self.assertFalse(data['result']['found'])
        self.assertEqual(data['result']['barcode'], 'UNKNOWN123')

    def test_04_short_barcode_rejected(self):
        """Barcodes shorter than 4 chars should return error."""
        response = self.url_open('/price-display/search', data=json.dumps({
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'barcode': '12'}, 'id': 1,
        }), headers={'Content-Type': 'application/json'})
        data = response.json()
        self.assertFalse(data['result']['found'])
        self.assertEqual(data['result']['error'], 'too_short')

    def test_05_placeholder_for_no_image(self):
        """Product without image should return placeholder_letter + color."""
        response = self.url_open('/price-display/search', data=json.dumps({
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'barcode': '9876543210987'}, 'id': 1,
        }), headers={'Content-Type': 'application/json'})
        data = response.json()
        self.assertTrue(data['result']['found'])
        self.assertFalse(data['result']['image'])
        self.assertEqual(data['result']['placeholder_letter'], 'N')
        self.assertTrue(data['result']['placeholder_color'].startswith('#'))

    def test_06_placeholder_color_deterministic(self):
        """Same product name should always produce same placeholder color."""
        response1 = self.url_open('/price-display/search', data=json.dumps({
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'barcode': '9876543210987'}, 'id': 1,
        }), headers={'Content-Type': 'application/json'})
        response2 = self.url_open('/price-display/search', data=json.dumps({
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'barcode': '9876543210987'}, 'id': 2,
        }), headers={'Content-Type': 'application/json'})
        color1 = response1.json()['result']['placeholder_color']
        color2 = response2.json()['result']['placeholder_color']
        self.assertEqual(color1, color2)

    def test_07_product_with_image(self):
        """Product with image should return base64 image data."""
        # Set a small image on the product
        import base64
        tiny_png = base64.b64encode(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01\x5d\xcc\xdb\xf2\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        self.product.write({'image_128': tiny_png})
        response = self.url_open('/price-display/search', data=json.dumps({
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'barcode': '1234567890123'}, 'id': 1,
        }), headers={'Content-Type': 'application/json'})
        data = response.json()['result']
        self.assertTrue(data['found'])
        self.assertTrue(data['image'])
        self.assertTrue(data['image'].startswith('data:image/png;base64,'))

    def test_08_empty_barcode(self):
        """Empty barcode should return not found with error."""
        response = self.url_open('/price-display/search', data=json.dumps({
            'jsonrpc': '2.0', 'method': 'call',
            'params': {'barcode': ''}, 'id': 1,
        }), headers={'Content-Type': 'application/json'})
        data = response.json()
        self.assertFalse(data['result']['found'])
        self.assertEqual(data['result']['error'], 'too_short')

    def test_09_no_barcode_param(self):
        """Missing barcode param should return not found."""
        response = self.url_open('/price-display/search', data=json.dumps({
            'jsonrpc': '2.0', 'method': 'call',
            'params': {}, 'id': 1,
        }), headers={'Content-Type': 'application/json'})
        data = response.json()
        self.assertFalse(data['result']['found'])

    def test_10_groups_exist(self):
        """User and Manager groups should exist."""
        user_group = self.env.ref('el_barcode_price_display.group_barcode_price_user')
        mgr_group = self.env.ref('el_barcode_price_display.group_barcode_price_manager')
        self.assertTrue(user_group)
        self.assertTrue(mgr_group)
