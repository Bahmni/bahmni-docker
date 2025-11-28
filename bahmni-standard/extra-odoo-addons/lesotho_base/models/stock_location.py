from odoo import models, fields

class StockLocation(models.Model):
    _inherit = "stock.location"

    elmis_facility_code = fields.Char(
        string="eLMIS Facility Code",
        help="OpenLMIS facility code mapped to this location.",
        index=True,
        copy=False,
    )
