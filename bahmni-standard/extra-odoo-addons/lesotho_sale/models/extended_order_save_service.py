import json
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ExtendedOrderSaveService(models.Model):
    """
    Extends OrderSaveService to add prescription data to order lines
    """

    _name = "order.save.service"
    _inherit = "order.save.service"

    @api.model
    def create_orders(self, vals):
        """
        Override to:
        1. Add encounter_uuid to sale order
        2. Add prescription data to order lines
        """
        _logger.info("ExtendedOrderSaveService.create_orders called")

        # Add DEBUG logging to see what we're receiving
        _logger.info("=== DEBUG START ===")
        _logger.info(f"Customer ID: {vals.get('customer_id')}")
        _logger.info(f"Encounter ID: {vals.get('encounter_id')}")
        _logger.info(f"Location Name: {vals.get('locationName')}")

        # Check orders data type
        orders_data = vals.get("orders")
        _logger.info(f"Orders type: {type(orders_data)}")
        if orders_data:
            if isinstance(orders_data, str):
                try:
                    parsed = json.loads(orders_data)
                    _logger.info(
                        f"Orders parsed successfully. Has openERPOrders: {'openERPOrders' in parsed}"
                    )
                except:
                    _logger.info("Orders is string but not valid JSON")
            elif isinstance(orders_data, dict):
                _logger.info(
                    f"Orders is dict. Has openERPOrders: {'openERPOrders' in orders_data}"
                )
        _logger.info("=== DEBUG END ===")

        # 1. First, we need to modify vals to ensure the base class creates the sale order properly
        # But since we can't modify the base class, we'll work around it

        # 2. Call ORIGINAL method first
        try:
            result = super(ExtendedOrderSaveService, self).create_orders(vals)
        except Exception as e:
            _logger.error(f"Base create_orders failed: {e}")
            raise

        try:
            # 3. After base creates order, we need to:
            #    a. Find the created sale order and set encounter_uuid
            #    b. Add prescription data to order lines

            self._update_sale_order_with_encounter_uuid(vals)
            self._add_prescription_data_to_order_lines(vals)

            _logger.info(
                "Successfully updated sale order with encounter_uuid and prescription data"
            )

        except Exception as e:
            # Log error but don't fail - original order creation succeeded
            _logger.error(
                f"Failed to add encounter_uuid or prescription data, but order was created: {str(e)}",
                exc_info=True,
            )

        return result

    @api.model
    def _update_sale_order_with_encounter_uuid(self, vals):
        """Find the sale order created by base class and add encounter_uuid"""
        _logger.debug("Updating sale order with encounter_uuid")

        customer_ref = vals.get("customer_id")
        if not customer_ref:
            _logger.warning("No customer_id in payload")
            return

        customer = self.env["res.partner"].search([("ref", "=", customer_ref)], limit=1)
        if not customer:
            _logger.warning(f"Customer not found: {customer_ref}")
            return

        encounter_uuid = vals.get("encounter_id")
        if not encounter_uuid:
            _logger.warning("No encounter_id in payload")
            return

        location_name = vals.get("locationName")

        # The base class creates sale orders with origin='API FEED SYNC'
        # Find the MOST RECENT draft sale order for this customer
        sale_orders = self.env["sale.order"].search(
            [
                ("partner_id", "=", customer.id),
                ("origin", "=", "API FEED SYNC"),
                ("state", "=", "draft"),
            ],
            order="create_date desc",
            limit=5,
        )

        if not sale_orders:
            _logger.warning(f"No draft sale orders found for customer: {customer_ref}")
            return

        _logger.info(
            f"Found {len(sale_orders)} draft sale orders for customer {customer_ref}"
        )

        # Update all found sale orders with encounter_uuid
        updated_count = 0
        for sale_order in sale_orders:
            # Check if this sale order has order lines from this encounter
            # by looking for order lines with matching external_order_id from our data

            # Get orders data
            orders_data = self._get_orders_data(vals)
            if not orders_data:
                continue

            # Check if any order lines in this sale order match our order IDs
            order_ids = [
                order.get("orderId")
                for order in orders_data.get("openERPOrders", [])
                if order.get("orderId")
            ]
            if order_ids:
                matching_lines = self.env["sale.order.line"].search(
                    [
                        ("order_id", "=", sale_order.id),
                        ("external_order_id", "in", order_ids),
                    ],
                    limit=1,
                )

                if matching_lines:
                    # This is the sale order we want to update
                    update_data = {"encounter_uuid": encounter_uuid}
                    if location_name:
                        update_data["location_name"] = location_name

                    sale_order.write(update_data)
                    _logger.info(
                        f"Updated sale order {sale_order.name} with encounter_uuid: {encounter_uuid}"
                    )
                    updated_count += 1
                    break  # Found the right one, stop searching

        if updated_count == 0:
            _logger.warning(
                f"Could not find sale order with matching order lines for encounter: {encounter_uuid}"
            )
            # Fallback: update the most recent one
            if sale_orders:
                update_data = {"encounter_uuid": encounter_uuid}
                if location_name:
                    update_data["location_name"] = location_name
                sale_orders[0].write(update_data)
                _logger.info(
                    f"Fallback: Updated most recent sale order {sale_orders[0].name} with encounter_uuid"
                )

    @api.model
    def _get_orders_data(self, vals):
        """Parse orders data from vals"""
        orders_data = vals.get("orders")
        if not orders_data:
            return None

        if isinstance(orders_data, str):
            try:
                return json.loads(orders_data)
            except json.JSONDecodeError as e:
                _logger.error(f"Failed to parse orders JSON string: {e}")
                return None
        elif isinstance(orders_data, dict):
            return orders_data
        else:
            _logger.error(f"Orders data is not dict or string: {type(orders_data)}")
            return None

    @api.model
    def _add_prescription_data_to_order_lines(self, vals):
        """Add prescription details to order lines"""
        _logger.debug("Adding prescription data to order lines")

        # Get parsed orders data
        orders_data = self._get_orders_data(vals)
        if not orders_data:
            _logger.info("No orders data found")
            return

        # Get customer
        customer_ref = vals.get("customer_id")
        if not customer_ref:
            return

        customer = self.env["res.partner"].search([("ref", "=", customer_ref)], limit=1)
        if not customer:
            return

        # Find the sale order by encounter UUID (which we just set)
        encounter_uuid = vals.get("encounter_id")
        sale_orders = self.env["sale.order"].search(
            [("partner_id", "=", customer.id), ("encounter_uuid", "=", encounter_uuid)],
            order="create_date desc",
        )

        if not sale_orders:
            _logger.warning(
                f"No sale order found with encounter_uuid: {encounter_uuid}"
            )
            # Try to find by order lines instead
            self._add_prescription_data_by_order_ids(vals, customer)
            return

        # Process each sale order (should usually be just one)
        for sale_order in sale_orders:
            orders_list = orders_data.get("openERPOrders", [])
            _logger.info(
                f"Processing {len(orders_list)} orders for sale order {sale_order.name}"
            )

            updated_count = 0
            for order_data in orders_list:
                try:
                    if self._update_order_line_with_prescription_data(
                        sale_order, order_data
                    ):
                        updated_count += 1
                except Exception as e:
                    _logger.error(f"Failed to update order line: {e}", exc_info=True)

            _logger.info(
                f"Updated {updated_count} out of {len(orders_list)} order lines in sale order {sale_order.name}"
            )

    @api.model
    def _add_prescription_data_by_order_ids(self, vals, customer):
        """Alternative method: find order lines by external_order_id when we can't find sale order by encounter_uuid"""
        orders_data = self._get_orders_data(vals)
        if not orders_data:
            return

        orders_list = orders_data.get("openERPOrders", [])
        _logger.info(
            f"Processing {len(orders_list)} orders by order IDs for customer {customer.name}"
        )

        updated_count = 0
        for order_data in orders_list:
            order_uuid = order_data.get("orderId")
            if not order_uuid:
                continue

            # Find order line by external_order_id
            order_lines = self.env["sale.order.line"].search(
                [("external_order_id", "=", order_uuid)], order="create_date desc"
            )

            for order_line in order_lines:
                # Verify this order line belongs to the right customer
                if order_line.order_id.partner_id.id == customer.id:
                    try:
                        if self._update_single_order_line(order_line, order_data):
                            updated_count += 1
                            break  # Found the right one
                    except Exception as e:
                        _logger.error(
                            f"Failed to update order line {order_uuid}: {e}",
                            exc_info=True,
                        )

        _logger.info(
            f"Updated {updated_count} out of {len(orders_list)} order lines by order IDs"
        )

    @api.model
    def _update_order_line_with_prescription_data(self, sale_order, order_data):
        """Update a single order line with prescription data"""
        order_uuid = order_data.get("orderId")

        if not order_uuid:
            _logger.warning("Order data has no orderId")
            return False

        # Find the order line in this sale order
        order_line = self.env["sale.order.line"].search(
            [("order_id", "=", sale_order.id), ("external_order_id", "=", order_uuid)],
            limit=1,
        )

        if not order_line:
            _logger.debug(
                f"Order line not found in sale order {sale_order.name} for order: {order_uuid}"
            )
            return False

        return self._update_single_order_line(order_line, order_data)

    @api.model
    def _update_single_order_line(self, order_line, order_data):
        """Update prescription data on a single order line"""
        # Prepare prescription data
        prescription_data = {}

        # Map fields from order data to model fields
        field_mapping = {
            "previousOrderId": "previous_order_uuid",
            "conceptName": "concept_name",
            "dose": "dose",
            "doseUnits": "dose_units",
            "frequency": "frequency",
            "route": "route",
            "administrationInstructions": "administration_instructions",
            "duration": "duration",
            "durationUnits": "duration_units",
            "numRefills": "num_refills",
            "asNeeded": "as_needed",
            "drugForm": "drug_form",
        }

        # Map the data
        for json_field, model_field in field_mapping.items():
            value = order_data.get(json_field)
            if value is not None:
                # Handle special conversions
                if json_field == "asNeeded":
                    prescription_data[model_field] = str(value).lower() == "true"
                elif json_field == "dose" and value is not None:
                    try:
                        prescription_data[model_field] = float(value)
                    except (ValueError, TypeError):
                        _logger.warning(f"Invalid dose value: {value}")
                elif json_field in ["duration", "numRefills"] and value is not None:
                    try:
                        prescription_data[model_field] = int(value)
                    except (ValueError, TypeError):
                        _logger.warning(f"Invalid {json_field} value: {value}")
                else:
                    prescription_data[model_field] = value

        # Clean administration instructions if it's JSON
        admin_instructions = prescription_data.get("administration_instructions")
        if (
            admin_instructions
            and isinstance(admin_instructions, str)
            and admin_instructions.startswith('{"instructions":"')
        ):
            try:
                instructions_json = json.loads(admin_instructions)
                prescription_data["administration_instructions"] = (
                    instructions_json.get("instructions", admin_instructions)
                )
            except json.JSONDecodeError:
                pass

        # Only update if we have data
        if prescription_data:
            _logger.debug(
                f"Updating order line {order_line.id} with: {prescription_data}"
            )
            order_line.write(prescription_data)
            return True

        return False
