# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestResUsersRole(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.role_model = cls.env["res.users.role"]
        cls.group_model = cls.env["res.groups"]
        cls.access_model = cls.env["ir.model.access"]
        cls.model_res_partner = cls.env.ref("base.model_res_partner")

        cls.test_group = cls.group_model.create(
            {
                "name": "Test Group for Export Sync",
            }
        )
        cls.partner_access = cls.access_model.create(
            {
                "name": "Test Group Partner Access",
                "model_id": cls.model_res_partner.id,
                "group_id": cls.test_group.id,
                "perm_read": True,
                "perm_export": False,
            }
        )
        cls.test_role = cls.role_model.create(
            {
                "name": "Test Role for Export Sync",
                "implied_ids": [(6, 0, [cls.test_group.id])],
            }
        )

    def test_collect_all_perm_fields(self):
        """Test that collect_all_perm_fields includes perm_export."""
        role = self.env["res.users.role"].new()
        perm_fields = role.collect_all_perm_fields()
        self.assertIn("perm_export", perm_fields)
        self.assertFalse(perm_fields["perm_export"])

    def test_update_role_model_access_synchronization(self):
        """Test that _update_role_model_access propagates
        perm_export from implied groups."""
        self.test_role._update_role_model_access()
        role_access = self.access_model.search(
            [
                ("group_id", "=", self.test_role.group_id.id),
                ("model_id", "=", self.model_res_partner.id),
            ]
        )
        self.assertTrue(role_access)
        self.assertFalse(role_access.perm_export)

        self.partner_access.write({"perm_export": True})
        self.test_role._update_role_model_access()
        role_access = self.access_model.search(
            [
                ("group_id", "=", self.test_role.group_id.id),
                ("model_id", "=", self.model_res_partner.id),
            ]
        )
        self.assertTrue(role_access.perm_export)
