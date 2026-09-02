# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import new_test_user
from odoo.tests.common import TransactionCase


class TestIrUiView(TransactionCase):
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

        cls.user_admin = cls.env.ref("base.user_admin")
        cls.user_root = cls.env.ref("base.user_root")
        cls.test_user = new_test_user(
            cls.env,
            login="test_role_user",
            name="Test Role User",
            groups="base.group_user,base.group_erp_manager",
        )
        cls.model_res_partner = cls.env.ref("base.model_res_partner")
        cls.model_res_users = cls.env.ref("base.model_res_users")

        cls.role_partner_manager = cls.env["res.users.role"].create(
            {"name": "Partner Manager Role"}
        )
        cls.env["res.users.role.line"].create(
            {
                "user_id": cls.test_user.id,
                "role_id": cls.role_partner_manager.id,
            }
        )

        cls.env["ir.model.access"].create(
            {
                "name": "partner manager export access",
                "model_id": cls.model_res_partner.id,
                "group_id": cls.role_partner_manager.group_id.id,
                "perm_read": True,
                "perm_write": True,
                "perm_create": False,
                "perm_unlink": False,
                "perm_export": True,
            }
        )
        cls.env["ir.model.access"].create(
            {
                "name": "partner manager no export access",
                "model_id": cls.model_res_users.id,
                "group_id": cls.role_partner_manager.group_id.id,
                "perm_read": True,
                "perm_write": False,
                "perm_create": False,
                "perm_unlink": False,
                "perm_export": False,
            }
        )

    def test_postprocess_access_rights_allowed(self):
        tree = etree.fromstring(
            '<list model_access_rights="res.partner"><field name="name"/></list>'
        )
        processed_tree = (
            self.env["ir.ui.view"]
            .with_user(self.test_user)
            ._postprocess_access_rights(tree)
        )
        self.assertNotEqual(processed_tree.get("export_xlsx"), "0")

    def test_postprocess_access_rights_restricted(self):
        tree = etree.fromstring(
            '<list model_access_rights="res.users"><field name="name"/></list>'
        )
        processed_tree = (
            self.env["ir.ui.view"]
            .with_user(self.test_user)
            ._postprocess_access_rights(tree)
        )
        self.assertEqual(processed_tree.get("export_xlsx"), "0")

    def test_postprocess_access_rights_non_list_kanban(self):
        tree = etree.fromstring(
            '<form model_access_rights="res.users"><field name="name"/></form>'
        )
        processed_tree = (
            self.env["ir.ui.view"]
            .with_user(self.test_user)
            ._postprocess_access_rights(tree)
        )
        self.assertIsNone(processed_tree.get("export_xlsx"))
