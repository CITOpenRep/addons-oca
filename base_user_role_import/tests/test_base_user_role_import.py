# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestBaseUserRoleImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_model = cls.env["res.users"]
        cls.role_model = cls.env["res.users.role"]
        cls.group_model = cls.env["res.groups"]
        cls.access_model = cls.env["ir.model.access"]
        cls.test_group = cls.group_model.create(
            {
                "name": "Test Group for Import",
            }
        )
        cls.group_user = cls.env.ref("base.group_user")

        cls.partner_model = cls.env["ir.model"].search(
            [("model", "=", "res.partner")], limit=1
        )
        cls.partner_access = cls.access_model.create(
            {
                "name": "Test Partner Access",
                "model_id": cls.partner_model.id,
                "group_id": cls.test_group.id,
                "perm_read": True,
                "perm_write": True,
                "perm_create": True,
                "perm_unlink": True,
                "perm_import": False,
            }
        )

        cls.access_model.search(
            [
                ("model_id.model", "=", "res.partner"),
                ("group_id", "in", [cls.group_user.id, cls.test_group.id]),
            ]
        ).write({"perm_import": False})
        cls.test_role = cls.role_model.create(
            {
                "name": "Test Role for Import",
                "implied_ids": [(6, 0, [cls.group_user.id, cls.test_group.id])],
            }
        )

        cls.test_user = cls.user_model.create(
            {
                "name": "Test Import User",
                "login": "test_import_user",
                "groups_id": [(6, 0, [cls.env.ref("base.group_user").id])],
            }
        )

    def test_collect_all_perm_fields(self):
        """Test that collect_all_perm_fields includes perm_import."""
        role = self.env["res.users.role"].new()
        perm_fields = role.collect_all_perm_fields()
        self.assertIn("perm_import", perm_fields)
        self.assertFalse(perm_fields["perm_import"])

    def test_import_access_controls(self):
        self.test_user.write(
            {
                "role_line_ids": [(0, 0, {"role_id": self.test_role.id})],
            }
        )
        self.env.registry.clear_cache()
        with self.assertRaises(AccessError):
            self.access_model.with_user(self.test_user)._check_import_access(
                "res.partner"
            )
        result = (
            self.env["res.partner"].with_user(self.test_user).get_view(view_type="list")
        )
        arch = etree.fromstring(result["arch"])
        self.assertEqual(arch.get("import"), "0")

        self.partner_access.write({"perm_import": True})
        self.test_role._update_role_model_access()
        self.env.registry.clear_cache()
        has_import = self.access_model.with_user(self.test_user)._check_import_access(
            "res.partner"
        )
        self.assertTrue(has_import)
        result = (
            self.env["res.partner"].with_user(self.test_user).get_view(view_type="list")
        )
        arch = etree.fromstring(result["arch"])
        self.assertNotEqual(arch.get("import"), "0")
