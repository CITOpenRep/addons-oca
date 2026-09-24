# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class IrUiView(models.Model):
    _inherit = "ir.ui.view"

    def _get_import_group_ids(self):
        """Get group IDs representing active user roles for import check."""
        user = self.env.user
        if user.bypass_role_policy:
            return super()._get_import_group_ids()

        active_roles = user.role_line_ids.filtered(lambda r: r.is_enabled).mapped(
            "role_id"
        )
        if active_roles:
            return active_roles.mapped("group_id").ids

        return super()._get_import_group_ids()
