This module extends `base_user_role_extended` to add **archive** and
**unarchive** access control to role-based model permissions.

It adds two new boolean fields to `ir.model.access`:

- **Archive Access** (`perm_archive`): controls whether a user may archive
  records of that model.
- **Unarchive Access** (`perm_unarchive`): controls whether a user may
  unarchive records of that model.

When a role's model access record has these permissions unchecked, the
Archive / Unarchive actions are automatically hidden in the UI (List and
Form view action menus) and blocked at the server level whenever the
user tries to write `active = False/True` on a record.

The enforcement logic follows the same strict role-group pattern as
`base_user_role_extended`: for users with active roles, only the role's
associated group access records are evaluated.
