# Copyright 2026 CIT Services
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, models, tools


class IrModelAccess(models.Model):
    _inherit = "ir.model.access"

    @api.model
    @tools.ormcache("self.env.uid", "model_name")
    def _check_archive_access_cached(self, model_name):
        """
        Override to enforce exclusive role-based model access.
        """
        self = self.with_context(role=True)
        return super()._check_archive_access_cached(model_name)

    @api.model
    @tools.ormcache("self.env.uid", "model_name")
    def _check_unarchive_access_cached(self, model_name):
        """
        Override to enforce exclusive role-based model access.
        """
        self = self.with_context(role=True)
        return super()._check_unarchive_access_cached(model_name)
