from odoo import models, fields

class ResPartner(models.Model):
    """
    Extends res_partner with patient age and sex
    """
    _inherit = "res.partner"

    sex = fields.Selection([
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')], 
        string="Sex",
        help="Sex of the patient.",
        index=True,
        copy=False,
    )

    age = fields.Integer(
        string="Age",
        help="Age of the patient.",
        index=True,
        copy=False,
    )

    
