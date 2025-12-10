import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ExtendedSaleOrder(models.Model):
    """
    Extends sale.order with clinical data from Bahmni prescriptions
    """

    _name = "sale.order"
    _inherit = "sale.order"
    encounter_uuid = fields.Char(string="Encounter UUID", index=True)
    location_name = fields.Char(string="Location Name", index=True)
    dispensed_line_count = fields.Integer(
        string="To Dispense",
        compute="_compute_dispensed_line_count",
        store=False,
        help="Number of order lines that need dispensing",
    )

    @api.depends("order_line.dispensed")
    def _compute_dispensed_line_count(self):
        """Compute number of lines that need dispensing"""
        for order in self:
            undispensed_lines = order.order_line.filtered(
                lambda l: not l.dispensed and not l.display_type
            )
            order.dispensed_line_count = len(undispensed_lines)

    # ============ ACTION METHODS ============
    def action_view_dispensing_lines(self):
        """Open view for dispensing lines"""
        self.ensure_one()
        action = self.env.ref("lesotho_sale.action_view_dispensing_lines").read()[0]
        action.update(
            {
                "domain": [("order_id", "=", self.id), ("dispensed", "=", False)],
                "context": {
                    "search_default_filter_undispensed": 1,
                    "default_order_id": self.id,
                    "create": False,
                    "edit": False,
                },
            }
        )
        return action

    def action_mark_all_dispensed(self):
        """Mark all lines in the order as dispensed"""
        self.ensure_one()
        lines_to_dispense = self.order_line.filtered(
            lambda l: not l.dispensed and not l.display_type
        )
        lines_to_dispense.write({"dispensed": True})
        return True

    def action_mark_all_undispensed(self):
        """Mark all lines in the order as not dispensed"""
        self.ensure_one()
        lines_to_undispense = self.order_line.filtered(
            lambda l: l.dispensed and not l.display_type
        )
        lines_to_undispense.write({"dispensed": False})
        return True

    # Add a method to help find orders

    @api.model
    def search_by_encounter_and_customer(self, encounter_uuid, customer_id):
        return self.search(
            [
                ("encounter_uuid", "=", encounter_uuid),
                ("partner_id", "=", customer_id),
                ("state", "=", "draft"),
            ],
            order="create_date desc",
            limit=1,
        )

    # ============ ENCOUNTER/VISIT FIELDS ============
    encounter_uuid = fields.Char(
        string="Encounter UUID", help="Bahmni Encounter UUID", index=True
    )

    visit_uuid = fields.Char(string="Visit UUID", help="Bahmni Visit UUID", index=True)

    location_name = fields.Char(
        string="Location",
        help="Clinic/Location name from Bahmni (e.g., OPD-1, Ward-2)",
        index=True,
    )

    encounter_type = fields.Char(
        string="Encounter Type",
        help="Type of encounter (e.g., Consultation, Admission)",
        index=True,
    )

    # ============ PROVIDER INFORMATION ============
    provider_name = fields.Char(
        string="Provider", help="Prescribing provider name", index=True
    )

    provider_uuid = fields.Char(
        string="Provider UUID", help="Provider UUID from Bahmni"
    )

    # ============ CLINICAL DATA ============
    diagnosis = fields.Text(
        string="Diagnosis/Reason", help="Primary diagnosis or visit reason"
    )

    clinical_notes = fields.Text(
        string="Clinical Notes", help="Additional clinical notes"
    )

    disposition = fields.Char(
        string="Disposition", help="Patient disposition (e.g., Discharged, Admitted)"
    )

    # ============ TIMESTAMP FIELDS ============
    encounter_datetime = fields.Datetime(
        string="Encounter Date/Time", help="Date and time of the encounter"
    )

    # ============ COMPUTED/CONVENIENCE FIELDS ============
    has_clinical_data = fields.Boolean(
        string="Has Clinical Data",
        compute="_compute_has_clinical_data",
        store=True,
        help="True if this sale order has clinical data from Bahmni",
    )

    clinical_data_summary = fields.Char(
        string="Clinical Summary",
        compute="_compute_clinical_data_summary",
        store=True,
        help="Summary of clinical data for quick reference",
    )

    # ============ COMPUTE METHODS ============
    @api.depends("encounter_uuid", "provider_name", "diagnosis", "location_name")
    def _compute_has_clinical_data(self):
        """Check if any clinical data exists"""
        for order in self:
            order.has_clinical_data = any(
                [
                    order.encounter_uuid,
                    order.provider_name,
                    order.diagnosis,
                    order.location_name,
                ]
            )

    @api.depends("encounter_type", "location_name", "provider_name", "diagnosis")
    def _compute_clinical_data_summary(self):
        """Create a summary string for quick reference"""
        for order in self:
            parts = []

            if order.encounter_type:
                parts.append(order.encounter_type)

            if order.location_name:
                parts.append(f"at {order.location_name}")

            if order.provider_name:
                parts.append(f"by {order.provider_name}")

            # Add abbreviated diagnosis if exists
            if order.diagnosis:
                # Take first 50 chars of diagnosis
                diag_short = order.diagnosis[:50]
                if len(order.diagnosis) > 50:
                    diag_short += "..."
                parts.append(f"({diag_short})")

            order.clinical_data_summary = (
                " ".join(parts) if parts else "No clinical data"
            )

    # ============ SEARCH/UTILITY METHODS ============
    @api.model
    def search_by_encounter_uuid(self, encounter_uuid):
        """Find sale order by Bahmni encounter UUID"""
        return self.search([("encounter_uuid", "=", encounter_uuid)], limit=1)

    @api.model
    def search_by_visit_uuid(self, visit_uuid):
        """Find sale order by Bahmni visit UUID"""
        return self.search([("visit_uuid", "=", visit_uuid)], limit=1)

    def get_clinical_data_dict(self):
        """Return clinical data as dictionary for export/API"""
        self.ensure_one()
        return {
            "encounter_uuid": self.encounter_uuid,
            "visit_uuid": self.visit_uuid,
            "location_name": self.location_name,
            "encounter_type": self.encounter_type,
            "provider_name": self.provider_name,
            "provider_uuid": self.provider_uuid,
            "diagnosis": self.diagnosis,
            "clinical_notes": self.clinical_notes,
            "disposition": self.disposition,
            "encounter_datetime": self.encounter_datetime,
            "has_clinical_data": self.has_clinical_data,
            "clinical_summary": self.clinical_data_summary,
        }
