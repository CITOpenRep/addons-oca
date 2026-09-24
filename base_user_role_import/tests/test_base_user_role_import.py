# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import Command
from odoo.tests.common import TransactionCase


class TestBaseUserRoleImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        polluted_columns = [
            ("res_partner", "autopost_bills"),
            ("res_users", "notification_type"),
        ]
        for table, column in polluted_columns:
            cls.env.cr.execute(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='{table}' AND column_name='{column}'
            """)
            if cls.env.cr.fetchone():
                cls.env.cr.execute(
                    f"ALTER TABLE {table} ALTER COLUMN {column} DROP NOT NULL"
                )

        cls.test_group_1 = cls.env["res.groups"].create({"name": "Test Group 1"})
        cls.test_group_2 = cls.env["res.groups"].create({"name": "Test Group 2"})

        user_vals = {
            "name": "Test User",
            "login": "test_user_import_role",
            "groups_id": [
                Command.set([cls.test_group_1.id, cls.env.ref("base.group_user").id])
            ],
            "bypass_role_policy": False,
        }
        cls.test_user = cls.env["res.users"].create(user_vals)

        cls.model_res_partner = cls.env["ir.model"]._get_id("res.partner")

        cls.env["ir.model.access"].search(
            [("model_id", "=", cls.model_res_partner)]
        ).write({"perm_import": False})

        cls.role1 = cls.env["res.users.role"].create(
            {
                "name": "Role 1",
                "group_id": cls.test_group_1.id,
            }
        )
        cls.role2 = cls.env["res.users.role"].create(
            {
                "name": "Role 2",
                "group_id": cls.test_group_2.id,
            }
        )

        cls.access_group_1 = cls.env["ir.model.access"].create(
            {
                "name": "Access Group 1",
                "model_id": cls.model_res_partner,
                "group_id": cls.test_group_1.id,
                "perm_read": True,
                "perm_import": False,
            }
        )

        cls.access_group_2 = cls.env["ir.model.access"].create(
            {
                "name": "Access Group 2",
                "model_id": cls.model_res_partner,
                "group_id": cls.test_group_2.id,
                "perm_read": True,
                "perm_import": True,
            }
        )

    def _get_tree(self, tag="list", target_model="res.partner"):
        tree = etree.Element(tag)
        if target_model:
            tree.set("model_access_rights", target_model)
        return tree

    def test_ir_ui_view_bypass_role_policy_no_import(self):
        self.test_user.bypass_role_policy = True
        tree = self._get_tree()
        processed_tree = (
            self.env["ir.ui.view"]
            .with_user(self.test_user)
            ._postprocess_access_rights(tree)
        )
        self.assertEqual(processed_tree.get("import"), "0")

    def test_ir_ui_view_bypass_role_policy_with_import(self):
        self.test_user.bypass_role_policy = True
        self.test_user.write({"groups_id": [Command.link(self.test_group_2.id)]})
        tree = self._get_tree()
        processed_tree = (
            self.env["ir.ui.view"]
            .with_user(self.test_user)
            ._postprocess_access_rights(tree)
        )
        self.assertNotIn("import", processed_tree.attrib)

    def test_ir_ui_view_with_active_roles_no_import(self):
        self.test_user.write(
            {
                "role_line_ids": [
                    Command.create(
                        {
                            "role_id": self.role1.id,
                            "is_enabled": True,
                        }
                    )
                ]
            }
        )

        tree = self._get_tree()
        processed_tree = (
            self.env["ir.ui.view"]
            .with_user(self.test_user)
            ._postprocess_access_rights(tree)
        )
        self.assertEqual(processed_tree.get("import"), "0")

    def test_ir_ui_view_with_active_roles_with_import(self):
        self.test_user.write(
            {
                "role_line_ids": [
                    Command.create(
                        {
                            "role_id": self.role2.id,
                            "is_enabled": True,
                        }
                    )
                ]
            }
        )
        tree = self._get_tree()
        processed_tree = (
            self.env["ir.ui.view"]
            .with_user(self.test_user)
            ._postprocess_access_rights(tree)
        )
        self.assertNotIn("import", processed_tree.attrib)

    def test_res_users_role_update_role_model_access(self):
        role = self.env["res.users.role"].create(
            {
                "name": "Role Test Update",
            }
        )
        fields = {"perm_read": True}
        role._update_role_model_access(perm_fields=fields)
        self.assertIn("perm_import", fields)
