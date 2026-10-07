# BombSquad Flatpak

This directory holds everything needed to package BombSquad as a Flatpak
(`net.froemling.bombsquad`), both for local/CI test builds and for
publishing on [Flathub](https://flathub.org).

There is one manifest, `net.froemling.bombsquad.yml`, used two ways:

- **Local / CI builds** use it as-is and build straight from the working
  tree. They produce a `.flatpak` bundle you can install by hand.
- **Flathub builds** use a copy generated at release time, with the
  working-tree source swapped for git at the release tag plus a small
  archive of the prebuilt inputs that aren't in git, attached to the GitHub
  release. That copy is pushed to our Flathub repo.

### Files

| File | Purpose |
| --- | --- |
| `net.froemling.bombsquad.yml` | The manifest. Its `bombsquad` module includes its project source from `bombsquad-sources.yml`. |
| `bombsquad-sources.yml` | The `bombsquad` module's project source: the project directory itself (`type: dir`). The Flathub generator writes its own copy of this file with a git source plus the release's prebuilt-inputs archive instead. |
| `python-build-env.yml` | Generated module supplying `uv` plus one wheel per package in `pconfig/requirements_build_lock.txt`, so the build can create its venv offline. Do not edit by hand. |
| `net.froemling.bombsquad.metainfo.xml` | AppStream metadata (description, screenshots, content rating, branding) shown on Flathub and in software centers. |
| `net.froemling.bombsquad.releases.xml` | AppStream release history, installed alongside the metainfo. The release workflow adds each new version's entry (see below). |
| `net.froemling.bombsquad.desktop` | Desktop entry that launches `ballisticakit`. |

## How the build works

Flatpak builds run in a sandbox based on `org.freedesktop.Sdk` 26.08 (plus
the `llvm22` SDK extension for the compiler), with the matching
`org.freedesktop.Platform` as the runtime. The 26.08 runtime ships the
Python 3.14 the game needs, so we don't build Python ourselves. A
commented-out `Python` module remains in the manifest in case we ever
need to target an older runtime.

The manifest builds three modules in order:

1. **`rsync`** builds rsync from a pinned source archive, since the SDK
   doesn't include it and our build tooling needs it. It comes first
   because it never changes, and flatpak-builder rebuilds every module
   after one that does.
2. **`python-build-env`** stages `uv` and the build's Python wheels under
   `/app/share/python-build-env`.
3. **`bombsquad`** runs `make env-clean` then `make cmake-build` to compile
   the game, and installs the staged build into `/app/bin/bombsquad`, plus
   the desktop file, metainfo, releases file and icon.

The build modules (`rsync`, `uv` and the wheels) are cleaned out of the
finished app.

The app's command is `ballisticakit`, a symlink into `/app/bin/bombsquad`.
`finish-args` sets `BA_DATA_DIR=/app/bin/bombsquad`, which works like the
`--data-dir` arg, so the game finds its data without a wrapper script.

### No network during the build

Flathub builds have no network access, and the `bombsquad` module doesn't
request it either, so local and CI builds hit the same limits Flathub
does. (The app itself still gets network at runtime through `finish-args`,
for multiplayer.) Several steps of `make cmake-build` normally download
things, so `make flatpak-prefetch` fetches them on the host first and they
travel into the sandbox with the sources:

- the cmake assets in `build/assets`, including the asset bundle that is
  assembled by calling the bacloud server (its manifest in
  `.cache/asset_bundle/gui-minimal` and the blobs it references in
  `.cache/assetdata`);
- the built resources;
- `build/prefab/lib/linux_<arch>_gui/release/libballisticaplus.a`, the
  prebuilt library the binary links against, for both `x86_64` and
  `arm64`;
- the app icon, `pconfig/flatpak/net.froemling.bombsquad.png`, fetched
  from files.ballistica.net and checked against a pinned sha256 (it isn't
  in git).

Inside the sandbox those make targets then find their outputs already in
place and up to date, so nothing is downloaded. Two build steps make
sure of that whatever the sources are:

- in Flathub builds, the files from the prebuilt-inputs archive (see
  below) are all touched to one fresh timestamp, since extracted over a
  git checkout they can be older than the files around them, and make
  would then try to re-download them. The archive lists its own files in
  `.flatpak-prebuilt-inputs` for this; local builds have no such list
  and skip the step;
- an empty `.cache/efrocache` is created, since the asset build
  downloads an efrocache starter archive whenever that dir is missing.

If you add a build step that downloads something, add it to
`flatpak-prefetch` (and, if it lands outside the paths
`flatpak_prebuilt_inputs` packs, to that list too), or the flatpak build
will fail.

### The Python venv

The build tooling (`pcommand` and friends) runs out of the project venv
(`.venv`). A venv can't be copied into the sandbox from the host, because
its `bin/python` symlink, its `pyvenv.cfg` `home` key, and every script
shebang hold the absolute path of the interpreter that created it. So the
host's `.venv` is excluded from the sources, and `make env` creates a
fresh venv inside the sandbox against the runtime's `python3.14`.

That venv is installed offline, from vendored wheels:

- `pconfig/requirements_build.txt` lists the root packages the *build*
  needs. These are a small subset of the full dev requirements, which also
  pull in linters, type checkers, test tooling, and so on.
- `make flatpak-build-env` (see `tools/batools/flatpakbuildenv.py`)
  expands those roots through the main `pconfig/requirements_lock.txt` and
  writes two outputs:
  - `pconfig/requirements_build_lock.txt`, the reduced lockfile. Versions
    and hashes are copied verbatim from the main lockfile, which stays the
    only place anything is pinned.
  - `pconfig/flatpak/python-build-env.yml`, which has a pinned `uv`
    release plus a hash-verified wheel per package for each arch
    (`x86_64`, `aarch64`).
- The `bombsquad` module sets `VENV_LOCK`, `UV_OFFLINE=1`,
  `UV_FIND_LINKS` and `UV_PYTHON_DOWNLOADS=never`, so `make env` installs
  the reduced lockfile from the staged wheels and never touches the
  network.

Both generated files are committed. **Re-run `make flatpak-build-env` and
commit the result** whenever `pconfig/requirements.txt`, the main lockfile,
or `pconfig/requirements_build.txt` changes. If a flatpak build fails on a
missing import, add that package to `requirements_build.txt` and
regenerate. To bump `uv`, update `UV_VERSION` and `UV_SHA256` in
`flatpakbuildenv.py` and regenerate.

Note that a venv built from the reduced lockfile has no dev tooling, so
`make check` / `make test` won't run against it.

## Building locally

Install `flatpak` and `flatpak-builder`. Then, once, add the `flathub`
remote for your user and install the build dependencies:

```sh
flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
make flatpak-deps
```

`make flatpak-deps` runs `flatpak-builder --user
--install-deps-from=flathub --install-deps-only` against
`net.froemling.bombsquad.yml`, which installs (or updates) the SDK,
runtime and extensions the manifest names, so their versions live only in
the manifest. It's a separate step, not part of the build, because it
changes your user flatpak installation (about 1GB). If the `flathub`
remote is missing it stops and prints the `remote-add` command above
rather than adding it for you. Re-run it after the manifest's runtime
version or extensions change.

Then, from the project root:

```sh
make flatpak-linux
```

This first runs `make flatpak-prefetch` (see above), which needs the host
venv and network access. It then builds `net.froemling.bombsquad.yml`
with flatpak-builder, which installs nothing; if the build fails because
the SDK or an extension isn't installed, run `make flatpak-deps`. State, the build
dir and the repo live under `.cache/flatpak/`. The target then exports a
bundle to `build/flatpak/bombsquad.flatpak`. Install and run it with:

```sh
flatpak install --user build/flatpak/bombsquad.flatpak
flatpak run net.froemling.bombsquad
```

`make flatpak-clean` removes `build/flatpak`, `build/flathub` and
`.cache/flatpak`.

## CI builds

- **Nightly** (`.github/workflows/nightly.yml`, job
  `make_flatpak_gui_debug`) adds the `flathub` remote and runs `make
  flatpak-deps` as its own step, then runs `make flatpak-linux` on x86_64
  and arm64 runners and uploads the bundles as workflow artifacts. The per-user
  flatpak installation and flatpak-builder's state are cached between runs,
  keyed on the manifest and `python-build-env.yml`.
- **Release** (`.github/workflows/release.yml`, job
  `release_flatpak_gui_debug`) does the same on every `v*` tag and attaches
  `bombsquad_x86_64.flatpak` / `bombsquad_arm64.flatpak` to the GitHub
  release.

## Publishing to Flathub

Flathub builds every app from its own manifest repo, on Flathub's
infrastructure, with no network access during the build. Flathub also
wants everything the build installs to come from the app's own sources,
not from files in the Flathub repo. So the Flathub manifest takes the code
from git, pinned to the release tag and its commit, and the few things git
doesn't have from one release asset,
`bombsquad_prebuilt_inputs.tar.xz` (about 4MB), written by `make
flatpak-prebuilt-inputs` (`pcommand flatpak_prebuilt_inputs`). It holds
what `make flatpak-prefetch` fetches (see above), icon included, plus
`releases.xml` with this release's entry, and is extracted over the git
checkout.

Two jobs in `.github/workflows/release.yml` handle this. They only run
when the repo owner is `efroemling` or `Loup-Garou911XD`.

```
git tag v1.x.y ─► release.yml
                   │
                   ├─ release_flatpak_prebuilt_inputs
                   │    pcommand flatpak_add_release <tag>   (adds the entry to releases.xml)
                   │    make flatpak-prebuilt-inputs  ─► bombsquad_prebuilt_inputs.tar.xz
                   │    attach it to the GitHub release
                   │
                   └─ release_generate_flathub_manifest   (needs the job above)
                        clone <owner>/flathub, branch net.froemling.bombsquad, into build/flathub
                        make flatpak-generate-flathub-manifest
                        commit + push to <owner>/flathub (net.froemling.bombsquad branch)
```

`pcommand flatpak_add_release <version> [YYYY-MM-DD]` prepends a
`<release>` entry to `net.froemling.bombsquad.releases.xml`, built from
that version's `CHANGELOG.md` entries, with links to the GitHub release
and its source archive. A version that's already listed is left alone, so
you can also commit the entry ahead of time.

`make flatpak-generate-flathub-manifest` runs `pcommand
generate_flathub_manifest` (in `tools/batools/pcommands3.py`), which:

1. Copies the manifest, unchanged, and `python-build-env.yml`, which it
   includes as a module, into `build/flathub/`, and deletes any
   metainfo, desktop or releases files an older version of this step
   left there.
2. Queries the GitHub API for the **latest** release of the repo
   (`GITHUB_REPOSITORY`, or else derived from `git remote.origin.url`),
   and finds its tag, the commit that tag points at, and the
   `bombsquad_prebuilt_inputs.tar.xz` asset and its SHA256 digest.
3. Writes `build/flathub/bombsquad-sources.yml`, the Flathub copy of the
   manifest's included project source: a `git` source (url, tag and
   commit) followed by an `archive` source for the prebuilt inputs.

The push uses the `FLATHUB_PUSH_PAT` repository secret, a token with
push access to the `<owner>/flathub` repo.

From there the update goes to Flathub through the usual Flathub flow,
which is outside this repo: a pull request from that branch into the
app's Flathub repository. Once it's merged, Flathub's buildbot builds the
manifest and publishes the new version.

### Release checklist

- If the build starts needing a file that git doesn't have, add it to
  `flatpak_prebuilt_inputs`, or Flathub builds will fail while local ones
  (which see the whole working tree) still pass.
- Keep `python-build-env.yml` current with `make flatpak-build-env`,
  because the Flathub build uses the committed copy.
- Changes to `metainfo.xml` or the `.desktop` file reach Flathub on the
  next release. You can validate them with
  `flatpak run --command=flatpak-builder-lint org.flatpak.Builder appstream net.froemling.bombsquad.metainfo.xml`.
- The generator always uses the *latest* GitHub release, so it has to run
  after the release (and its `bombsquad_prebuilt_inputs.tar.xz`) has been
  published.
