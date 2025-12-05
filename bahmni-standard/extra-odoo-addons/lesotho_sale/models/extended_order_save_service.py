from odoo import models, api
import json
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class ExtendedOrderSaveService(models.Model):
    """
    Extends OrderSaveService to add clinical and prescription data
    """
    _name = 'order.save.service'
    _inherit = 'order.save.service'

    @api.model
    def create_orders(self, vals):
        """
        Override to add clinical data after original order creation

        1. Original method creates sale order and lines
        2. We add clinical data to sale order
        3. We add prescription data to order lines
        """
        _logger.info("ExtendedOrderSaveService.create_orders called")

        # 1. Call ORIGINAL method first - let it create the basic order
        result = super(ExtendedOrderSaveService, self).create_orders(vals)

        try:
            # 2. Add clinical data
            self._add_clinical_data_to_sale_order(vals)

            # 3. Add prescription data to order lines
            self._add_prescription_data_to_order_lines(vals)

            _logger.info("Successfully added clinical and prescription data")

        except Exception as e:
            # Log error but don't fail - original order creation succeeded
            _logger.error(
                f"Failed to add clinical data, but order was created: {str(e)}",
                exc_info=True
            )

        return result

    @api.model
    def _add_clinical_data_to_sale_order(self, vals):
        """Add clinical encounter data to the newly created sale order"""
        _logger.debug("Adding clinical data to sale order")

        # Get customer reference
        customer_ref = vals.get("customer_id") or vals.get("patientId")
        if not customer_ref:
            _logger.warning("No customer_id or patientId in payload")
            return

        # Find customer
        customer = self.env['res.partner'].search([('ref', '=', customer_ref)], limit=1)
        if not customer:
            _logger.warning(f"Customer not found: {customer_ref}")
            return

        # Find the MOST RECENT sale order for this customer (the one just created)
        sale_order = self.env['sale.order'].search([
            ('partner_id', '=', customer.id),
            ('origin', '=', 'API FEED SYNC'),
            ('state', '=', 'draft')
        ], order='create_date desc', limit=1)

        if not sale_order:
            _logger.warning(f"No draft sale order found for customer: {customer_ref}")
            return

        _logger.info(f"Found sale order to update: {sale_order.name}")

        # Prepare clinical data
        clinical_data = {}

        # Encounter/Vist data
        if vals.get('encounterUuid'):
            clinical_data['encounter_uuid'] = vals['encounterUuid']

        if vals.get('visitUuid'):
            clinical_data['visit_uuid'] = vals['visitUuid']

        if vals.get('locationName'):
            clinical_data['location_name'] = vals['locationName']

        if vals.get('encounterType'):
            clinical_data['encounter_type'] = vals['encounterType']

        # Provider data
        providers = vals.get('providers', [])
        if providers and isinstance(providers, list) and len(providers) > 0:
            provider = providers[0]
            if isinstance(provider, dict):
                if provider.get('name'):
                    clinical_data['provider_name'] = provider['name']
                if provider.get('uuid'):
                    clinical_data['provider_uuid'] = provider['uuid']

        # Clinical notes and diagnosis
        if vals.get('reason'):
            clinical_data['diagnosis'] = vals['reason']

        if vals.get('disposition'):
            clinical_data['disposition'] = vals['disposition']

        # Extract diagnosis from observations if available
        observations = vals.get('observations', [])
        diagnosis_text = self._extract_diagnosis_from_observations(observations)
        if diagnosis_text:
            clinical_data['diagnosis'] = diagnosis_text

        # Encounter date/time
        encounter_timestamp = vals.get('encounterDateTime')
        if encounter_timestamp:
            encounter_date = self._parse_timestamp(encounter_timestamp)
            if encounter_date:
                clinical_data['encounter_datetime'] = encounter_date

        # Only update if we have data
        if clinical_data:
            _logger.info(f"Updating sale order {sale_order.name} with clinical data: {clinical_data}")
            sale_order.write(clinical_data)
        else:
            _logger.info("No clinical data to add")

    @api.model
    def _add_prescription_data_to_order_lines(self, vals):
        """Add prescription details to order lines"""
        _logger.debug("Adding prescription data to order lines")

        drug_orders = vals.get('drugOrders', [])
        if not drug_orders:
            _logger.info("No drug orders in payload")
            return

        # Get customer to find sale order
        customer_ref = vals.get("customer_id") or vals.get("patientId")
        if not customer_ref:
            return

        customer = self.env['res.partner'].search([('ref', '=', customer_ref)], limit=1)
        if not customer:
            return

        # Find the sale order
        sale_order = self.env['sale.order'].search([
            ('partner_id', '=', customer.id),
            ('origin', '=', 'API FEED SYNC'),
            ('state', '=', 'draft')
        ], order='create_date desc', limit=1)

        if not sale_order:
            return

        _logger.info(f"Processing {len(drug_orders)} drug orders for sale order {sale_order.name}")

        updated_count = 0
        for drug_order in drug_orders:
            try:
                if self._update_order_line_with_prescription_data(sale_order, drug_order):
                    updated_count += 1
            except Exception as e:
                _logger.error(f"Failed to update order line for drug order: {e}", exc_info=True)

        _logger.info(f"Updated {updated_count} out of {len(drug_orders)} order lines")

    @api.model
    def _update_order_line_with_prescription_data(self, sale_order, drug_order):
        """Update a single order line with prescription data"""
        # Get order identifiers
        order_uuid = drug_order.get('uuid')
        order_number = drug_order.get('orderNumber')

        if not order_uuid and not order_number:
            _logger.warning("Drug order has no uuid or orderNumber")
            return False

        # Try to find the order line
        order_line = None

        # First try by UUID
        if order_uuid:
            order_line = self.env['sale.order.line'].search([
                ('order_id', '=', sale_order.id),
                ('external_order_id', '=', order_uuid)
            ], limit=1)

        # If not found, try by order number
        if not order_line and order_number:
            order_line = self.env['sale.order.line'].search([
                ('order_id', '=', sale_order.id),
                ('external_order_id', '=', order_number)
            ], limit=1)

        if not order_line:
            _logger.warning(f"Order line not found for drug order: uuid={order_uuid}, number={order_number}")
            return False

        # Prepare prescription data
        prescription_data = {}

        # Order references
        if order_uuid:
            prescription_data['external_order_uuid'] = order_uuid

        if order_number:
            prescription_data['order_number'] = order_number

        # Dosing instructions
        dosing = drug_order.get('dosingInstructions', {})
        if isinstance(dosing, dict):
            if dosing.get('frequency'):
                prescription_data['frequency'] = dosing['frequency']

            if dosing.get('route'):
                prescription_data['route'] = dosing['route']

            if dosing.get('dose') is not None:
                prescription_data['dose'] = float(dosing['dose'])

            if dosing.get('doseUnits'):
                prescription_data['dose_units'] = dosing['doseUnits']

            if dosing.get('asNeeded') is not None:
                prescription_data['as_needed'] = bool(dosing['asNeeded'])

            if dosing.get('administrationInstructions'):
                instructions = dosing['administrationInstructions']
                # Clean JSON format if present
                if instructions.startswith('{"instructions":"'):
                    try:
                        instructions = json.loads(instructions).get('instructions', instructions)
                    except:
                        pass
                prescription_data['administration_instructions'] = instructions

        # Duration
        if drug_order.get('duration') is not None:
            prescription_data['duration'] = int(drug_order['duration'])

        if drug_order.get('durationUnits'):
            prescription_data['duration_units'] = drug_order['durationUnits']

        # Dates
        for date_field, model_field in [
            ('dateActivated', 'start_date'),
            ('effectiveStopDate', 'stop_date'),
            ('autoExpireDate', 'expire_date')
        ]:
            timestamp = drug_order.get(date_field)
            if timestamp:
                date_value = self._parse_timestamp(timestamp)
                if date_value:
                    prescription_data[model_field] = date_value

        # Drug details
        drug = drug_order.get('drug', {})
        if isinstance(drug, dict):
            if drug.get('uuid'):
                prescription_data['drug_uuid'] = drug['uuid']

            if drug.get('form'):
                prescription_data['drug_form'] = drug['form']

            if drug.get('strength'):
                prescription_data['drug_strength'] = drug['strength']

        # Only update if we have data
        if prescription_data:
            _logger.debug(f"Updating order line {order_line.id} with prescription data")
            order_line.write(prescription_data)
            return True

        return False

    @api.model
    def _extract_diagnosis_from_observations(self, observations):
        """Extract diagnosis text from observations array"""
        if not observations or not isinstance(observations, list):
            return None

        diagnoses = []
        for obs in observations:
            if isinstance(obs, dict):
                concept = obs.get('concept', {})
                if isinstance(concept, dict):
                    concept_name = concept.get('name')
                    if concept_name:
                        value = obs.get('value')
                        if value:
                            diagnoses.append(f"{concept_name}: {value}")
                        else:
                            diagnoses.append(concept_name)

        return ', '.join(diagnoses) if diagnoses else None

    @api.model
    def _parse_timestamp(self, timestamp):
        """
        Convert timestamp (milliseconds or seconds) to datetime
        Handles both millisecond and second timestamps
        """
        if not timestamp:
            return None

        try:
            # Convert to integer/float
            if isinstance(timestamp, str):
                timestamp = float(timestamp)

            # Check if timestamp is in milliseconds (> year 2000 in milliseconds)
            if timestamp > 1000000000000:  # After year 2000 in milliseconds
                timestamp = timestamp / 1000.0

            return datetime.fromtimestamp(timestamp)

        except (ValueError, TypeError, OSError) as e:
            _logger.warning(f"Failed to parse timestamp {timestamp}: {e}")
            return None
