# Copyright 2026 CIT Services
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class ResUsersRole(models.Model):
    _inherit = "res.users.role"

    def collect_all_perm_fields(self, perm_fields=None):
        res = super().collect_all_perm_fields(perm_fields)
        res.setdefault("perm_duplicate", False)
        return res
