from odoo import models, _
from odoo.exceptions import UserError


class MrpUnbuild(models.Model):
    _inherit = 'mrp.unbuild'

    def action_unbuild(self):
        """Call the original action, but reword the specific tracking error."""
        try:
            return super().action_unbuild()
        except UserError as e:
            # Get the original message text
            msg = e.name if hasattr(e, 'name') else (e.args[0] if e.args else '')

            original = (
                "Some of your components are tracked, you have to specify a "
                "manufacturing order in order to retrieve the correct components."
            )

            if original in msg:
                # 🔁 Your new wording here
                new_msg = _(
                    "Some components are batch/serial tracked.\n"
                    "Please select the related Prepacking Order so we can load "
                    "the correct batches for each component."
                )
                # Re-raise with new text, hide Python traceback
                raise UserError(new_msg) from None

            # Any other UserError → let it pass as normal
            raise
