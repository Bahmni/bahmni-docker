from odoo.exceptions import UserError
from odoo.tests import SavepointCase, tagged


@tagged("post_install", "-at_install")
class TestPackSubstitution(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.unit_uom = cls.env.ref("uom.product_uom_unit")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.partner = cls.env["res.partner"].create({"name": "Test Patient"})

        cls.base_template = cls.env["product.template"].create(
            {
                "name": "Paracetamol 500 mg",
                "detailed_type": "product",
                "uom_id": cls.unit_uom.id,
                "uom_po_id": cls.unit_uom.id,
                "list_price": 1.0,
            }
        )
        cls.base_product = cls.base_template.product_variant_id

        cls.pack7_template = cls.env["product.template"].create(
            {
                "name": "Paracetamol 500 mg pack of 7",
                "detailed_type": "product",
                "uom_id": cls.unit_uom.id,
                "uom_po_id": cls.unit_uom.id,
                "list_price": 7.0,
                "is_prepack": True,
                "bulk_product_id": cls.base_product.id,
                "is_dispensing_pack": True,
                "dispensing_pack_enabled": True,
                "dispensing_base_product_id": cls.base_product.id,
                "pack_unit_qty": 7.0,
                "substitution_priority": 5,
            }
        )
        cls.pack7 = cls.pack7_template.product_variant_id

        cls.pack14_template = cls.env["product.template"].create(
            {
                "name": "Paracetamol 500 mg pack of 14",
                "detailed_type": "product",
                "uom_id": cls.unit_uom.id,
                "uom_po_id": cls.unit_uom.id,
                "list_price": 14.0,
                "is_prepack": True,
                "bulk_product_id": cls.base_product.id,
                "is_dispensing_pack": True,
                "dispensing_pack_enabled": True,
                "dispensing_base_product_id": cls.base_product.id,
                "pack_unit_qty": 14.0,
                "substitution_priority": 10,
            }
        )
        cls.pack14 = cls.pack14_template.product_variant_id

        cls.env["stock.quant"]._update_available_quantity(
            cls.pack7, cls.stock_location, 25.0
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.pack14, cls.stock_location, 10.0
        )

    def _create_line(self, qty):
        order = self.env["sale.order"].create({"partner_id": self.partner.id})
        return self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.base_product.id,
                "name": self.base_product.display_name,
                "product_uom_qty": qty,
                "product_uom": self.unit_uom.id,
                "price_unit": 1.0,
            }
        )

    def test_exact_fit_pack_of_14(self):
        line = self._create_line(14.0)

        candidates = line.get_pack_substitution_candidates()

        self.assertEqual(candidates[0]["product_id"], self.pack14.id)
        self.assertEqual(candidates[0]["packs_needed"], 1)

        line.action_apply_pack_substitution(self.pack14, 1)

        self.assertEqual(line.product_id, self.pack14)
        self.assertEqual(line.product_uom_qty, 1)
        self.assertTrue(line.is_pack_substituted)
        self.assertEqual(line.prescribed_product_id, self.base_product)
        self.assertEqual(line.prescribed_qty_base_units, 14.0)
        self.assertEqual(line.base_product_id, self.base_product)

    def test_exact_fit_two_packs_of_seven(self):
        line = self._create_line(14.0)

        candidates = line.get_pack_substitution_candidates()
        pack7_candidate = next(
            candidate for candidate in candidates if candidate["product_id"] == self.pack7.id
        )

        self.assertEqual(pack7_candidate["packs_needed"], 2)
        self.assertEqual(pack7_candidate["covered_qty"], 14.0)

        line.action_apply_pack_substitution(self.pack7, 2)

        self.assertEqual(line.product_id, self.pack7)
        self.assertEqual(line.product_uom_qty, 2)

    def test_non_exact_fit_rejected(self):
        self.pack14.dispensing_pack_enabled = False
        line = self._create_line(15.0)

        candidates = line.get_pack_substitution_candidates()

        self.assertFalse(candidates)
        with self.assertRaises(UserError):
            line.action_apply_pack_substitution(self.pack7, 2)

        self.pack14.dispensing_pack_enabled = True

    def test_original_prescribed_metadata_preserved(self):
        line = self._create_line(14.0)

        line.action_apply_pack_substitution(self.pack7, 2)

        self.assertEqual(line.prescribed_product_id, self.base_product)
        self.assertEqual(line.prescribed_qty_base_units, 14.0)
        self.assertEqual(line.prescribed_uom_id, self.unit_uom)
        self.assertEqual(line.base_product_id, self.base_product)
        self.assertTrue(line.substitution_note)
        self.assertEqual(line.substitution_user_id, self.env.user)
