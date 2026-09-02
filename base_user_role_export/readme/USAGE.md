To use this module:

1. Install this module (depends on `base_user_role`, `base_user_role_extended`,
   and `base_export_manager`).
2. Go to **Settings › Users & Companies › Roles**.
3. Create or open a role.
4. **Verify that the group "Access to export feature" is present in the
   role's implied groups.** This group is added automatically when creating
   a new role; remove it only when export should be explicitly denied.
5. On the **Model Access** tab, set `perm_export = True` on each model line
   that role should be allowed to export.
6. Assign the role to the relevant users and enable it.

Users governed by an active role will only be able to export models for which
their role's model access record has `perm_export` checked **and** the
"Access to export feature" group is implied by their role.
