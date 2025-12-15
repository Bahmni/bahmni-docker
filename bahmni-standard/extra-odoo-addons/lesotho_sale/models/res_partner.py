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

    systolic = fields.Integer(
        string="Systolic BP",
        help="Systolic blood pressure from registration vitals",
        copy=False,
    )

    diastolic = fields.Integer(
        string="Diastolic BP",
        help="Diastolic blood pressure from registration vitals",
        copy=False,
    )

    height = fields.Float(
        string="Height (cm)",
        help="Height in centimeters from registration vitals",
        copy=False,
    )

    weight = fields.Float(
        string="Weight (kg)",
        help="Weight in kilograms from registration vitals",
        copy=False,
    )

    
