from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = "product.template"

    elmis_code = fields.Char(
        string="eLMIS Code",
        help="OpenLMIS product code for integration.",
        index=True,
        copy=False,
    )
