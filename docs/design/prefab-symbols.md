# Prefab symbols pipeline

**Description:** How Windows prefab PDBs are archived at publish time and fetched on demand by exe hash, so crash traces from prefab builds symbolicate.

Prefab builds ship stripped-ish binaries via efrocache, but crash reports
from them are only useful if the matching debug symbols can be found later.
The prefab symbols pipeline archives Windows PDBs at publish time, keyed by
the exact exe they pair with, and serves them back through a public endpoint
— enabling both in-game self-symbolication (dbghelp) and offline
symbolication of user-reported traces.

## Flow, end to end

1. **Publish side** — during pubsync's `do_assets` step, after
   `efrocache_update`, the best-effort `push_public_artifacts_publish`
   pcommand (`tools/batoolsinternal/pushpublicartifacts.py`) runs. It pulls
   the four Windows PDBs via the Makefile `_prefab-windows-pdbs` target
   (rules are pubsync-stripped; the same-MSBuild-incremental build keeps each
   PDB's GUID matched to the efrocached exe), stages them as
   `<stem>.<exe_sha256>.pdb` plus a `manifest.json`, and publishes the
   directory to the master server's `push-public-artifacts` archive with the
   build number as the version (on a version conflict it uses
   `max(build, latest+1)`).
2. **Server side** — the archive has 90-day / 10-version retention (expiry
   is automatic). A public, **unauthenticated**
   `GET /api/v1/prefab-symbols/{exe_sha256}` endpoint
   (`bamaster/rest/prefabs.py` in the master-server repo) scans recent
   published archive versions for a filename with the `.{sha}.pdb` suffix
   and returns a signed download URL. The request/response schema lives at
   `tools/bacommon/restapi/v1/prefabs.py`.
3. **Client side** — `make prefab-windows-symbols` runs
   `prefab_symbols_fetch` (`tools/batools/prefabsymbols.py`; MIT/public). It
   sha256s the locally-present prefab exes, queries the endpoint
   (fleet-aware via `BA_FLEET`; prod is `www.ballistica.net`), and drops
   each fetched `.pdb` next to its exe so the game's dbghelp integration can
   self-symbolicate crash traces. It requires the exes to already be present
   — by design: fetch-for-what-you-have guarantees the symbols match.

## PDB naming and the CodeView gotcha

Archived PDBs are named `<CodeView-stem>.<exe_sha256>.pdb`. The stem must be
the name recorded in the exe's **CodeView debug record**, not whatever name
staging happens to give the file: the GUI exe's CodeView record references
`BallisticaKitGeneric.pdb` (its pre-staging-rename name), and an early
version of the pipeline staged/served `BallisticaKit.pdb` instead — dbghelp
never matched it. The Makefile GUI-pdb rules and the `_BINARIES` table in
`pushpublicartifacts.py` now stage and archive under the CodeView stem, so
the fetched file resolves with no rename. (If you ever hand a mismatched pdb
to a tool, renaming it to the CodeView stem fixes matching.)

## Offline symbolication recipe

To symbolicate a user-reported module+offset trace without Windows:

1. In the public repo, `make
   build/prefab/full/windows_x86_64_gui/debug/BallisticaKit.exe` (pulls the
   exe from efrocache) and `make prefab-windows-symbols` (fetches the
   matching PDB).
2. If needed, copy the PDB to its CodeView name (see above).
3. `llvm-symbolizer --obj=BallisticaKit.exe --relative-address <offsets>`
   (e.g. `/opt/homebrew/opt/llvm/bin/llvm-symbolizer` from Homebrew LLVM).

For old builds past the fetch window: the exe comes from efrocache via the
public `.efrocachemap` at the relevant commit; the PDB from the archive by
exe hash, while retention lasts.

## In-game dbghelp details

Two fixes in `platform_windows.cc` matter if you touch the trace formatter
(`FormatWinStackTraceForDisplay`):

- **Symbol search path** — `SymInitialize(proc, NULL, TRUE)` searches only
  the CWD plus `_NT_SYMBOL_PATH`, *not* the exe's directory — so a PDB
  sitting next to the exe was never found. The code now uses
  `SymInitializeW` with an explicit exe-dir+cwd search path, plus
  `SYMOPT_LOAD_LINES | SYMOPT_FAIL_CRITICAL_ERRORS`.
- **Wide-char ModuleName** — the formatter prints real `module+0xoffset`
  via `SymGetModuleInfo64` on both the success and SymFromAddr-failure
  paths (previously the failure path printed an uninitialized address —
  the 0xCC garbage seen in old user reports). Our dbghelp build is
  wide-char: `modinfo.ModuleName` is `WCHAR*` and must go through
  `UTF8Encode`. The mismatch (C4477) is caught only by a real MSVC compile.

**Verifying Windows platform C++:** `make cmake-build` cannot compile the
Windows platform code at all. Verify via the prefab exe make target
(`make build/prefab/full/windows_x86_64_gui/debug/BallisticaKit.exe`), which
runs the real MSVC build (fast when incremental on the Windows build host).

## Future directions

Phase-2 ideas (mac dSYMs via `dsymutil` + tar; Linux release builds with
`-g`) are tracked in the followups notes under Build System.
