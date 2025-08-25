from odoo.tests.common import TransactionCase

class TestMyModule(TransactionCase):
    def test_create_record(self):
        rec = self.env['my.module'].create({'name': 'Test'})
        self.assertTrue(rec.id)
        rec.action_confirm()
        self.assertEqual(rec.state, 'confirm')
