# utfcpp (vendored)

Header-only C++ UTF-8 library, used engine-wide for UTF-8 validation,
sanitization, and conversion to/from code-point arrays. Wrapped behind the
`ballistica::Utils` UTF-8 methods in `src/ballistica/shared/generic/utils.cc`.

- **Upstream:** https://github.com/nemtrif/utfcpp
- **Pinned version:** v4.1.1 (released 2026-05-20)
- **License:** Boost Software License 1.0 (see `LICENSE`)
- **Files:** `utf8.h` + `utf8/{checked,unchecked,core,cpp11,cpp17,cpp20}.h` —
  vendored pristine (unmodified). Include via `"external/utfcpp/utf8.h"`.

## Updating

Drop in the new `source/` headers from the desired upstream tag and bump the
version above. Header-only, so an update is a clean file swap + rebuild; the
engine only touches it through the `Utils::` wrappers. Keep pristine -- do not
edit these files.
