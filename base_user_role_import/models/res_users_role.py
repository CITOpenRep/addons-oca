# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ResUsersRole(models.Model):
    _inherit = "res.users.role"

    def collect_all_perm_fields(self, perm_fields=None):
        """Include `perm_import` in the synchronized permission fields."""
        perm_fields = perm_fields or {}
        perm_fields.setdefault("perm_import", False)
        return super().collect_all_perm_fields(perm_fields=perm_fields)
