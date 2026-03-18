from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class BahmniPrepackBatch(models.Model):
    _name = "bahmni.prepack.batch"
    _description = "Bahmni Prepack Batch"
    _order = "planned_date desc, id desc"

    name = fields.Char(
        string="Batch Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("generated", "Orders Generated"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        default="draft",
        required=True,
        copy=False,
    )
    planned_date = fields.Datetime(
        string="Planned Date",
        required=True,
        default=fields.Datetime.now,
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    responsible_id = fields.Many2one(
        "res.users",
        string="Responsible",
        default=lambda self: self.env.user,
    )
    picking_type_id = fields.Many2one(
        "stock.picking.type",
        string="Manufacturing Operation Type",
        required=True,
        domain="[('code', '=', 'mrp_operation')]",
        default=lambda self: self._default_picking_type_id(),
    )
    location_src_id = fields.Many2one(
        "stock.location",
        string="Components Location",
        required=True,
    )
    location_dest_id = fields.Many2one(
        "stock.location",
        string="Finished Goods Location",
        required=True,
    )
    line_ids = fields.One2many(
        "bahmni.prepack.batch.line",
        "batch_id",
        string="Lines",
        copy=True,
    )
    note = fields.Text()
    line_count = fields.Integer(compute="_compute_counts")
    mrp_production_ids = fields.Many2many(
        "mrp.production",
        compute="_compute_mrp_production_ids",
        string="Manufacturing Orders",
    )
    mrp_production_count = fields.Integer(compute="_compute_counts")

    @api.model
    def _default_picking_type_id(self):
        picking_type = self.env["stock.picking.type"].search(
            [
                ("code", "=", "mrp_operation"),
                "|",
                ("company_id", "=", False),
                ("company_id", "=", self.env.company.id),
            ],
            order="company_id desc, sequence, id",
            limit=1,
        )
        return picking_type.id

    @api.depends("line_ids", "line_ids.mrp_production_id")
    def _compute_counts(self):
        for batch in self:
            batch.line_count = len(batch.line_ids)
            batch.mrp_production_count = len(batch.line_ids.mapped("mrp_production_id"))

    @api.depends("line_ids.mrp_production_id")
    def _compute_mrp_production_ids(self):
        for batch in self:
            batch.mrp_production_ids = batch.line_ids.mapped("mrp_production_id")

    @api.onchange("picking_type_id")
    def _onchange_picking_type_id(self):
        for batch in self:
            batch.location_src_id = batch.picking_type_id.default_location_src_id
            batch.location_dest_id = batch.picking_type_id.default_location_dest_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("bahmni.prepack.batch") or _("New")
        records = super().create(vals_list)
        for record in records.filtered(lambda r: not r.location_src_id or not r.location_dest_id):
            record._onchange_picking_type_id()
        return records

    def unlink(self):
        for batch in self:
            if batch.state != "draft" or batch.line_ids.filtered("mrp_production_id"):
                raise UserError(_("Only draft batches without generated manufacturing orders can be deleted."))
        return super().unlink()

    def action_generate_orders(self):
        for batch in self:
            batch._check_can_edit_workflow()
            if batch.state != "draft":
                raise UserError(_("Orders can only be generated while the batch is in Draft."))
            if not batch.line_ids:
                raise UserError(_("Add at least one prepack line before generating manufacturing orders."))
            for line in batch.line_ids:
                line._generate_manufacturing_order()
            batch.state = "generated"
        return True

    def action_confirm_batch(self):
        for batch in self:
            batch._check_can_edit_workflow()
            if batch.state != "generated":
                raise UserError(_("Only batches with generated orders can be confirmed."))
            if not batch.line_ids:
                raise UserError(_("Add at least one prepack line before confirming the batch."))
            for line in batch.line_ids:
                if not line.mrp_production_id:
                    raise UserError(_("Generate manufacturing orders before confirming the batch."))
                line._confirm_manufacturing_order()
            batch.state = "in_progress"
        return True

    def action_mark_done(self):
        for batch in self:
            if batch.state != "in_progress":
                raise UserError(_("Only batches in progress can be marked done."))
            if batch.state == "cancel":
                raise UserError(_("Cancelled batches cannot be completed."))
            for line in batch.line_ids:
                if not line.mrp_production_id:
                    raise UserError(_("All batch lines must have manufacturing orders before completion."))
                line._complete_manufacturing_order()
            batch.state = "done"
        return True

    def action_cancel(self):
        for batch in self:
            for mo in batch.line_ids.mapped("mrp_production_id").filtered(lambda m: m.state not in ("done", "cancel")):
                mo.action_cancel()
            batch.state = "cancel"
        return True

    def action_reset_to_draft(self):
        for batch in self:
            if batch.line_ids.mapped("mrp_production_id").filtered(lambda m: m.state not in ("cancel",)):
                raise UserError(_("Reset to draft is only allowed after generated manufacturing orders are cancelled."))
            batch.state = "draft"
        return True

    def action_view_manufacturing_orders(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.mrp_production_action")
        action["domain"] = [("id", "in", self.line_ids.mapped("mrp_production_id").ids)]
        action["context"] = {
            "default_prepack_batch_id": self.id,
            "default_origin": self.name,
        }
        return action

    def _check_can_edit_workflow(self):
        for batch in self:
            if batch.state in ("done", "cancel"):
                raise UserError(_("This batch is already closed and cannot be changed."))


class BahmniPrepackBatchLine(models.Model):
    _name = "bahmni.prepack.batch.line"
    _description = "Bahmni Prepack Batch Line"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    batch_id = fields.Many2one(
        "bahmni.prepack.batch",
        required=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(related="batch_id.company_id", store=True)
    product_id = fields.Many2one(
        "product.product",
        string="Finished Pack",
        required=True,
        domain="[('detailed_type', '=', 'product')]",
    )
    product_tmpl_id = fields.Many2one(
        "product.template",
        string="Finished Product Template",
        related="product_id.product_tmpl_id",
        store=True,
        readonly=True,
    )
    bom_id = fields.Many2one(
        "mrp.bom",
        string="Prepack Template",
        required=True,
        domain="[('type', '=', 'normal'), ('product_tmpl_id', '=', product_tmpl_id)]",
    )
    bulk_lot_id = fields.Many2one(
        "stock.lot",
        string="Source Bulk Lot",
        required=True,
        domain="[('id', 'in', available_bulk_lot_ids)]",
    )
    available_bulk_lot_ids = fields.Many2many(
        "stock.lot",
        compute="_compute_available_bulk_lot_ids",
        string="Available Bulk Lots",
    )
    bulk_product_id = fields.Many2one(
        "product.product",
        string="Bulk Product",
        related="bulk_lot_id.product_id",
        store=True,
    )
    package_qty = fields.Integer(
        string="Number of Packs",
        required=True,
        default=1,
    )
    component_qty_per_pack = fields.Float(
        string="Units per Pack",
        compute="_compute_component_metrics",
        digits="Product Unit of Measure",
    )
    component_required_qty = fields.Float(
        string="Bulk Units Required",
        compute="_compute_component_metrics",
        digits="Product Unit of Measure",
    )
    bulk_qty_available = fields.Float(
        string="Lot Stock On Hand",
        compute="_compute_bulk_qty_available",
        digits="Product Unit of Measure",
    )
    has_sufficient_bulk_stock = fields.Boolean(
        string="Has Sufficient Bulk Stock",
        compute="_compute_bulk_qty_available",
    )
    finished_lot_id = fields.Many2one(
        "stock.lot",
        string="Finished Pack Lot",
        readonly=True,
        copy=False,
    )
    mrp_production_id = fields.Many2one(
        "mrp.production",
        string="Manufacturing Order",
        readonly=True,
        copy=False,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("generated", "Orders Generated"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        compute="_compute_state",
    )
    note = fields.Char()

    @api.depends("bom_id", "bulk_lot_id", "package_qty", "product_id")
    def _compute_component_metrics(self):
        for line in self:
            qty_per_pack = 0.0
            if line.bom_id and line.bom_id.product_qty:
                matching_lines = line.bom_id.bom_line_ids
                if line.bulk_lot_id:
                    matching_lines = matching_lines.filtered(
                        lambda bom_line: bom_line.product_id == line.bulk_lot_id.product_id
                    )
                elif len(matching_lines) > 1:
                    matching_lines = self.env["mrp.bom.line"]

                if matching_lines:
                    qty_per_pack = sum(matching_lines.mapped("product_qty")) / line.bom_id.product_qty
            line.component_qty_per_pack = qty_per_pack
            line.component_required_qty = qty_per_pack * line.package_qty

    @api.depends(
        "bulk_lot_id",
        "bulk_lot_id.product_id",
        "batch_id.location_src_id",
        "component_required_qty",
        "company_id",
    )
    def _compute_bulk_qty_available(self):
        Quant = self.env["stock.quant"]
        for line in self:
            qty_available = 0.0
            if line.bulk_lot_id and line.batch_id.location_src_id:
                qty_available = Quant._get_available_quantity(
                    line.bulk_lot_id.product_id,
                    line.batch_id.location_src_id,
                    lot_id=line.bulk_lot_id,
                    strict=True,
                )
            line.bulk_qty_available = qty_available
            line.has_sufficient_bulk_stock = qty_available >= line.component_required_qty

    @api.depends("bom_id", "batch_id.location_src_id", "company_id")
    def _compute_available_bulk_lot_ids(self):
        Quant = self.env["stock.quant"]
        for line in self:
            lots = self.env["stock.lot"]
            if line.bom_id and line.batch_id.location_src_id:
                component_products = line.bom_id.bom_line_ids.mapped("product_id")
                if component_products:
                    quants = Quant.search(
                        [
                            ("product_id", "in", component_products.ids),
                            ("lot_id", "!=", False),
                            ("location_id", "child_of", line.batch_id.location_src_id.id),
                            ("quantity", ">", 0),
                            "|",
                            ("company_id", "=", False),
                            ("company_id", "=", line.company_id.id),
                        ]
                    )
                    lots = quants.mapped("lot_id")
            line.available_bulk_lot_ids = lots

    @api.depends("batch_id.state", "mrp_production_id.state")
    def _compute_state(self):
        for line in self:
            mo = line.mrp_production_id
            if not mo:
                line.state = "draft" if line.batch_id.state == "draft" else line.batch_id.state
            elif mo.state == "done":
                line.state = "done"
            elif mo.state == "cancel":
                line.state = "cancel"
            elif mo.state == "draft":
                line.state = "generated"
            else:
                line.state = "in_progress"

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for line in self:
            if not line.product_id:
                continue
            bom = self.env["mrp.bom"].search(
                [
                    ("product_tmpl_id", "=", line.product_id.product_tmpl_id.id),
                    "|",
                    ("product_id", "=", False),
                    ("product_id", "=", line.product_id.id),
                ],
                order="sequence, id",
                limit=1,
            )
            if bom:
                line.bom_id = bom

    @api.onchange("bom_id")
    def _onchange_bom_id(self):
        for line in self:
            if line.bom_id and line.bom_id.product_id:
                line.product_id = line.bom_id.product_id

    @api.constrains("package_qty")
    def _check_package_qty(self):
        for line in self:
            if line.package_qty <= 0:
                raise ValidationError(_("Number of packs must be greater than zero."))

    @api.constrains("product_id", "bom_id", "bulk_lot_id", "batch_id.location_src_id", "package_qty")
    def _check_line_configuration(self):
        for line in self:
            line._validate_configuration()
            line._validate_bulk_stock()

    def name_get(self):
        result = []
        for line in self:
            result.append((line.id, _("%s x %s") % (line.product_id.display_name, line.package_qty)))
        return result

    def _validate_configuration(self):
        for line in self:
            if not line.product_id or line.product_id.detailed_type != "product":
                raise ValidationError(_("Finished packs must use stockable products."))
            if not line.bom_id:
                raise ValidationError(_("A prepack template is required on every line."))
            bom_product = line.bom_id.product_id or line.bom_id.product_tmpl_id.product_variant_id
            if bom_product != line.product_id:
                raise ValidationError(_("The selected prepack template must manufacture the chosen finished pack."))
            if line.bulk_lot_id and line.bulk_lot_id.product_id not in line.bom_id.bom_line_ids.mapped("product_id"):
                raise ValidationError(_("The source bulk lot product must exist on the selected prepack template."))

    def _validate_bulk_stock(self):
        for line in self:
            if not line.bulk_lot_id or not line.batch_id.location_src_id:
                continue
            if line.component_required_qty <= 0:
                continue
            if line.bulk_qty_available < line.component_required_qty:
                raise ValidationError(
                    _(
                        "Insufficient stock for lot %(lot)s in %(location)s. "
                        "Required: %(required).2f, On hand: %(available).2f."
                    )
                    % {
                        "lot": line.bulk_lot_id.display_name,
                        "location": line.batch_id.location_src_id.display_name,
                        "required": line.component_required_qty,
                        "available": line.bulk_qty_available,
                    }
                )

    def _get_finished_lot_name(self):
        self.ensure_one()
        return self.bulk_lot_id.name

    def _ensure_finished_lot(self):
        self.ensure_one()
        if self.finished_lot_id:
            return self.finished_lot_id
        finished_lot = self.env["stock.lot"].search(
            [
                ("name", "=", self._get_finished_lot_name()),
                ("product_id", "=", self.product_id.id),
                "|",
                ("company_id", "=", False),
                ("company_id", "=", self.company_id.id),
            ],
            limit=1,
        )
        if not finished_lot:
            vals = {
                "name": self._get_finished_lot_name(),
                "product_id": self.product_id.id,
                "company_id": self.company_id.id,
            }
            for field_name in ("expiration_date", "use_date", "removal_date", "alert_date"):
                if field_name in self.bulk_lot_id._fields and field_name in self.env["stock.lot"]._fields:
                    vals[field_name] = self.bulk_lot_id[field_name]
            finished_lot = self.env["stock.lot"].create(vals)
        self.finished_lot_id = finished_lot.id
        return finished_lot

    def _prepare_mo_vals(self):
        self.ensure_one()
        finished_lot = self._ensure_finished_lot()
        return {
            "origin": self.batch_id.name,
            "product_id": self.product_id.id,
            "product_qty": self.package_qty,
            "product_uom_id": self.product_id.uom_id.id,
            "bom_id": self.bom_id.id,
            "company_id": self.company_id.id,
            "date_start": self.batch_id.planned_date,
            "picking_type_id": self.batch_id.picking_type_id.id,
            "location_src_id": self.batch_id.location_src_id.id,
            "location_dest_id": self.batch_id.location_dest_id.id,
            "lot_producing_id": finished_lot.id,
            "prepack_batch_id": self.batch_id.id,
            "prepack_batch_line_id": self.id,
            "prepack_source_lot_id": self.bulk_lot_id.id,
            "prepack_finished_lot_id": finished_lot.id,
        }

    def _sync_mo_from_line(self):
        for line in self:
            mo = line.mrp_production_id
            if not mo or mo.state in ("done", "cancel"):
                continue
            vals = {}
            if mo.product_qty != line.package_qty:
                vals["product_qty"] = line.package_qty
            if vals:
                mo.write(vals)
            if line.bom_id and line.bom_id.product_qty:
                raw_qty_map = {}
                for bom_line in line.bom_id.bom_line_ids:
                    raw_qty_map.setdefault(bom_line.product_id.id, 0.0)
                    raw_qty_map[bom_line.product_id.id] += (
                        bom_line.product_qty / line.bom_id.product_qty
                    ) * line.package_qty
                for move in mo.move_raw_ids.filtered(lambda m: m.state not in ("done", "cancel")):
                    expected_qty = raw_qty_map.get(move.product_id.id)
                    if expected_qty is not None and move.product_uom_qty != expected_qty:
                        move.write({"product_uom_qty": expected_qty})
            for move in mo.move_finished_ids.filtered(lambda m: m.state not in ("done", "cancel")):
                if move.product_id == line.product_id and move.product_uom_qty != line.package_qty:
                    move.write({"product_uom_qty": line.package_qty})
            if "qty_producing" in mo._fields and mo.qty_producing != mo.product_qty:
                mo.write({"qty_producing": mo.product_qty})

    def _generate_manufacturing_order(self):
        for line in self:
            line._validate_configuration()
            line._validate_bulk_stock()
            if line.mrp_production_id and line.mrp_production_id.state != "cancel":
                continue
            mo = self.env["mrp.production"].create(line._prepare_mo_vals())
            line.mrp_production_id = mo.id
        return True

    def _confirm_manufacturing_order(self):
        for line in self:
            line._validate_bulk_stock()
            if not line.mrp_production_id:
                line._generate_manufacturing_order()
            mo = line.mrp_production_id
            if mo.state in ("done", "cancel"):
                continue
            line._sync_mo_from_line()
            if mo.state == "draft":
                mo.action_confirm()
            if hasattr(mo, "action_assign"):
                mo.action_assign()
            line._apply_component_lot()
            line._apply_finished_lot()
        return True

    def _complete_manufacturing_order(self):
        for line in self:
            line._validate_bulk_stock()
            line._sync_mo_from_line()
            line._confirm_manufacturing_order()
            mo = line.mrp_production_id
            if mo.state in ("done", "cancel"):
                continue
            if "qty_producing" in mo._fields and not mo.qty_producing:
                mo.write({"qty_producing": mo.product_qty})
            result = mo.button_mark_done()
            if isinstance(result, dict):
                raise UserError(
                    _("Manufacturing order %s needs manual intervention before it can be completed.")
                    % mo.display_name
                )
            line.finished_lot_id = mo.lot_producing_id
        return True

    def _apply_component_lot(self):
        for line in self:
            mo = line.mrp_production_id
            if not mo:
                continue
            target_moves = mo.move_raw_ids.filtered(
                lambda move: move.state not in ("done", "cancel") and move.product_id == line.bulk_lot_id.product_id
            )
            if not target_moves:
                raise UserError(
                    _("No component move for %s was generated on %s.")
                    % (line.bulk_lot_id.product_id.display_name, mo.display_name)
                )
            for move in target_moves:
                line._write_move_lines(move, line.bulk_lot_id)

    def _apply_finished_lot(self):
        for line in self:
            mo = line.mrp_production_id
            if not mo:
                continue
            finished_lot = line._ensure_finished_lot()
            mo.write(
                {
                    "lot_producing_id": finished_lot.id,
                    "prepack_source_lot_id": line.bulk_lot_id.id,
                    "prepack_finished_lot_id": finished_lot.id,
                }
            )
            target_moves = mo.move_finished_ids.filtered(
                lambda move: move.state not in ("done", "cancel") and move.product_id == line.product_id
            )
            for move in target_moves:
                line._write_move_lines(move, finished_lot)

    def _write_move_lines(self, move, lot):
        self.ensure_one()
        qty = move.product_uom_qty
        first_line = move.move_line_ids[:1]
        if not first_line:
            first_line = self.env["stock.move.line"].create(
                {
                    "move_id": move.id,
                    "product_id": move.product_id.id,
                    "lot_id": lot.id,
                    "location_id": move.location_id.id,
                    "location_dest_id": move.location_dest_id.id,
                    "qty_done": qty,
                }
            )
        else:
            first_line.write(
                {
                    "lot_id": lot.id,
                    "location_id": move.location_id.id,
                    "location_dest_id": move.location_dest_id.id,
                    "qty_done": qty,
                }
            )
        for extra_line in move.move_line_ids - first_line:
            extra_line.write({"lot_id": lot.id, "qty_done": 0})
