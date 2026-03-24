import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """
    Extends res_partner with patient age and sex
    """

    _inherit = "res.partner"

    sex = fields.Selection(
        [("M", "Male"), ("F", "Female"), ("O", "Other")],
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

    # ============ ALLERGY FIELDS ============
    is_patient = fields.Boolean(
        string="Is Patient",
        default=False,
        help="Indicates if this contact is a patient",
    )

    allergy_summary = fields.Text(
        string="Allergy Summary",
        help="Summary of patient allergies for quick reference",
    )

    # FIX: Change from 'patient_id' to 'partner_id' to match PatientAllergy model
    allergy_ids = fields.One2many(
        "patient.allergy",
        "partner_id",  # Changed from 'patient_id' to 'partner_id'
        string="Allergies",
    )

    has_allergies = fields.Boolean(
        string="Has Allergies",
        compute="_compute_has_allergies",
        store=True,
        help="Indicates if patient has any allergies",
    )

    active_allergy_count = fields.Integer(
        string="Active Allergies",
        compute="_compute_active_allergy_count",
        store=True,
        help="Number of active (non-voided) allergies",
    )

    # ============ COMPUTE METHODS ============
    @api.depends("allergy_ids")
    def _compute_has_allergies(self):
        """Check if patient has any allergies"""
        for partner in self:
            partner.has_allergies = bool(
                partner.allergy_ids.filtered(lambda a: not a.voided)
            )

    @api.depends("allergy_ids", "allergy_ids.voided")
    def _compute_active_allergy_count(self):
        """Count active allergies"""
        for partner in self:
            active_allergies = partner.allergy_ids.filtered(lambda a: not a.voided)
            partner.active_allergy_count = len(active_allergies)

    # ============ UTILITY METHODS ============
    def check_drug_allergy(self, drug_name):
        """
        Check if patient has allergy to a specific drug
        Returns: (has_allergy, allergy_details)
        """
        self.ensure_one()

        if not self.is_patient:
            return (False, None)

        # Search for drug allergies (case-insensitive)
        allergies = self.env["patient.allergy"].search(
            [
                ("partner_id", "=", self.id),  # Changed from patient_id to partner_id
                ("voided", "=", False),
                ("allergen_type", "=", "DRUG"),
                ("allergen_name", "ilike", drug_name),
            ]
        )

        if allergies:
            allergy_details = []
            for allergy in allergies:
                details = {
                    "id": allergy.id,
                    "allergen_name": allergy.allergen_name,
                    "severity": allergy.severity,
                    "reactions": allergy.reactions,
                    "comments": allergy.comments,
                    "date_created": allergy.date_created,
                }
                allergy_details.append(details)

            return (True, allergy_details)

        return (False, None)

    def update_allergy_summary(self):
        """
        Update allergy summary from active allergies
        """
        for partner in self:
            if not partner.is_patient:
                continue

            active_allergies = partner.allergy_ids.filtered(lambda a: not a.voided)

            if not active_allergies:
                partner.allergy_summary = "No known allergies"
                continue

            summaries = []
            for allergy in active_allergies:
                summary = f"{allergy.allergen_name}"
                if allergy.severity:
                    summary += f" ({allergy.severity})"
                if allergy.reactions:
                    # Take first reaction if multiple
                    reactions = allergy.reactions.split(",")
                    if reactions:
                        summary += f": {reactions[0].strip()}"
                summaries.append(summary)

            partner.allergy_summary = "; ".join(summaries)

    def get_allergy_warnings(self, drug_name):
        """
        Get formatted allergy warnings for UI display
        """
        self.ensure_one()

        has_allergy, allergy_details = self.check_drug_allergy(drug_name)

        if not has_allergy:
            return []

        warnings = []
        for allergy in allergy_details:
            warning = {
                "type": "danger",
                "title": f"DRUG ALLERGY: {allergy['allergen_name']}",
                "message": f"Patient has {allergy['severity'].lower() if allergy['severity'] else 'unknown'} allergy to this drug.",
                "details": allergy.get("reactions", "No reaction details"),
                "comments": allergy.get("comments", ""),
                "date_recorded": allergy.get("date_created", ""),
            }
            warnings.append(warning)

        return warnings
