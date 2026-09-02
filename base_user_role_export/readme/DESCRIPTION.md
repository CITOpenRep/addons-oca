This module bridges **Base User Role** (`base_user_role`) and
**Base Export Manager** (`base_export_manager`) to enforce role-based export
access control.

When users are governed by roles, export permissions are determined
exclusively by the ``perm_export`` flag on ``ir.model.access`` records that
belong to the user's active role groups.  Any model not covered by such a
record will be hidden from export, regardless of other group memberships.

Additionally, the export action (`export_xlsx` button) in list and kanban views
is dynamically disabled for models where the active role does not explicitly
grant export access.

> **Important:** The Odoo group **"Access to export feature"**
> (``base.group_allow_export``) **must be added to a role's implied groups**
> for the export feature to be available to users assigned that role.
> This group is pre-populated automatically when creating a new role, but
> can be removed when export access is explicitly unwanted.
