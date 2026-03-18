from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    prepack_batch_id = fields.Many2one(
        "bahmni.prepack.batch",
        string="Prepack Batch",
        readonly=True,
        copy=False,
    )
    prepack_batch_line_id = fields.Many2one(
        "bahmni.prepack.batch.line",
        string="Prepack Batch Line",
        readonly=True,
        copy=False,
    )
    prepack_source_lot_id = fields.Many2one(
        "stock.lot",
        string="Source Bulk Lot",
        readonly=True,
        copy=False,
    )
    prepack_finished_lot_id = fields.Many2one(
        "stock.lot",
        string="Finished Pack Lot",
        readonly=True,
        copy=False,
    )
