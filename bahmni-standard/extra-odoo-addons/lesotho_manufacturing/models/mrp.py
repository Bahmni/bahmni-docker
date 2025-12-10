from odoo.exceptions import ValidationError

from odoo import _, api, fields, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    type = fields.Selection(
        selection=[
            (
                "normal",
                "Prepack this product",
            ),  # Changed from 'Manufacture this product'
            ("phantom", "Kit"),
        ],
        string="Prepacking Type",  # Changed from 'BoM Type'
        default="normal",
        required=True,
    )

    ready_to_produce = fields.Selection(
        selection=[
            ("all_available", "When all components are available"),
            ("asap", "When components for 1st operation are available"),
        ],
        string="Prepacking Readiness",  # Changed from 'Manufacturing Readiness'
        default="all_available",
        required=True,
    )

    picking_type_id = fields.Many2one(
        "stock.picking.type",
        "Operation Type",
        domain="[('code', '=', 'mrp_operation'), ('company_id', '=', company_id)]",
        check_company=True,
        help="When a procurement has a 'produce' route with an operation type set, "
        "it will try to create a Prepacking Order for that product using a Prepacking Template of the same operation type. "  # Changed from 'Manufacturing Order' and 'BoM'
        "That allows to define stock rules which trigger different prepacking orders with different prepacking templates.",
    )

    @api.onchange("bom_line_ids", "product_qty", "product_id", "product_tmpl_id")
    def onchange_bom_structure(self):
        if (
            self.type == "phantom"
            and self._origin
            and self.env["stock.move"].search(
                [("bom_line_id", "=", self._origin.bom_line_ids.ids)], limit=1
            )
        ):
            return {
                "warning": {
                    "title": _("Warning"),
                    "message": _(
                        "The product has already been used at least once, editing its structure may lead to undesirable behaviours. "
                        "You should rather archive the product and create a new one with a new prepacking template."
                    ),  # Changed from 'bill of materials'
                }
            }
