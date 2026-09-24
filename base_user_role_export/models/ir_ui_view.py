# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class IrUiView(models.Model):
    _inherit = "ir.ui.view"

    def _postprocess_access_rights(self, tree):
        """Disable the 'export all' action based on the user's
        effective model access rights."""
        target_model = tree.get("model_access_rights")
        tree = super()._postprocess_access_rights(tree)

        if not target_model or tree.tag not in ("list", "kanban"):
            return tree

        group_ids = tuple(self.env.user.with_context(role=True)._get_group_ids())
        has_export = bool(
            self.env["ir.model.access"]
            .sudo()
            .search(
                [
                    ("model_id.model", "=", target_model),
                    ("perm_export", "=", True),
                    "|",
                    ("group_id", "=", False),
                    ("group_id", "in", group_ids),
                ],
                limit=1,
            )
        )

        if not has_export:
            tree.set("export_xlsx", "0")

        return tree
