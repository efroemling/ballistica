# Android: serving ba_data directly from the APK

**Description:** How Android serves ba_data straight from the installed APK — zipimport pyc rules, stored-entry mmap spans, and the packaging gotchas that silently break either.

On Android nothing under `ba_data` (or `pylib`, the bundled CPython
stdlib) is ever extracted to disk. The APK is a zip; Python imports out
of it via `zipimport`, and bundled asset blobs are read as memory spans
out of one whole-apk memory-map. There is no first-launch extraction
wait, no doubled on-device copy, and the pre-engine phase of a launch is
a `mkdir` plus three `stat` calls.

Everything staged for Android lands under `assets/ballistica_files/` in
the APK (`tools/batools/staging.py`, `_parse_android_args`). Two
`const bool`s in `platform_android.cc` gate the runtime side —
`kUsePythonFromApk` and `kUseAssetsFromApk` — and every other platform
keeps its plain-directory behavior through the same code paths.

## Python from the APK

`PlatformAndroid` overrides three `Platform` virtuals
(`Get{App,Site}PythonDirectoryMonolithicOverride`,
`GetPylibDirectoryMonolithicOverride`; default `nullopt` = ordinary
dirs) to return paths *into* the apk, e.g.
`<apk>/assets/ballistica_files/ba_data/python`. `core_python.cc`
consumes them for the stdlib module-search-path, the baenv bootstrap
prepend, and the explicit `app_python_dir`/`site_python_dir` passed to
`baenv.configure()`. The apk path itself comes from Java via JNI
(`fromNativeGetPackageCodePathString` →
`PlatformAndroid::GetPackageCodePath`). `sys.path` ordering is unchanged
from the extracted-files era: mods dir, app python, site-packages,
pylib.

zipimport accepts such into-the-archive paths natively, and so does the
meta-scan (it is loader-based and handles archives).

### The pyc rules

zipimport never writes bytecode, so without shipped pycs every import
recompiles on every launch. The pycs it will actually *use* are narrowly
constrained:

- **Side-by-side layout only** (`foo.pyc` beside `foo.py`).
  `__pycache__/` entries inside an archive are ignored outright. A pyc
  is preferred over its `.py`.
- **Timestamp-invalidated pycs do not work.** They validate against the
  `.py` zip entry's DOS timestamp, and APK tooling normalizes entry
  timestamps — so they are *silently* rejected and the source recompiles
  every launch. Nothing logs.
- **PEP 552 `UNCHECKED_HASH` pycs load unconditionally.** This is the
  required shape.
- **Keep the `.py` alongside.** pyc-only imports work but lose traceback
  source lines.
- **Compile at the device interpreter's optimization level.** The
  embedded interpreter runs at level 0 in debug builds and 1 in release
  (`core_python.cc`); zipimport ignores the runtime `-O` state when
  picking a pyc, and compile-time `assert` stripping makes a mismatch
  silent. Staging passes `optimize=` per build type.
