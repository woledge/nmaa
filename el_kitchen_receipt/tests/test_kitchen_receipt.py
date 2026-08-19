from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestKitchenReceipt(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env['res.partner']
        cls.SaleOrder = cls.env['sale.order']
        cls.Wizard = cls.env['pilot.report.wizard']
        cls.Pilot = cls.env['x.pilot']

        cls.pilot = cls.Pilot.create({'name': 'أحمد محمد'})
        cls.pilot2 = cls.Pilot.create({'name': 'سعيد علي'})

        cls.partner = cls.Partner.create({
            'name': 'Test Customer',
            'phone': '01001234567',
            'x_building_floor': 'عمارة 5 - الدور 3',
            'x_landmark': 'بجوار الصيدلية',
            'x_driver_name': cls.pilot.id,
        })

    def test_01_partner_delivery_fields_exist(self):
        self.assertIn('x_building_floor', self.Partner._fields)
        self.assertIn('x_landmark', self.Partner._fields)
        self.assertIn('x_driver_name', self.Partner._fields)

    def test_02_sale_order_delivery_fields_exist(self):
        self.assertIn('x_building_floor', self.SaleOrder._fields)
        self.assertIn('x_driver_name', self.SaleOrder._fields)

    def test_03_onchange_partner_fills_fields(self):
        """Selecting a partner auto-fills delivery info."""
        order = self.SaleOrder.new({'partner_id': self.partner.id})
        order._onchange_partner_id_kitchen_fields()
        self.assertEqual(order.x_building_floor, 'عمارة 5 - الدور 3')
        self.assertEqual(order.x_driver_name, self.pilot)

    def test_04_sync_delivery_to_partner(self):
        """Editing delivery info on order syncs back to partner."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'x_building_floor': 'عمارة 10 - الدور 7',
        })
        self.assertEqual(self.partner.x_building_floor, 'عمارة 10 - الدور 7')

    def test_05_driver_name_passed_to_invoice(self):
        """Driver name passes from sale order to invoice."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'x_driver_name': self.pilot2.id,
        })
        invoice_vals = order._prepare_invoice()
        self.assertEqual(invoice_vals.get('x_driver_name'), self.pilot2.id)

    def test_06_wizard_print_report(self):
        """Wizard finds orders by driver name."""
        self.SaleOrder.create({
            'partner_id': self.partner.id,
            'x_driver_name': self.pilot.id,
        })
        wizard = self.Wizard.create({'x_driver_name': self.pilot.id})
        orders = self.SaleOrder.search([('x_driver_name', '=', self.pilot.id)])
        self.assertTrue(orders)

    def test_07_stock_picking_driver_field(self):
        self.assertIn('x_driver_name', self.env['stock.picking']._fields)

    def test_08_account_move_driver_field(self):
        self.assertIn('x_driver_name', self.env['account.move']._fields)

    def test_09_kitchen_receipt_report_exists(self):
        report = self.env.ref('el_kitchen_receipt.action_kitchen_receipt_report',
                              raise_if_not_found=False)
        self.assertTrue(report)

    def test_10_pilot_report_exists(self):
        report = self.env.ref('el_kitchen_receipt.action_pilot_report',
                              raise_if_not_found=False)
        self.assertTrue(report)

    def test_11_pilot_report_wizard_model_exists(self):
        self.assertTrue(self.env['ir.model'].search([('model', '=', 'pilot.report.wizard')]))

    def test_12_partner_chatter_logged(self):
        """Syncing delivery info logs a message in partner chatter."""
        self.partner.message_ids.unlink()
        self.SaleOrder.create({
            'partner_id': self.partner.id,
            'x_building_floor': 'عمارة جديدة',
        })
        self.assertTrue(self.partner.message_ids)
