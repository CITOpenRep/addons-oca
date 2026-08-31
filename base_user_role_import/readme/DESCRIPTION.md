This module bridges `base_import_manager` and `base_user_role_extended` to enable role-based import control.

1. It integrates the "Import Access" permission field on model access rights (`ir.model.access`) with user roles.
2. It dynamically enforces the import permission restriction based on the user's active Roles.
3. Supports role policy bypass for superusers.
