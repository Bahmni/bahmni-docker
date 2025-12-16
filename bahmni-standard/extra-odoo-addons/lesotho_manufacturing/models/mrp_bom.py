from odoo import models, fields

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    type = fields.Selection(default='normal')
