import json
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PatientAllergy(models.Model):
    _name = "patient.allergy"
    _description = "Patient Allergy"
    _rec_name = "allergen_name"
    _order = "date_created desc, create_date desc"

    # ============ PATIENT REFERENCE ============
    # IMPORTANT: Use 'partner_id' not 'patient_id' to match res.partner
    partner_id = fields.Many2one(
        "res.partner",
        string="Patient",
        required=True,
        domain=[("is_patient", "=", True)],
        ondelete="cascade",
        index=True,
    )

    # ============ ALLERGY IDENTIFIERS ============
    allergy_uuid = fields.Char(
        string="Allergy UUID",
        required=True,
        index=True,
        help="UUID from OpenMRS/Bahmni",
    )

    # ============ ALLERGY DETAILS ============
    allergen_type = fields.Selection(
        [
            ("DRUG", "Drug"),
            ("FOOD", "Food"),
            ("ENVIRONMENT", "Environment"),
            ("OTHER", "Other"),
        ],
        string="Allergen Type",
        index=True,
    )

    allergen_name = fields.Char(string="Allergen Name", required=True, index=True)

    severity = fields.Selection(
        [
            ("MILD", "Mild"),
            ("MODERATE", "Moderate"),
            ("SEVERE", "Severe"),
            ("LIFE-THREATENING", "Life-threatening"),
        ],
        string="Severity",
        index=True,
    )

    # ============ REACTIONS ============
    reactions = fields.Text(
        string="Reactions", help="Patient reactions to the allergen"
    )

    reactions_json = fields.Text(
        string="Reactions (JSON)", help="Structured reaction data from OpenMRS"
    )

    comments = fields.Text(
        string="Comments", help="Additional comments about the allergy"
    )

    # ============ STATUS & AUDIT ============
    voided = fields.Boolean(
        string="Voided/Deleted",
        default=False,
        index=True,
        help="If true, this allergy has been voided in OpenMRS",
    )

    date_created = fields.Datetime(
        string="Date Created", help="Date when allergy was created in OpenMRS"
    )

    date_voided = fields.Datetime(
        string="Date Voided", help="Date when allergy was voided in OpenMRS"
    )

    # ============ FEED TRACKING ============
    feed_uri = fields.Char(string="Feed URI")
    last_read_entry_id = fields.Char(string="Last Read Entry ID")

    # ============ COMPUTED FIELDS ============
    is_active = fields.Boolean(
        string="Active",
        compute="_compute_is_active",
        store=True,
        index=True,
        help="True if allergy is not voided",
    )

    allergy_summary = fields.Char(
        string="Summary",
        compute="_compute_allergy_summary",
        store=True,
        help="Brief summary of the allergy",
    )

    # ============ CONSTRAINTS ============
    _sql_constraints = [
        ("allergy_uuid_uniq", "unique(allergy_uuid)", "Allergy UUID must be unique!"),
    ]

    # ============ COMPUTE METHODS ============
    @api.depends("voided")
    def _compute_is_active(self):
        for allergy in self:
            allergy.is_active = not allergy.voided

    @api.depends("allergen_name", "severity", "reactions")
    def _compute_allergy_summary(self):
        for allergy in self:
            parts = []
            if allergy.allergen_name:
                parts.append(allergy.allergen_name)
            if allergy.severity:
                parts.append(f"({allergy.severity})")

            if parts:
                allergy.allergy_summary = " ".join(parts)
            else:
                allergy.allergy_summary = "Unknown Allergy"

    # ============ BUSINESS METHODS ============
    @api.model
    def create_or_update_allergy(self, allergy_data):
        """
        Create or update allergy from OpenMRS data
        """
        _logger.info("Processing allergy data: %s", allergy_data.get("allergy_uuid"))

        allergy_uuid = allergy_data.get("allergy_uuid")
        patient_uuid = allergy_data.get("patient_uuid")

        if not allergy_uuid or not patient_uuid:
            _logger.error(
                "Missing required UUIDs: allergy_uuid=%s, patient_uuid=%s",
                allergy_uuid,
                patient_uuid,
            )
            return False

        # Find patient by UUID (assuming patient UUID is stored in 'ref' field)
        # patient = self.env["res.partner"].search(
        #     [("ref", "=", patient_uuid), ("is_patient", "=", True)], limit=1
        # )

        # if not patient:
        #     _logger.warning(
        #         "Patient not found with UUID: %s. Creating stub record.", patient_uuid
        #     )
        #     # Create a stub patient record
        #     patient = self.env["res.partner"].create(
        #         {
        #             "ref": patient_uuid,
        #             "name": f"Patient {patient_uuid[:8]}...",
        #             "is_patient": True,
        #             "active": False,  # Mark as inactive until full sync
        #         }
        #     )
        # Find patient by Reference (removed the strict 'is_patient' requirement)
        patient = self.env["res.partner"].search([("ref", "=", patient_uuid)], limit=1)

        if not patient:
            _logger.warning(
                "Patient not found with Ref: %s. Creating stub record.", patient_uuid
            )
            # Create a stub patient record
            patient = self.env["res.partner"].create(
                {
                    "ref": patient_uuid,
                    "name": f"Patient {patient_uuid[:8]}...",
                    "is_patient": True,
                    "active": False,  # Mark as inactive until full sync
                }
            )
        else:
            # If the patient exists but isn't marked as a patient yet, update them
            if not patient.is_patient:
                patient.is_patient = True

        # Check if allergy already exists
        existing_allergy = self.search([("allergy_uuid", "=", allergy_uuid)], limit=1)

        vals = {
            "partner_id": patient.id,  # Changed from patient_id to partner_id
            "allergy_uuid": allergy_uuid,
            "allergen_type": allergy_data.get("allergen_type"),
            "allergen_name": allergy_data.get("allergen_name", "Unknown Allergen"),
            "severity": allergy_data.get("severity"),
            "reactions": allergy_data.get("reactions"),
            "reactions_json": allergy_data.get("reactions_json", "[]"),
            "comments": allergy_data.get("comments"),
            "voided": str(allergy_data.get("voided", False)).lower() == "true",
            "date_created": allergy_data.get("date_created"),
            "date_voided": allergy_data.get("date_voided"),
            "feed_uri": allergy_data.get("feed_uri"),
            "last_read_entry_id": allergy_data.get("last_read_entry_id"),
        }

        try:
            if existing_allergy:
                existing_allergy.write(vals)
                _logger.info(
                    "Updated allergy: %s for patient: %s", allergy_uuid, patient.name
                )
                allergy_id = existing_allergy.id
            else:
                new_allergy = self.create(vals)
                _logger.info(
                    "Created allergy: %s for patient: %s", allergy_uuid, patient.name
                )
                allergy_id = new_allergy.id

            # Update patient's allergy summary
            patient.update_allergy_summary()

            return allergy_id
        except Exception as e:
            _logger.error(
                "Failed to create/update allergy %s: %s", allergy_uuid, str(e)
            )
            return False

    def action_view_patient(self):
        """Open patient record"""
        self.ensure_one()
        return {
            "name": self.partner_id.name,
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "res_id": self.partner_id.id,
            "view_mode": "form",
            "target": "current",
        }