- `sys.pycache_prefix` (baenv's pyc dir) is orthogonal — it neither
  blocks in-archive pyc reads nor caches anything for zip imports.

### Staging the pycs (`batools/_pycstage.py`)

`update_pycs()` runs from staging's Android leg
(`include_payload_pycs`). Its design goals are determinism and a
near-free no-op pass:

- Emits unchecked-hash pycs with a root-relative `dfile`, so bytes are
  deterministic and `co_filename` is a clean relative path.
- Freshness is tracked by **mtime equality**: each pyc's mtime is pinned
  to its source's, so an up-to-date tree verifies with pure `stat` calls
  (milliseconds for ~1000 files). Orphan pycs are pruned.
- A root `.pycstamp` records the interpreter's bytecode magic number and
  the optimize level; a change to either forces full regeneration
  despite fresh-looking timestamps. (It is a dotfile so it never ships.)
- Staging refuses to run under a host Python whose version differs from
  the bundled one (`PYVER`) — such pycs would be unloadable.
- The staging rsyncs carry `--filter='P *.pyc'` on Android so their
  delete-excluded passes don't wipe the generated pycs.

### Packaging: stored, not deflated

`build.gradle` sets `aaptOptions.noCompress '.py', '.pyc'`. Deflated
Python costs a consistent ~0.4–0.5s of warm boot (every import
decompresses, and the boot meta-scan touches every entry); stored
entries boot on par with extracted files. Stored entries grow the
*on-disk* APK but not the Play download (Play compresses transport), and
total device footprint still shrinks because nothing is extracted.

### What modders and shipped code see

- **Overrides still work.** Shadowing is decided by `sys.path` order
  (mods dir first); the in-archive pyc preference is entry-local.
  Override granularity (top-level module/package) is unchanged.
- **File access from shipped Python is archive-safe.** The only non-`.py`
  payload files are read through `importlib.resources` (which
  materializes a temp file when a real path is needed, as certifi does
  for its CA bundle). `__file__` uses are display/compare-only.
  `create_user_system_scripts()` was the one real break and now extracts
  from the archive. Traceback source lines come through the loader's
  `get_source()`.
- There are no compiled extension modules in site-packages.

## Asset blobs from the APK

### AssetBlob: spans, not paths

All asset loading goes through `AssetBlob` (`base/assets/asset_blob.h`):
a read-only `(data, size)` span plus ownership of its backing. Parsers
never care where bytes live. Three backings:

- **mapped** — whole-file memory-map of a loose file (clean, evictable
  pages); unmapped on release. `Platform::MapFileReadOnly`/`UnmapFile`
  abstract this (POSIX `mmap` by default; Windows uses
  `CreateFileMapping`/`MapViewOfFile`).
- **heap** — plain read into owned bytes; the fallback for unmappable
  files.
- **borrowed** — a span into memory someone longer-lived owns: the
  boot-time apk mapping.

This is a win on every platform, not just Android, and it fits every
consumer: texture/mesh/collision/json loaders are read-whole-then-parse,
and both audio paths (decode-whole SFX and streaming music) run vorbisfile
over a memory cursor (`base/audio/ogg_blob_source.h`), so music streams
straight out of the mapping.

### One mapping, many spans (`AssetArchive`)

`base/assets/asset_archive.{h,cc}` maps the **whole apk once** at boot
and indexes its zip central directory. `AssetBlob::FromFile` resolves
`<apk>/<entry>` paths to borrowed spans. One mapping plus pointer math —
never per-blob mmaps — so zip-entry alignment never matters for
*mapping*. The archive is mounted from the `Assets` constructor when
`Platform::GetBundledAssetsArchiveInfo()` returns a value. Only
**stored** entries can be served (lookups of deflated entries fail); zip64
archives are rejected.

Bundled CAS blobs are staged as `<hash>.bablob` (`kBundledCasBlobSuffix`)
with `noCompress '.bablob'`. The suffix exists only because aapt's
`noCompress` is suffix-matched and CAS names are extension-less; a
whole-APK `noCompress` would store everything raw for no benefit.
`ba_data/manifest.json` is stored too (`noCompress
'ba_data/manifest.json'` — aapt matching is *endsWith*, so that is the
narrowest expressible rule). Python-side bundle access goes through
native bindings (`bundled_cas_blob_size`, `bundled_cas_blob_bytes`,
`bundled_asset_manifest_text`) that work for both directory and archive
backings, so all platforms share one code path.

### Alignment discipline

The real cost of spans: `fread`-based parsers copied implicitly, span
parsers must not. **Treat a blob as unaligned bytes** — stored zip
entries are 4-byte aligned at best — and read multi-byte fields with
memcpy-style accesses (`AssetBlob::ReadAt`, the sequential
`AssetBlobReader`), never by casting interior pointers to struct or int
types. The zip index parser follows the same rule. Any new parser over
blobs must too.

(The legacy dds/pvr/ktx texture loaders were never converted; current
pipelines ship only ktx2, so they are deletion candidates rather than
conversion targets. Runtime-written sound peak-cache files stay plain
files by design.)

## Gotchas that fail silently

- **JNI-only Java methods need `@Keep`.** Release builds run R8, which
  strips methods only native code calls. A missing annotation on the
  apk-path getter made *release* builds die in `Py_InitializeFromConfig`
  ("Failed to import encodings") while debug worked. The C++ side now
  `FatalError`s on a missing method rather than returning an empty
  string.
- **`.bablob` is never a content extension.** Loaders must not infer
  format from a blob's name. The path check only answers "is this a CAS
  blob" (bare hash or blob suffix); the parser is then chosen from the
  blob's **content magic bytes** (`OpenCasTextureBlob` in
  `texture_asset.cc`; `SoundAsset`'s `.ogg` guard exempts the suffix).
  A future container format is one new magic case.
- **Bundled-blob serving is only exercised on a true fresh install.** A
  warm writable cache serves the ideal texture flavor from bare-hash
  cache paths, and even a broken bundle self-heals visually once
  downloads land. Verify any change here with an **uninstall/reinstall**.
- **Whatever thread first steps the engine is the main thread forever.**
  `BallisticaContext.updateNativeState()` runs `nativeInit()` on its
  caller's thread. The files-dir prep runs on a background thread, so its
  completion must be posted with `runOnUiThread(...)`; calling straight
  through marks the throwaway thread "main" and the next step from the
  real UI thread dies on `StartApp`'s main-thread precondition.
- **The boot `ba_data`-directory sanity check** in `core.cc` only runs
  when `GetBundledAssetsArchiveInfo()` is empty — with archive serving
  the directory legitimately does not exist.

## Upgrading from the extraction era

Older versions extracted everything to `noBackupFilesDir` on first
launch. `BallisticaActivity.syncAssets()` is now just a background
files-dir prep: ensure `ballistica_files` exists (native code `chdir`s
into it), then **prune-if-encountered** the legacy `ba_data`, `pylib`,
and `payload_info`. The prune is idempotent, so a device arriving from
any old version at any future date self-cleans, and the engine's pycache
upkeep then clears the now-orphaned extracted-era pycs. Steady state is
three `stat` calls and no prune log lines.

## Measuring

On-device numbers for this system were gathered with
`test_game_run --platform android --release` plus automation `--exec`
probes — a workflow that needs no rebuilds for pure-measurement
iteration. Boot comparisons should be warm, release, and averaged over
several runs; debug builds and cold first boots swamp the differences
that matter here.
