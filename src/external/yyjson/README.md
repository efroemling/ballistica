# yyjson (vendored)

High-performance JSON library (single-file C99) used by the engine's JSON
façade in `src/ballistica/shared/generic/`. Read + write, UTF-8 validating,
safe error-as-value API.

- **Upstream:** https://github.com/ibireme/yyjson
- **Pinned version:** 0.12.0 (released 2025-08-18)
- **License:** MIT (see `LICENSE`)
- **Files:** `yyjson.h`, `yyjson.c` — vendored pristine (unmodified).

## Updating

Drop in the new `yyjson.h` + `yyjson.c` from the desired upstream tag and bump
the version above. Because it parses untrusted input, **watch upstream release
notes for security/correctness fixes and pull those promptly**; everything else
is opportunistic. The engine only touches yyjson through the façade
(`shared/generic/json_facade.*`), so upgrades rarely require code changes.

Kept pristine so updates stay a clean two-file swap — do not edit these files.
