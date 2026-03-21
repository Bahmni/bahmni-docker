from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _sync_sale_line_fefo_lot(self):
        for move in self.filtered(lambda m: m.sale_line_id and m.move_line_ids):
            move_lines = move.move_line_ids.filtered("lot_id")
            if not move_lines:
                continue
            move_lines = move_lines.sorted(
                key=lambda line: (
                    move.sale_line_id._get_lot_expiry_key(line.lot_id),
                    line.lot_id.name or "",
                )
            )
            move.sale_line_id._sync_lot_from_reserved_stock(move_lines[0].lot_id)

    def _action_assign(self, force_qty=False):
        moves = super()._action_assign(force_qty=force_qty)
        target_moves = moves or self
        target_moves._sync_sale_line_fefo_lot()
        return moves
