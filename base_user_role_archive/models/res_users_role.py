# Copyright 2026 CIT-Services
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ResUsersRole(models.Model):
    _inherit = "res.users.role"

    def _collect_all_perm_fields(self, perm_fields=None):
        res = super()._collect_all_perm_fields(perm_fields=perm_fields)
        res.update(
            {
                "perm_archive": False,
                "perm_unarchive": False,
            }
        )
        return res
