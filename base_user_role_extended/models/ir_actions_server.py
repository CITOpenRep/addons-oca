import logging

from odoo import models

_logger = logging.getLogger(__name__)


class IrActionsServer(models.Model):
    _inherit = "ir.actions.server"

    def run(self):
        """
        Adapts server action execution for role-based users.

        *  Natively, actions without explicit groups crash if the user lacks
        * 'write' access. Strict role policies often remove 'write' access,
        *  breaking basic UI menus. This cleanly injects the user's role groups
        *  into the ORM cache temporarily. `super().run()` reads the cache,
        *  bypassing the hardcoded 'write' check natively.
        *  Avoids overriding the large core method or using stack frame workarounds.
        """
        role_group_ids = self.env.user.with_context(role=True)._get_group_ids()

        if role_group_ids:
            role_groups_tuple = tuple(role_group_ids)
            for action in self.sudo():
                if not action.groups_id:
                    # Inject into cache safely without triggering a database write.
                    self.env.cache.set(
                        action, action._fields["groups_id"], role_groups_tuple
                    )

        try:
            return super().run()
        finally:
            if role_group_ids:
                # Clean up the injected cache to maintain perfect environment state
                for action in self.sudo():
                    if self.env.cache.contains(action, action._fields["groups_id"]):
                        self.env.cache.remove(action, action._fields["groups_id"])
