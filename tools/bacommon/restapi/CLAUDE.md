# REST API v1 Package Conventions

## Standalone constraint

This package is shipped inside the game (`ba_data/python/bacommon/`). It must
remain standalone — no `baserver` or `bamaster` imports. Define any needed
enums locally, mirroring internal values where necessary.

## IOAttrs / Field conventions

- All fields carry explicit `IOAttrs` storage keys even when the key matches
  the field name. This guards against automated renaming breaking the public
  wire format and allows variable names to diverge from wire names later.
- Use full descriptive names (no short keys) for readability.

## Docstrings

- Response dataclasses should include a `Returned by` line in their docstring
  with a ``:attr:`Endpoint.XXX``` reference to the associated endpoint(s).
- Docstrings must be valid RST (processed by Sphinx via ``make docs``).
  Indented content under a label line requires a blank line before the indented
  block, or use a bullet list or a ``::`` literal block.

## File layout

- `v1/__init__.py` — `Endpoint` StrEnum only.
- `v1/accounts.py` — `ErrorResponse`, `AccountResponse`.
- `v1/workspaces.py` — all `Workspace*` types and `WorkspaceEntryType`.
- Add new resource groups as separate `v1/<resource>.py` files.
- Every submodule must include ``# See CLAUDE.md in this directory for
  contributor conventions.`` as the first comment line (after the license
  header).
