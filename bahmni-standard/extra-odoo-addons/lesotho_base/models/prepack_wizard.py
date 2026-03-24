from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CreatePrepackWizard(models.TransientModel):
    _name = "create.prepack.wizard"
    _description = "Create Prepack Product Wizard"

    bulk_product_tmpl_id = fields.Many2one(
        "product.template",
        string="Bulk Product",
        required=True,
        readonly=True,
    )

    pack_qty = fields.Integer(string="Pack Size", default=10, required=True)
    pack_name_suffix = fields.Char(string="Name Suffix", compute="_compute_suffix", store=False)

    new_name = fields.Char(string="New Product Name", compute="_compute_new_name", store=False)
    new_default_code = fields.Char(string="New Internal Reference")

    @api.depends("pack_qty")
    def _compute_suffix(self):
        for w in self:
            w.pack_name_suffix = f" - Pack of {w.pack_qty}"

    @api.depends("bulk_product_tmpl_id", "pack_qty")
    def _compute_new_name(self):
        for w in self:
            if w.bulk_product_tmpl_id:
                w.new_name = f"{w.bulk_product_tmpl_id.name} - Pack of {w.pack_qty}"
            else:
                w.new_name = False

    def action_confirm(self):
        self.ensure_one()
        bulk = self.bulk_product_tmpl_id

        if self.pack_qty <= 0:
            raise UserError(_("Pack size must be greater than 0."))

        # Clone the template while keeping attributes/lines/etc.
        new_tmpl = bulk.copy(default={
            "name": self.new_name,
            "default_code": self.new_default_code or False,
            "is_prepack": True,
            "bulk_product_id": bulk.product_variant_id.id,
            "is_dispensing_pack": True,
            "dispensing_base_product_id": bulk.product_variant_id.id,
            "pack_unit_qty": self.pack_qty,
            "dispensing_pack_enabled": True,
        })



        # Open the new product template after creation
        return {
            "type": "ir.actions.act_window",
            "name": _("Prepack Product"),
            "res_model": "product.template",
            "view_mode": "form",
            "res_id": new_tmpl.id,
            "target": "current",
        }
