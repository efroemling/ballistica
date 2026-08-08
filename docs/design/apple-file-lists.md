# Apple file lists

**Description:** The three hand-maintained file lists that must be updated together whenever Apple source/external dirs or Swift files are added, removed, or renamed.

Apple platform code sits at an awkward intersection of three systems: it
builds only on a remote Mac host (so sources must be *synced there*), its
Swift sources are private (so they must be *kept out of the public repo*),
and its binary external deps are huge and privately-consumed (so they must be
*kept out of the public repo too, by a different mechanism*). Each concern
has its own hand-maintained list, none of them auto-update, and forgetting
one produces a failure far from where you made the change. This doc is the
checklist.

**When it applies:** any add / remove / rename under
`src/external/<apple-binary-dir>` (angle-apple, angle-apple-debug,
openal-apple, …) or of `src/ballistica/base/app_platform/apple/*.swift`.

## The three lists

1. **Cloudshell `ba-apple` env sync filters** —
   `tools/efrotoolsinternal/cloudshell.py`. The Mac cloud build
   (`make mac-cloud-build` and friends) rsyncs the workspace to the Mac
   build host using this env's `filters` list. New `src/external/<dir>`
   entries need an `'--include=/src/external/<dir>'` **before** the
   catch-all `'--exclude=/src/external/*'`, or the directory simply never
   arrives on the build host — and the Xcode build dies with confusing
   errors like `'KHR/khrplatform.h' file not found` or
   `ld: warning: search path '...angle-apple' not found`. (cloudshell.py is
   synced across all sibling repos, but only this repo builds Apple.)

2. **`internal_source_files`** — `pconfig/projectconfig.json`. Apple Swift
   files are private and must be listed here so they are not published to
   the public repo (see `docs/design/spinoff.md` for the public/private
   split machinery). Two failure directions: a *missing* entry leaks source;
   a *stale* entry for a deleted file makes pubsync's staging setup abort
   with `Nonexistent internal_source_files entry: <path>`. Run
   `make update` after editing.

3. **`NO_SYNC_DIRS`** — `tools/batoolsinternal/pubsync.py`. Apple *binary*
   external dirs (angle-apple, angle-apple-debug, openal-apple) must be
   listed so they don't publish to the public `ballistica` repo. Nothing
   public consumes them: the public macOS cmake build uses system desktop GL
   (ANGLE absent, auto-detected) plus homebrew openal-soft, and the only
   xcframework consumer is the private Xcode project (itself NO_SYNC). A
   missing entry nearly shipped a 198MB `OpenALSoft.xcframework` to the
   public repo. Note also that *removing* an already-published path needs a
   manual `git rm` in the public staging clone between pubsync begin and
   push — NO_SYNC only stops future syncs, it doesn't retract history.

## Failure-surface map

Local `make preflight` catches **only one** of the three
(`internal_source_files` consistency, partially — and even there the
stale-entry case surfaces only at pubsync time). The other two fail remotely:

| List | Where the miss surfaces |
|------|-------------------------|
| cloudshell `ba-apple` filters | Cloud CI's Apple-Xcode smoke branch only — Xcode build fails on the Mac host with missing-header / missing-search-path errors. Never caught locally. |
| `internal_source_files` | Stale entries abort pubsync staging setup; missing entries leak private source to public. Not caught by local preflight. |
| `NO_SYNC_DIRS` | Pubsync happily publishes the binaries — the failure mode is a silent leak into the public repo, caught only by inspection. |

All three were missed at once by a single publish during the ANGLE/Metal
Apple migration going public — hence this checklist.

## Mnemonic

When touching Apple files: **sync-to-build** (cloudshell `ba-apple` env),
**keep-source-private** (`internal_source_files`),
**keep-binaries-out-of-public** (`NO_SYNC_DIRS`).

Related: `docs/design/spinoff.md` (public/private split and strip
machinery).
