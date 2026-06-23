from odoo import http
from odoo.http import request

class PriceCheckerKiosk(http.Controller):

    # مسار فتح الشاشة (يمكن فتحه من أي تابلت في الهايبر)
    @http.route('/price-checker', type='http', auth='public', website=True)
    def price_checker_page(self, **kw):
        return request.render('hyper_price_checker.price_checker_kiosk_template')

    # مسار البحث عن المنتج بالباركود (API)
    @http.route('/price-checker/scan', type='json', auth='public')
    def scan_barcode(self, barcode):
        if not barcode:
            return {'found': False}
        
        # البحث عن المنتج باستخدام صلاحيات السوبر يوزر لأن المستخدم عام (Public)
        product = request.env['product.product'].sudo().search([('barcode', '=', barcode)], limit=1)
        
        if product:
            currency = product.company_id.currency_id.symbol or ''
            return {
                'found': True,
                'name': product.display_name,
                'price': f"{product.lst_price} {currency}",
                'image_url': f"/web/image/product.product/{product.id}/image_512"
            }
        return {'found': False}