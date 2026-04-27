from odoo import models, fields, api
from odoo.exceptions import UserError


class ContractPaymentSchedule(models.Model):
    _name = 'contract.payment.schedule'
    _description = 'Contract Installment Schedule'
    _order = 'installment_number'

    contract_id = fields.Many2one(
        'sale.contract', string='Contract',
        ondelete='cascade', tracking=True
    )
    installment_number = fields.Integer(
        string='Installment #', required=True, tracking=True
    )
    amount = fields.Monetary(
        string='Amount', required=True, tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency', related='contract_id.currency_id'
    )
    due_date = fields.Date(
        string='Due Date', required=True, tracking=True
    )
    invoice_id = fields.Many2one(
        'account.move', string='Invoice'
    )
    state = fields.Selection([
        ('pending', 'Pending'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid'),
    ], default='pending', tracking=True)

    def action_create_installment_invoice(self):
        """Create invoice for this installment"""
        for rec in self:
            if rec.invoice_id:
                raise UserError("Invoice already created for this installment.")
            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': rec.contract_id.partner_id.id,
                'contract_id': rec.contract_id.id,
                'invoice_line_ids': [(0, 0, {
                    'name': f'Contract {rec.contract_id.name} - Installment {rec.installment_number}',
                    'quantity': 1,
                    'price_unit': rec.amount,
                })],
            }
            invoice = self.env['account.move'].create(invoice_vals)
            rec.write({'invoice_id': invoice.id, 'state': 'invoiced'})
            rec.contract_id.message_post(
                body=f"<b>Installment Invoice Created</b><br/>Installment #{rec.installment_number}: <a href='#' data-oe-model='account.move' data-oe-id='{invoice.id}'>{invoice.name}</a>"
            )

    def open_invoice(self):
        """Open the invoice form for this installment"""
        self.ensure_one()
        if self.invoice_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Invoice',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': self.invoice_id.id,
                'target': 'current',
            }
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def _cron_auto_create_invoices(self):
        """Scheduled action: auto-create invoices for due pending installments"""
        today = fields.Date.today()
        due_installments = self.search([
            ('state', '=', 'pending'),
            ('due_date', '<=', today),
        ])
        for installment in due_installments:
            try:
                installment.action_create_installment_invoice()
            except Exception:
                pass
        return True
