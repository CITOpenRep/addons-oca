This module extends the `base_user_role_extended` functionality to restrict
the "Duplicate" action for Odoo models.

It adds a new field `perm_duplicate` (Duplicate Access) to `ir.model.access` to control
whether roles/groups have duplicate rights. In the frontend, the module post-processes views
to dynamically inject `duplicate="0"` on form and list views when a user lacks duplication
rights, hiding the duplicate button.
