# Build Blessing

"Blessing" is the engine's code-integrity mechanism: a way to prove
that a shipped build's Python game scripts are the unmodified,
official ones. A build is *blessed* when the hash of its game scripts
has been registered with the master server for that build number and
embedded back into the binary. The runtime can then ask "am I an
unmodified blessed build?" and gate trust-sensitive behavior (score /
leaderboard submission validation, etc.) on the answer.

The single most important and least obvious property is that blessing
is **spinoff-invariant**: blessing ballistica-internal must produce
the *same* hash as the public spinoff (bombsquad) built from the same
commit. Bless once in core, and every downstream spinoff is blessed
for free. When that invariant breaks, it's almost always because a
hashed Python file contains a `BallisticaKit` / `ballisticakit`
literal that spinoff substitution rewrites — see
[The spinoff-invariance invariant](#the-spinoff-invariance-invariant)
below. That exact bug (a docstring literal in `tools/bacommon/app.py`)
broke invariance and was the motivation for writing this doc.

## The master hash (`__MASTER__`)

The core artifact is a single 32-char md5 called the **master hash**.
It is computed at app startup over the *contents* of every `.py` file
shipped in the app's Python directories.

Computation lives in
`src/codegen/bapluscodegen/pyembed/game_hash.py` (`_gmh()`), which
runs on a background thread during startup:

- Walks three dirs from `babase.app.env`:
  `python_directory_user`, `python_directory_app`,
  `python_directory_app_site`.
- Collects every file ending in `.py` (only `.py` — `.pyc` was
  abandoned because prebuilt pyc output is non-deterministic across
  machines; see the long comment in `_gmh`).
- Sorts the file list by unix-normalized path (`\` → `/`) so ordering
  is identical on Windows and POSIX.
- md5's each file's bytes (storing per-file hashes in `oghashes`), and
  md5's the concatenation of those into `oghashes['__MASTER__']`.
- Excludes any filename in `ignore_filenames` — currently just
  `baenv.py` (a per-repo file that legitimately differs / only appears
  in one variant; excluding it keeps the hashes lined up). This is the
  "need to start doing blessings per spinoff" HACK noted in the
  source.

Because `__MASTER__` is an md5 over the concatenated file contents, a
match between two builds is **definitive**: every hashed file is
byte-identical. A single differing byte in any hashed `.py` changes
`__MASTER__`.

The same module's `_get_game_hash()` consumes `__MASTER__` to build
per-score verification hashes the master server can re-derive. That's
the *consumer* of blessing; the rest of this doc is about producing
and validating the master hash itself.

## Runtime plumbing (Python ↔ C++)

```
game_hash.py _gmh()  ──md5 of all .py──▶  oghashes['__MASTER__']
        │
        └─ set_master_hash(hash)  ──▶  C++ PySetMasterHash
                                         (python_methods_plus.cc)
                                         stores calced_blessing_hash()

_baplus.master_hash_dump()  ──▶  C++ PyMasterHashDump
                                  prints  "MHBEGIN|<hash>|MHEND"

plus.cc:
  const char* kBlessingHash = "....";   // embedded at bless time
  PlusFeatureSet::IsUnmodifiedBlessedBuild():
    debug build / ran-commands / custom-scripts / no-embedded-hash
      → not blessed
    else → embedded hash == calced hash
```

- `kBlessingHash` is a string literal compiled into the binary
  (`src/ballistica/plus/plus.cc`, ~line 41). `nullptr` means "no
  embedded hash → not blessed".
- `IsUnmodifiedBlessedBuild()` returns false for debug builds, builds
  where the user has run console commands or used workspaces, or
  builds using a custom app-python dir — then compares the embedded
  `kBlessingHash` against the runtime-calced hash.

## The blessing tool — `tools/batoolsinternal/blessing.py`

Driven via `make bless` / `make blessing-check[-cloud]` etc. Three
modes:

### BLESS (core only)

Guarded by the split-string core check
(`'ballistica' + 'kit' != 'ballisticakit'` → refuse), so it can only
run in ballistica-internal, never a spinoff.

1. `make update format` — formatting affects file bytes, so normalize
   first.
2. Build the headless binary (`make cmake-server-build`, or in cloud
   blessing a binary-only build + staged synced assets).
3. `calc_current_hash()` — run the headless binary with
   `_baplus.master_hash_dump()` and parse `MHBEGIN|…|MHEND`.
4. Register with the master server (`legacy.ballistica.net`,
   `/buildblessing`) for the current build number. If that build
   already has a *different* registered hash, increment the build
   number and retry until a free (or already-matching) build number is
   found.
5. `set_embedded_blessing_hash()` — write the hash into
   `plus.cc`'s `kBlessingHash`.
6. `lazy_increment_build --update-hash-only` — update the
   lazy-build-increment state so it won't re-fire until source changes.

### CHECK (runs in build pipelines; no auth needed)

1. **Assetpin gate** — refuse if any asset-package pin is dev/test
   (`batools.assetpins.do_check`). A build pinned to non-prod assets
   isn't shippable (assets would 404 for others), so the
   blessing-check gate enforces it for free across all callers
   (`make blessing-check[-cloud]`, `android-archive-*`,
   `basn-binaries`, `Jenkinsfile-pushall*`).
2. Build + `calc_current_hash()`.
3. Pass only if calced hash == embedded `kBlessingHash` **and** the
   master server agrees the hash is valid for this build number
   (`/buildblessingcheck`, no auth).

`SKIP_BLESSING_CHECK=1` short-circuits CHECK.

### CLEAR

Wipe the embedded `kBlessingHash` (set to `nullptr`).

### Master server side

Hashes are registered/queried on the **legacy** master server
(`legacy.ballistica.net`):

- `GET /buildblessing?build=N&auth=…` → the registered hash for build
  N (auth required).
- `GET /buildblessingcheck?build=N&hash=…` → `{valid: bool}` (no
  auth — safe for pipelines).
- `POST /buildblessing` (build, hash, auth) → register.

`blessing_auth` comes from the repo's `pconfig/localconfig.json`.

## The spinoff-invariance invariant

This is the crux, and the part that's easy to break silently.

When a spinoff (e.g. bombsquad) is generated, spinoff substitutes
`BallisticaKit` → the project's CamelCase name and `ballisticakit` →
its lowercase name throughout the source. The blessed `kBlessingHash`
in `plus.cc` flows through spinoff unchanged (it's an opaque hex
string), and the spinoff's build must reproduce that exact hash for
its own `blessing-check` to pass.

For that to work, **the set of shipped `.py` files must hash to the
same value in core and in every spinoff** — i.e. they must be
byte-identical after substitution. Since substitution *changes* bytes
wherever it fires, the practical requirement is:

> No hashed `.py` file may contain a `BallisticaKit` / `ballisticakit`
> literal that spinoff substitution would rewrite.

In practice the shipped game scripts avoid hardcoding the app name
(they go through `babase.appname()` and friends), so the substitution
count in hashed files is normally zero and the invariant holds for
free. The danger is a stray literal sneaking into a hashed file —
even in a comment or docstring, since the hash is over raw bytes, not
semantics.

**Which files are hashed?** Anything shipped under the app Python
dirs — game logic (`bascenev1lib`, `bauiv1lib`, …) **and**
`tools/bacommon/` (shared code that ships into the app). `tools/`-only
code that never ships (e.g. `batoolsinternal/`) is *not* hashed, so
literals there are harmless to blessing.

### Worked example (the bug this doc was born from)

`tools/bacommon/app.py` had a docstring reading
``Supervisors such as the `ballisticakit_server` wrapper``. In
bombsquad that became `` `bombsquad_server` `` → different bytes →
different file hash → different `__MASTER__`. bombsquad's calced hash
no longer matched the blessed `kBlessingHash`, so bombsquad failed
`blessing-check` even though internal was blessed. Fix: reword to a
substitution-free phrase ("the headless server-wrapper script"). After
that, both repos produced `__MASTER__ = cecf6399ed636ee0928063ac54c32c6f`.

## Debugging — dump and diff the per-file hashes

`game_hash.py` has a built-in dump behind a secret env var. Set
`BA_HASH_TEST=X95` and the startup hash pass writes every per-file
hash plus `__MASTER__` to
`/Users/ericf/Desktop/<platform.node()>_ballisticakit.txt` (the
`ballisticakit` in the filename is itself spinoff-substituted, so the
bombsquad dump lands at `…_bombsquad.txt`).

Workflow to localize an invariance break:

```bash
# Dump internal's hashes.
BA_HASH_TEST=X95 tools/pcommand test_game_run --timeout 12
grep __MASTER__ ~/Desktop/<node>_ballisticakit.txt

# Dump the spinoff's hashes (after spinoff-upgrade onto the same commit).
cd ~/LocalDocs/bombsquad
BA_HASH_TEST=X95 tools/pcommand test_game_run --timeout 12
grep __MASTER__ ~/Desktop/<node>_bombsquad.txt
```

If the two `__MASTER__` values differ, diff the per-file sections to
find the offending file. The path prefixes differ between repos, so
compare just the *relative* path + hash columns (strip the leading
project dir, sort, diff). The file whose hash differs is the one with
a substitution-affected byte — open it and grep for `ballisticakit` /
`BallisticaKit`.

> Sandbox note: process substitution (`<(…)`) fails under the Claude
> Code sandbox ("/dev/fd: Operation not permitted"). Write the two
> sorted column lists to temp files under `build/tmp/` and `diff`
> those instead.

## Gotchas / checklist

- **Invariance breaks ⇒ look for a substituted literal in a hashed
  `.py`.** Comments and docstrings count — the hash is over bytes.
  bacommon ships into the app and is hashed; tools-only code is not.
- **`tools/bacommon/` is efrosync-shared.** A fix there must be
  propagated to the sibling repos (`make efrosync`, with permission)
  or `efrosync-check` fails and blocks `make update` /
  `spinoff-upgrade`.
- **Spinoff propagation requires push + upgrade.** Spinoffs source
  internal from the *remote*; a local-only commit won't reach
  bombsquad until pushed and `make spinoff-upgrade`'d.
- **Debug builds are never blessed** (`IsUnmodifiedBlessedBuild` short
  -circuits), and running console commands / workspaces / custom app
  scripts un-blesses a build at runtime.
- **Formatting affects hashes** — BLESS runs `make update format`
  first for this reason. A build checked without the same formatting
  state can mismatch.
- **`.py` only, not `.pyc`** — pyc output is non-deterministic across
  machines, so it's deliberately excluded.
