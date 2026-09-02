# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def fetch_export_models(self):
        """Return the list of models the current user is allowed to export.

        Enforces exclusive role-based access: only models whose
        ``ir.model.access`` record has ``perm_export = True`` for one of the
        current user's active role groups are returned.

        Falls back to the standard implementation when:
        - the parent method does not exist (``base_export_manager`` not
          installed),
        - the user has the ``bypass_role_policy`` flag set, or
        - the user has no enabled roles.
        """
        if self.env.user.bypass_role_policy:
            return super().fetch_export_models()

        user = self.env.user.sudo()
        roles = user.role_line_ids.filtered(lambda line: line.is_enabled).mapped(
            "role_id"
        )

        if not roles:
            return super().fetch_export_models()

        role_group_ids = tuple(roles.mapped("group_id").ids)
        accessobj = self.env["ir.model.access"].sudo()

        accessobj_ids = accessobj.search(
            [
                ("perm_export", "=", True),
                "|",
                ("group_id", "=", False),
                ("group_id", "in", role_group_ids),
            ]
        )
        return list(set(accessobj_ids.mapped("model_id.model")))
