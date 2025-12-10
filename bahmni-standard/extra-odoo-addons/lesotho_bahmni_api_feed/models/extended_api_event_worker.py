# from odoo import models, api
# import logging

# _logger = logging.getLogger(__name__)

# class ExtendedApiEventWorker(models.Model):
#     _inherit = 'api.event.worker'

#     @api.model
#     def _create_or_update_customer(self, vals):
#         _logger.warning("Lesotho override: _create_or_update_customer() CALLED with %s", vals)
        
#         super()._create_or_update_customer(vals)

#         # Now enforce sex + age
#         partner_ref = vals.get("ref")
#         partner = self.env['res.partner'].search([('ref', '=', partner_ref)], limit=1)

#         if not partner:
#             _logger.warning("Lesotho override: Partner not found for ref %s", partner_ref)
#             return

#         update_vals = {}

#         sex = vals.get("sex")
#         if sex:
#             update_vals["sex"] = sex

#         age = vals.get("age")
#         if age:
#             try:
#                 update_vals["age"] = int(age)
#             except:
#                 _logger.warning("Invalid age received: %s", age)

#         if update_vals:
#             partner.write(update_vals)
#             _logger.info("Lesotho extension applied: %s", update_vals)
#         else:
#             _logger.info("Lesotho override: No updates applied")

from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

class ApiEventWorkerExt(models.Model):
    _inherit = 'api.event.worker'

    @api.model
    def _get_customer_vals(self, vals):
        """
        Extend Bahmni customer values with sex & age
        while preserving original Bahmni logic.
        """
        # _logger.debug("Lesotho Bahmni API Feed: Entering _get_customer_vals with payload: %s", vals)

        # Call Bahmni's implementation first
        customer_vals = super()._get_customer_vals(vals)

        _logger.debug("Lesotho Bahmni API Feed: Base customer_vals from Bahmni: %s", customer_vals)

        # ---- ADD SEX ----
        sex = vals.get("sex")
        if sex:
            customer_vals["sex"] = sex
            _logger.info("Lesotho Bahmni API Feed: Added sex=%s for ref=%s", sex, vals.get("ref"))
        else:
            _logger.debug("Lesotho Bahmni API Feed: No sex field present in payload for ref=%s", vals.get("ref"))

        # ---- ADD AGE ----
        age = vals.get("age")
        if age is not None:
            try:
                customer_vals["age"] = int(age)
                _logger.info("Lesotho Bahmni API Feed: Added age=%s for ref=%s", age, vals.get("ref"))
            except ValueError:
                _logger.warning("Lesotho Bahmni API Feed: Invalid age received (%s) for ref=%s", age, vals.get("ref"))
        else:
            _logger.debug("Lesotho Bahmni API Feed: No age field present in payload for ref=%s", vals.get("ref"))

        _logger.debug("Lesotho Bahmni API Feed: Final customer_vals to be saved: %s", customer_vals)

        return customer_vals
