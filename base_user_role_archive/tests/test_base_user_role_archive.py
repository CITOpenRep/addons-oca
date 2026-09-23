# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestBaseUserRoleArchive(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        # Test User
        cls.test_user = cls.env.ref("base.user_demo")
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

        archive_access = (
            self.env["ir.model.access"]
            .with_user(self.test_user)
            .get_archive_access("res.partner")
        )
        self.assertTrue(archive_access["can_archive"])
        self.assertTrue(archive_access["can_unarchive"])

    def test_archive_access_revoked(self):
        """Test archive access is denied when group is removed from role."""
        self.test_user.role_line_ids.unlink()

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

        archive_access = (
            self.env["ir.model.access"]
            .with_user(self.test_user)
            .get_archive_access("res.partner")
        )
        self.assertFalse(archive_access["can_archive"])
        self.assertFalse(archive_access["can_unarchive"])
