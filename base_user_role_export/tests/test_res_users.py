# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import new_test_user
from odoo.tests.common import TransactionCase


class TestResUsers(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        polluted_columns = [
            ("res_partner", "autopost_bills"),
            ("res_users", "notification_type"),
        ]
        for table, column in polluted_columns:
            cls.env.cr.execute(
                f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='{table}' AND column_name='{column}'
            """
            )
            if cls.env.cr.fetchone():
                cls.env.cr.execute(
                    f"ALTER TABLE {table} ALTER COLUMN {column} DROP NOT NULL"
                )

        cls.model_res_partner = cls.env.ref("base.model_res_partner")
        cls.model_res_users = cls.env.ref("base.model_res_users")

        cls.user_role = new_test_user(
            cls.env,
            login="export_role_user",
            name="Export Role User",
            groups="base.group_user,base.group_erp_manager",
        )
        cls.user_bypass = new_test_user(
            cls.env,
            login="bypass_role_user",
            name="Bypass Role User",
            groups="base.group_user,base.group_erp_manager",
            bypass_role_policy=True,
        )
        cls.user_no_role = new_test_user(
            cls.env,
            login="no_role_user",
            name="No Role User",
            groups="base.group_user,base.group_erp_manager",
        )

        cls.role = cls.env["res.users.role"].create(
            {"name": "Export Test Role"}
        )
        cls.env["res.users.role.line"].create(
            {
                "user_id": cls.user_role.id,
                "role_id": cls.role.id,
            }
        )

        cls.env["ir.model.access"].create(
            {
                "name": "res.partner export access",
                "model_id": cls.model_res_partner.id,
                "group_id": cls.role.group_id.id,
                "perm_read": True,
                "perm_export": True,
            }
        )
        cls.env["ir.model.access"].create(
            {
                "name": "res.users no export access",
                "model_id": cls.model_res_users.id,
                "group_id": cls.role.group_id.id,
                "perm_read": True,
                "perm_export": False,
            }
        )

    def test_fetch_export_models_role_user(self):
        models = (
            self.env["res.users"]
            .with_user(self.user_role)
            .fetch_export_models()
        )
        self.assertIn("res.partner", models)
        self.assertNotIn("res.users", models)

    def test_fetch_export_models_bypass_user(self):
        models = (
            self.env["res.users"]
            .with_user(self.user_bypass)
            .fetch_export_models()
        )
        self.assertIsInstance(models, list)

    def test_fetch_export_models_no_role_user(self):
        models = (
            self.env["res.users"]
            .with_user(self.user_no_role)
            .fetch_export_models()
        )
        self.assertIsInstance(models, list)
