from odoo import http
from odoo.http import request

class ContractPortal(http.Controller):

    @http.route(['/my/contracts/<int:contract_id>'], type='http', auth="user", website=True)
    def view_contract(self, contract_id, **kwargs):
        contract = request.env['sale.contract'].sudo().browse(contract_id)

        # Excellent security check!
        if not contract.exists() or contract.partner_id != request.env.user.partner_id:
            return request.redirect('/my')

        return request.render("sale_contract_auto.portal_contract_page", {
            'contract': contract,
        })

    @http.route(['/my/contracts/<int:contract_id>/sign'], type='http', auth="user", methods=['POST'], website=True)
    def sign_contract(self, contract_id, **post):
        contract = request.env['sale.contract'].sudo().browse(contract_id)

        # Excellent security check!
        if not contract.exists() or contract.partner_id != request.env.user.partner_id:
            return request.redirect('/my')

        signature = post.get('signature')
        if signature:
            # The signature from signature_pad is a data URL (e.g., "data:image/png;base64,iVBORw...").
            # Odoo's Binary field expects only the base64 part. We split the string and take the second part.
            signature_data = signature.split(',')[1]
            contract.write({'second_party_signature': signature_data})

        return request.redirect(f'/my/contracts/{contract_id}')