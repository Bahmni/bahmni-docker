from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = "product.template"

    elmis_code = fields.Char(
        string="eLMIS Code",
        help="OpenLMIS product code for integration.",
        index=True,
        copy=False,
    )

    is_prepack = fields.Boolean(
        string="Is Prepack?",
        default=False
    )

    bulk_product_id = fields.Many2one(
        'product.product',
        string="Bulk Product",
        domain="[('type', 'in', ['product', 'consu'])]",
        help="The bulk product used to create this prepack"
    )

    is_dispensing_pack = fields.Boolean(
        string="Is Dispensing Pack",
        help="Enable this product as a dispensing-time pack substitute.",
        default=False,
    )

    dispensing_base_product_id = fields.Many2one(
        "product.product",
        string="Dispensing Base Product",
        domain="[('type', 'in', ['product', 'consu'])]",
        help="Loose/base product that this pack substitutes during dispensing.",
    )

    pack_unit_qty = fields.Float(
        string="Pack Unit Quantity",
        digits=(16, 4),
        help="Number of base units contained in one pack.",
    )

    dispensing_pack_enabled = fields.Boolean(
        string="Dispensing Pack Enabled",
        default=False,
        help="Allow this pack product to appear in the dispensing pack substitution wizard.",
    )

    pack_bom_id = fields.Many2one(
        "mrp.bom",
        string="Dispensing Pack BoM",
        help="Optional BoM reference used to derive or validate pack substitution metadata.",
    )

    substitution_priority = fields.Integer(
        string="Substitution Priority",
        default=10,
        help="Higher values rank first when multiple exact-fit packs are available.",
    )

    @api.onchange("bulk_product_id")
    def _onchange_bulk_product_id_dispensing_base(self):
        for product in self:
            if not product.dispensing_base_product_id and product.bulk_product_id:
                product.dispensing_base_product_id = product.bulk_product_id

    @api.onchange("pack_bom_id")
    def _onchange_pack_bom_id(self):
        for product in self:
            bom = product.pack_bom_id
            if not bom:
                continue
            base_product = False
            unique_products = bom.bom_line_ids.mapped("product_id")
            if len(unique_products) == 1:
                base_product = unique_products[0]
            if base_product and not product.dispensing_base_product_id:
                product.dispensing_base_product_id = base_product
            if (
                base_product
                and bom.product_qty
                and not product.pack_unit_qty
            ):
                matching_lines = bom.bom_line_ids.filtered(
                    lambda line: line.product_id == base_product
                )
                component_qty = sum(matching_lines.mapped("product_qty"))
                if component_qty:
                    product.pack_unit_qty = component_qty / bom.product_qty

    @api.constrains("is_dispensing_pack", "dispensing_base_product_id", "pack_unit_qty")
    def _check_dispensing_pack_configuration(self):
        for product in self:
            if not product.is_dispensing_pack:
                continue
            if not product.dispensing_base_product_id:
                raise ValidationError(
                    _("Dispensing packs must define a dispensing base product.")
                )
            if product.pack_unit_qty <= 0:
                raise ValidationError(
                    _("Dispensing packs must define a positive pack unit quantity.")
                )

    def create_prepack_product(self):
        pass


class ProductProduct(models.Model):
    _inherit = "product.product"

    is_dispensing_pack = fields.Boolean(
        related="product_tmpl_id.is_dispensing_pack",
        store=True,
        readonly=False,
    )
    dispensing_base_product_id = fields.Many2one(
        related="product_tmpl_id.dispensing_base_product_id",
        store=True,
        readonly=False,
    )
    pack_unit_qty = fields.Float(
        related="product_tmpl_id.pack_unit_qty",
        store=True,
        readonly=False,
    )
    dispensing_pack_enabled = fields.Boolean(
        related="product_tmpl_id.dispensing_pack_enabled",
        store=True,
        readonly=False,
    )
    pack_bom_id = fields.Many2one(
        related="product_tmpl_id.pack_bom_id",
        store=True,
        readonly=False,
    )
    substitution_priority = fields.Integer(
        related="product_tmpl_id.substitution_priority",
        store=True,
        readonly=False,
    )
