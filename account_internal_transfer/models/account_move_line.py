##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _reconcile_plan(self, reconciliation_plan):
        # AMLs created inside account.move.write() (which always runs with
        # skip_account_move_synchronization=True) skip the recompute trigger for
        # stored fields like amount_residual.  Those land in the DB as NULL, which
        # the ORM silently reads back as 0.0 — making every new line look already
        # reconciled and causing _reconcile_plan_with_sync to produce no partials.
        # Fix: find any NULL amount_residual rows in the plan and recompute them.
        def _collect_ids(plan):
            ids = []
            for item in plan:
                if hasattr(item, 'ids'):
                    ids.extend(item.ids)
                elif isinstance(item, (list, tuple)):
                    ids.extend(_collect_ids(item))
            return ids

        all_ids = _collect_ids(reconciliation_plan)
        if all_ids:
            self.env.cr.execute(
                "SELECT id FROM account_move_line WHERE id = ANY(%s) AND amount_residual IS NULL",
                (all_ids,),
            )
            null_ids = [r[0] for r in self.env.cr.fetchall()]
            if null_ids:
                self.browse(null_ids)._compute_amount_residual()
        super()._reconcile_plan(reconciliation_plan)
