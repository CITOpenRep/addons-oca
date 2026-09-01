# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, tools
from odoo.tools import SQL


class IrModelAccess(models.Model):
    _inherit = "ir.model.access"

    @api.model
    @tools.ormcache("self.env.uid", "mode")
    def _get_allowed_models(self, mode="read"):
        """
        Override to enforce exclusive role-based model access.

        When the current user has active roles and is not a bypass user:
          - Query ir.model.access using ONLY the role-associated group IDs
            (populated by ResUsersRole._update_role_model_access).
          - This makes the role group's access rights the sole authority,
            superseding every other group the user belongs to.
          - Global access rules (group_id IS NULL) are still respected as the
            baseline, matching standard Odoo behaviour.

        For bypass users (admin/root) or users with no active roles:
          - Delegates to super() → standard all-groups resolution.
        """
        if self.env.user.bypass_role_policy:
            return super()._get_allowed_models(mode)

        # Check if role_group_ids is passed in context to bypass DB/compute
        if "role_group_ids" in self.env.context:
            role_group_ids = tuple(self.env.context["role_group_ids"])
            if not role_group_ids:
                return super()._get_allowed_models(mode)
        else:
            role_group_ids = tuple(
                self.env.user.with_context(role=True)._get_group_ids()
            )

            if not role_group_ids:
                return super()._get_allowed_models(mode)

        if role_group_ids:
            # Strictly use only the explicitly assigned role groups
            role_group_ids = tuple(role_group_ids)

        # Query ir.model.access restricted strictly to the explicit
        # role groups + global access
        self.flush_model()
        rows = self.env.execute_query(
            SQL(
                """
            SELECT m.model
              FROM ir_model_access a
              JOIN ir_model m ON (m.id = a.model_id)
             WHERE a.perm_%s
               AND a.active
               AND (
                    a.group_id IS NULL OR
                    a.group_id IN %s
                )
            GROUP BY m.model
            """,
                SQL(mode),
                role_group_ids or (None,),
            )
        )
        return frozenset(row[0] for row in rows)

    # Handle access rights changes from the respective groups,
    # such as create, update, and deletion of access rights
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._update_associated_roles()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._update_associated_roles()
        return res

    def unlink(self):
        if self.env.context.get("updating_role_model_access") or self.env.context.get(
            "install_mode"
        ):
            return super().unlink()

        roles = self._get_associated_roles()
        res = super().unlink()
        if roles:
            roles.with_context(
                updating_role_model_access=True
            )._update_role_model_access()
        return res

    def _get_associated_roles(self):
        """
        Find roles where the trans_implied_ids includes the group_ids
        of the current model access records.
        """
        group_ids = self.mapped("group_id").ids
        if not group_ids:
            return self.env["res.users.role"].browse()

        roles = self.env["res.users.role"].search([])
        return roles.filtered(
            lambda r: not set(r.trans_implied_ids.ids).isdisjoint(group_ids)
        )

    def _update_associated_roles(self):
        if self.env.context.get("updating_role_model_access") or self.env.context.get(
            "install_mode"
        ):
            return
        roles = self._get_associated_roles()
        if roles:
            roles.with_context(
                updating_role_model_access=True
            )._update_role_model_access()
