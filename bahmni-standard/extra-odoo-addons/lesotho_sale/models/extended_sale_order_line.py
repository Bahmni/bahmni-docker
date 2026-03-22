import json
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ExtendedSaleOrderLine(models.Model):
    """
    Extends sale.order.line with prescription details from Bahmni
    """

    _name = "sale.order.line"
    _inherit = "sale.order.line"

    # ============ PRESCRIPTION DOSING FIELDS ============
    frequency = fields.Char(
        string="Frequency",
        help="How often to take (e.g., Thrice a day, Once daily)",
        index=True,
    )

    route = fields.Char(
        string="Route",
        help="Administration route (e.g., Intravenous, Oral, Topical)",
        index=True,
    )

    dose = fields.Float(
        string="Dose", help="Amount per dose (e.g., 3.0, 500.0)", digits=(12, 4)
    )

    dose_units = fields.Char(
        string="Dose Units", help="Units for dose (e.g., mg, ml, tablets)"
    )

    # ============ DURATION FIELDS ============
    duration = fields.Integer(
        string="Duration", help="Duration of treatment (numeric value)"
    )

    duration_units = fields.Char(
        string="Duration Units", help="Units for duration (e.g., Days, Weeks, Months)"
    )

    # ============ NEW FIELDS FROM JAVA SERVICE ============
    num_refills = fields.Integer(
        string="Number of Refills",
        help="Number of times prescription can be refilled",
        default=0,
    )

    # ============ SPECIAL INSTRUCTIONS ============
    as_needed = fields.Boolean(
        string="PRN", help="Take as needed (Pro Re Nata)", default=False
    )

    administration_instructions = fields.Text(
        string="Administration Instructions",
        help="Special instructions for administration",
    )

    # ============ DRUG DETAILS ============
    drug_form = fields.Char(
        string="Drug Form",
        help="Physical form of drug (e.g., Injection, Tablet, Capsule)",
    )

    drug_uuid = fields.Char(string="Drug UUID", help="Bahmni Drug UUID for reference")

    # ============ ORDER REFERENCES ============
    external_order_uuid = fields.Char(
        string="External Order UUID",
        help="Bahmni Order UUID for this line item",
        index=True,
    )

    previous_order_uuid = fields.Char(
        string="Previous Order UUID",
        help="UUID of previous order if this is a revision",
        index=True,
    )

    order_number = fields.Char(
        string="Order Number", help="Bahmni Order Number (e.g., ORD-11)", index=True
    )

    # ============ ADDITIONAL FIELDS ============
    concept_name = fields.Char(string="Concept Name", help="Concept name from Bahmni")

    dispensed = fields.Boolean(
        string="Dispensed",
        help="Whether this medication has been dispensed",
        default=False,
    )

    # ============ COMPUTED FIELDS ============
    has_prescription_data = fields.Boolean(
        string="Has Prescription Data",
        compute="_compute_has_prescription_data",
        store=True,
        help="True if this line has prescription dosing data",
    )

    full_prescription_text = fields.Char(
        string="Prescription",
        compute="_compute_full_prescription_text",
        store=True,
        help="Complete prescription instruction as text",
    )

    prescription_summary = fields.Char(
        string="Prescription Summary",
        compute="_compute_prescription_summary",
        store=True,
        help="Short summary of prescription details",
    )

    # ============ COMPUTE METHODS ============
    @api.depends(
        "frequency",
        "route",
        "dose",
        "duration",
        "num_refills",
        "administration_instructions",
    )
    def _compute_has_prescription_data(self):
        """Check if any prescription data exists"""
        for line in self:
            line.has_prescription_data = any(
                [
                    line.frequency,
                    line.route,
                    line.dose,
                    line.duration,
                    line.num_refills,
                    line.administration_instructions,
                ]
            )

    @api.depends(
        "frequency",
        "route",
        "dose",
        "dose_units",
        "duration",
        "duration_units",
        "num_refills",
        "as_needed",
        "administration_instructions",
        "drug_form",
    )
    def _compute_full_prescription_text(self):
        """Create complete prescription instruction text"""
        for line in self:
            parts = []

            # Drug name
            if line.product_id:
                parts.append(line.product_id.name)

            # Dosage
            if line.dose and line.dose_units:
                parts.append(f"{line.dose} {line.dose_units}")

            # Frequency and route
            if line.frequency:
                parts.append(line.frequency)

            if line.route:
                parts.append(f"via {line.route}")

            # Duration
            if line.duration and line.duration_units:
                parts.append(f"for {line.duration} {line.duration_units}")

            # PRN
            if line.as_needed:
                parts.append("(as needed)")

            # Refills
            if line.num_refills and line.num_refills > 0:
                parts.append(f"with {line.num_refills} refill(s)")

            # Instructions
            if line.administration_instructions:
                parts.append(f"Instructions: {line.administration_instructions}")

            line.full_prescription_text = (
                " ".join(parts) if parts else "No prescription details"
            )

    @api.depends("frequency", "route", "dose", "dose_units")
    def _compute_prescription_summary(self):
        """Create a short summary for display"""
        for line in self:
            parts = []

            if line.dose and line.dose_units:
                parts.append(f"{line.dose}{line.dose_units}")

            if line.frequency:
                parts.append(line.frequency)

            if line.route:
                parts.append(line.route)

            line.prescription_summary = " | ".join(parts) if parts else "-"

    # ============ UTILITY METHODS ============
    def get_prescription_data_dict(self):
        """Return prescription data as dictionary"""
        self.ensure_one()
        return {
            "frequency": self.frequency,
            "route": self.route,
            "dose": self.dose,
            "dose_units": self.dose_units,
            "duration": self.duration,
            "duration_units": self.duration_units,
            "num_refills": self.num_refills,
            "as_needed": self.as_needed,
            "administration_instructions": self.administration_instructions,
            "drug_form": self.drug_form,
            "drug_uuid": self.drug_uuid,
            "external_order_uuid": self.external_order_uuid,
            "previous_order_uuid": self.previous_order_uuid,
            "order_number": self.order_number,
            "concept_name": self.concept_name,
            "dispensed": self.dispensed,
            "full_prescription": self.full_prescription_text,
            "prescription_summary": self.prescription_summary,
        }

    @api.model
    def search_by_external_order_uuid(self, order_uuid):
        """Find order line by Bahmni order UUID"""
        return self.search([("external_order_uuid", "=", order_uuid)], limit=1)

    @api.model
    def search_by_order_number(self, order_number):
        """Find order line by Bahmni order number"""
        return self.search([("order_number", "=", order_number)], limit=1)
        # ============ ALLERGY FIELDS ============

    allergy_checked = fields.Boolean(
        string="Allergy Checked",
        default=False,
        help="Indicates if allergy check was performed",
    )

    has_allergy_warning = fields.Boolean(
        string="Allergy Warning",
        compute="_compute_has_allergy_warning",
        store=True,
        help="True if patient has allergy to this drug",
    )

    allergy_warning_details = fields.Text(
        string="Allergy Details", help="Details of drug allergy if present"
    )

    allergy_override = fields.Boolean(
        string="Allergy Override",
        default=False,
        help="Manual override for allergy warning",
    )

    allergy_override_reason = fields.Text(
        string="Override Reason", help="Reason for overriding allergy warning"
    )

    # ============ COMPUTE METHODS ============
    @api.depends("order_id.partner_id", "product_id.name")
    def _compute_has_allergy_warning(self):
        """Check if drug has allergy warning"""
        for line in self:
            if not line.order_id or not line.order_id.partner_id or not line.product_id:
                line.has_allergy_warning = False
                continue

            # Only check if line hasn't been overridden
            if line.allergy_override:
                line.has_allergy_warning = False
                continue

            # Perform allergy check
            has_allergy, allergy_details = line.order_id.partner_id.check_drug_allergy(
                line.product_id.name
            )

            line.has_allergy_warning = has_allergy

            if has_allergy and allergy_details:
                # Store allergy details
                line.allergy_warning_details = json.dumps(allergy_details, indent=2)
            else:
                line.allergy_warning_details = False

    # ============ BUSINESS METHODS ============
    def check_allergy(self):
        """Manually trigger allergy check"""
        self.ensure_one()

        if not self.order_id or not self.order_id.partner_id or not self.product_id:
            return {
                "warning": {
                    "title": "Missing Information",
                    "message": "Cannot check allergy - missing patient or drug information.",
                }
            }

        has_allergy, allergy_details = self.order_id.partner_id.check_drug_allergy(
            self.product_id.name
        )

        self.allergy_checked = True
        self.allergy_override = False  # Reset override on new check

        if has_allergy:
            self.allergy_warning_details = json.dumps(allergy_details, indent=2)
            self.has_allergy_warning = True

            warnings = self.order_id.partner_id.get_allergy_warnings(
                self.product_id.name
            )

            return {
                "warning": {
                    "title": "DRUG ALLERGY WARNING",
                    "message": f"Patient has allergy to {self.product_id.name}",
                    "details": warnings,
                }
            }
        else:
            self.allergy_warning_details = False
            self.has_allergy_warning = False

            return {
                "info": {
                    "title": "Allergy Check Complete",
                    "message": f"No allergies found for {self.product_id.name}",
                }
            }

    def override_allergy_warning(self):
        """Override allergy warning with reason"""
        self.ensure_one()

        return {
            "name": "Override Allergy Warning",
            "type": "ir.actions.act_window",
            "res_model": "allergy.override.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_line_id": self.id,
                "default_patient_id": self.order_id.partner_id.id
                if self.order_id
                else False,
                "default_drug_name": self.product_id.name if self.product_id else "",
                "default_order_id": self.order_id.id if self.order_id else False,
            },
        }
