from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # NEW FIELDS ONLY
    sex = fields.Selection(
        [("male", "Male"), ("female", "Female"), ("other", "Other")], string="Sex"
    )

    age = fields.Integer(string="Age")
