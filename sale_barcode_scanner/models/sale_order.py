# -*- coding: utf-8 -*-

from odoo import models, _


class SaleOrder(models.Model):
  _inherit = 'sale.order'

  def action_open_barcode_scanner(self):
    return {
        'type': 'ir.actions.client',
        'tag': 'sale_barcode_scanner',
        'target': 'new',
        'context': {
            'active_id': self.id,
            'active_model': 'sale.order',
        }
    }

  def add_product_by_barcode(self, barcode):
    self.ensure_one()

    if not barcode:
      return {
          'success': False,
          'error': _('No barcode provided'),
      }

    product = self.env['product.product'].search(
        ['|', ('barcode', '=', barcode), ('default_code', '=', barcode)], limit=1)

    if not product:
      return {
          'success': False,
          'error': _('No product found with barcode: %s') % barcode,
      }

    existing_line = self.order_line.filtered(lambda l: l.product_id == product)

    if existing_line:
      existing_line[0].product_uom_qty += 1
      line = existing_line[0]
    else:
      line = self.env['sale.order.line'].create({
          'order_id': self.id,
          'product_id': product.id,
          'product_uom_qty': 1,
          'price_unit': product.list_price,
      })

    return {
        'success': True,
        'product_name': product.name,
        'product_code': product.default_code or '',
        'quantity': line.product_uom_qty,
        'line_id': line.id,
    }
