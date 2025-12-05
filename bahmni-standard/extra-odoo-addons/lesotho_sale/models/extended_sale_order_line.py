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

    # ============ SPECIAL INSTRUCTIONS ============
    as_needed = fields.Boolean(
        string="PRN", help="Take as needed (Pro Re Nata)", default=False
    )

    administration_instructions = fields.Text(
        string="Administration Instructions",
        help="Special instructions for administration",
    )

    # ============ DATE FIELDS ============
    start_date = fields.Datetime(
        string="Start Date", help="When the medication should start"
    )

    stop_date = fields.Datetime(
        string="Stop Date", help="When the medication should stop"
    )

    expire_date = fields.Datetime(
        string="Expiry Date", help="When the prescription expires"
    )

    # ============ DRUG DETAILS ============
    drug_form = fields.Char(
        string="Drug Form",
        help="Physical form of drug (e.g., Injection, Tablet, Capsule)",
    )

    drug_strength = fields.Char(
        string="Strength", help="Drug strength (e.g., 3 mg/ml, 500 mg)"
    )

    drug_uuid = fields.Char(string="Drug UUID", help="Bahmni Drug UUID for reference")

    # ============ ORDER REFERENCES ============
    external_order_uuid = fields.Char(
        string="External Order UUID",
        help="Bahmni Order UUID for this line item",
        index=True,
    )

    order_number = fields.Char(
        string="Order Number", help="Bahmni Order Number (e.g., ORD-11)", index=True
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
        "frequency", "route", "dose", "duration", "administration_instructions"
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
        "as_needed",
        "administration_instructions",
        "drug_form",
        "drug_strength",
    )
    def _compute_full_prescription_text(self):
        """Create complete prescription instruction text"""
        for line in self:
            parts = []

            # Drug name and details
            drug_parts = []
            if line.product_id:
                drug_parts.append(line.product_id.name)

            if line.drug_form:
                drug_parts.append(f"({line.drug_form}")
                if line.drug_strength:
                    drug_parts.append(f"{line.drug_strength})")
                else:
                    drug_parts.append(")")

            if drug_parts:
                parts.append(" ".join(drug_parts))

            # Dosage
            if line.dose and line.dose_units:
                parts.append(f"{line.dose} {line.dose_units}")

            # Frequency and route
            freq_route = []
            if line.frequency:
                freq_route.append(line.frequency)
            if line.route:
                freq_route.append(f"via {line.route}")

            if freq_route:
                parts.append(" ".join(freq_route))

            # Duration
            if line.duration and line.duration_units:
                parts.append(f"for {line.duration} {line.duration_units}")

            # PRN
            if line.as_needed:
                parts.append("(as needed)")

            # Instructions
            if line.administration_instructions:
                instructions = line.administration_instructions
                # Clean JSON if present
                if instructions.startswith('{"instructions":"'):
                    try:
                        instructions = json.loads(instructions).get(
                            "instructions", instructions
                        )
                    except:
                        pass
                parts.append(f"Instructions: {instructions}")

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
    def clean_administration_instructions(self):
        """Clean JSON format from administration instructions"""
        for line in self:
            if line.administration_instructions:
                instructions = line.administration_instructions
                if instructions.startswith('{"instructions":"'):
                    try:
                        data = json.loads(instructions)
                        line.administration_instructions = data.get(
                            "instructions", instructions
                        )
                    except json.JSONDecodeError:
                        # Leave as is if not valid JSON
                        pass
        return True

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
            "as_needed": self.as_needed,
            "administration_instructions": self.administration_instructions,
            "start_date": self.start_date,
            "stop_date": self.stop_date,
            "expire_date": self.expire_date,
            "drug_form": self.drug_form,
            "drug_strength": self.drug_strength,
            "drug_uuid": self.drug_uuid,
            "external_order_uuid": self.external_order_uuid,
            "order_number": self.order_number,
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
