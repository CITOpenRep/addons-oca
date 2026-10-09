# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, new_test_user


class TestBaseUserRoleArchive(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        polluted_columns = [
            ("res_partner", "autopost_bills"),
            ("res_users", "notification_type"),
            ("res_users_settings", "calendar_default_privacy"),
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

        cls.test_user = cls.env.ref(
            "base.user_demo", raise_if_not_found=False
        ) or new_test_user(
            cls.env,
            login="test_archive_user",
            name="Test Archive User",
            groups="base.group_user",
        )
        cls.model_res_partner = cls.env.ref("base.model_res_partner")

        # Create a group that grants archive and unarchive access
        cls.group_archive_manager = cls.env["res.groups"].create(
            {"name": "Archive Manager"}
        )
        cls.env["ir.model.access"].create(
            {
                "name": "partner archive manager",
                "model_id": cls.model_res_partner.id,
                "group_id": cls.group_archive_manager.id,
                "perm_read": True,
                "perm_write": True,
                "perm_create": False,
                "perm_unlink": False,
                "perm_archive": True,
                "perm_unarchive": True,
            }
        )

        # Create a group that grants read and write, but NO archive access
        cls.group_no_archive = cls.env["res.groups"].create(
            {"name": "No Archive Partner"}
        )
        cls.env["ir.model.access"].create(
            {
                "name": "partner no archive",
                "model_id": cls.model_res_partner.id,
                "group_id": cls.group_no_archive.id,
                "perm_read": True,
                "perm_write": True,
                "perm_create": False,
                "perm_unlink": False,
                "perm_archive": False,
                "perm_unarchive": False,
            }
        )

    def setUp(self):
        super().setUp()
        self.test_user.role_line_ids.unlink()
        self.env.registry.clear_cache()

    def test_collect_all_perm_fields(self):
        """Test that collect_all_perm_fields includes archive permissions."""
        role = self.env["res.users.role"].new()
        perm_fields = role.collect_all_perm_fields()

        self.assertIn("perm_archive", perm_fields)
        self.assertIn("perm_unarchive", perm_fields)
        self.assertFalse(perm_fields["perm_archive"])
        self.assertFalse(perm_fields["perm_unarchive"])

    def test_archive_access_with_role(self):
        """Test archive access is granted when user's role has the required group."""
        role = self.env["res.users.role"].create(
            {
                "name": "Archive Role",
                "implied_ids": [(4, self.group_archive_manager.id)],
            }
        )
        self.env["res.users.role.line"].create(
            {
                "user_id": self.test_user.id,
                "role_id": role.id,
            }
        )
        self.env.registry.clear_cache()

        access_model = self.env["ir.model.access"].with_user(self.test_user)
        can_archive = access_model._check_archive_access(
            "res.partner", raise_exception=False
        )
        can_unarchive = access_model._check_unarchive_access(
            "res.partner", raise_exception=False
        )
        self.assertTrue(can_archive)
        self.assertTrue(can_unarchive)

    def test_archive_access_revoked(self):
        """Test archive access is denied when group is removed from role."""
        role = self.env["res.users.role"].create(
            {
                "name": "No Archive Role",
                "implied_ids": [(4, self.group_no_archive.id)],
            }
        )
        self.env["res.users.role.line"].create(
            {
                "user_id": self.test_user.id,
                "role_id": role.id,
            }
        )
        self.env.registry.clear_cache()

        access_model = self.env["ir.model.access"].with_user(self.test_user)
        can_archive = access_model._check_archive_access(
            "res.partner", raise_exception=False
        )
        can_unarchive = access_model._check_unarchive_access(
            "res.partner", raise_exception=False
        )
        self.assertFalse(can_archive)
        self.assertFalse(can_unarchive)

    def test_check_archive_access_cached_override(self):
        """Test _check_archive_access_cached and _check_unarchive_access_cached
        from ir_model_access.py enforce role-based context."""
        # 1. Granted via Archive Role
        role_archive = self.env["res.users.role"].create(
            {
                "name": "Cached Archive Role",
                "implied_ids": [(4, self.group_archive_manager.id)],
            }
        )
        role_line = self.env["res.users.role.line"].create(
            {
                "user_id": self.test_user.id,
                "role_id": role_archive.id,
            }
        )
        self.env.registry.clear_cache()

        access_model = self.env["ir.model.access"].with_user(self.test_user)
        self.assertTrue(bool(access_model._check_archive_access_cached("res.partner")))
        self.assertTrue(
            bool(access_model._check_unarchive_access_cached("res.partner"))
        )
        self.assertTrue(access_model._check_archive_access("res.partner"))
        self.assertTrue(access_model._check_unarchive_access("res.partner"))

        # 2. Denied via No Archive Role
        role_no_archive = self.env["res.users.role"].create(
            {
                "name": "Cached No Archive Role",
                "implied_ids": [(4, self.group_no_archive.id)],
            }
        )
        role_line.role_id = role_no_archive.id
        self.env.registry.clear_cache()

        access_model = self.env["ir.model.access"].with_user(self.test_user)
        self.assertFalse(bool(access_model._check_archive_access_cached("res.partner")))
        self.assertFalse(
            bool(access_model._check_unarchive_access_cached("res.partner"))
        )

        with self.assertRaises(AccessError):
            access_model._check_archive_access("res.partner", raise_exception=True)
        with self.assertRaises(AccessError):
            access_model._check_unarchive_access("res.partner", raise_exception=True)
