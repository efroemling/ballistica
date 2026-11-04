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
| `net.froemling.bombsquad.releases.xml` | AppStream release history, installed alongside the metainfo. Not in git: generated from `CHANGELOG.md` (see below). |
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
  in git);
- `pconfig/flatpak/net.froemling.bombsquad.releases.xml`, generated from
  `CHANGELOG.md` (see "Release history" below; also not in git).

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
- `make flatpak-build-env` writes two outputs:
  - `pconfig/requirements_build_lock.txt`, the reduced lockfile, compiled
    by `uv pip compile` from those roots with the main
    `pconfig/requirements_lock.txt` as a constraint, so the main lockfile
    stays the only place anything is pinned.
  - `pconfig/flatpak/python-build-env.yml` (see
    `tools/batools/flatpakbuildenv.py`), which has a pinned `uv` release
    plus a hash-verified wheel per package for each arch (`x86_64`,
    `aarch64`).
- The `bombsquad` module sets `VENV_LOCK`, `UV_OFFLINE=1`,
  `UV_FIND_LINKS` and `UV_PYTHON_DOWNLOADS=never`, so `make env` installs
  the reduced lockfile from the staged wheels and never touches the
  network.

Both generated files are committed, and `make upgrade` regenerates them,
since everything in them is derived: the build lockfile takes its versions
from the main lockfile, and the module installs the `uv` pinned in
`pconfig/flatpak/uv.json` (version plus each arch's published checksum).
`make upgrade` also moves that pin to uv's latest release
(`make flatpak-uv-upgrade`). After changing `pconfig/requirements_build.txt`
by hand, run `make flatpak-build-env` and commit the result. `make
update-check` (so preflight and CI) fails if the build lockfile's versions
or the module's `uv` don't match what they're derived from. If a flatpak
build fails on a missing import, add that package to
`requirements_build.txt` and regenerate.

Note that a venv built from the reduced lockfile has no dev tooling, so
`make check` / `make test` won't run against it.

## Building locally

Install `flatpak` (any version). You don't need your distro's
`flatpak-builder`: builds run Flathub's packaged one,
`org.flatpak.Builder` (`FLATPAK_BUILDER` in the Makefile), which
bundles a current flatpak. The manifest needs that: its conditional
finish-args (`--device-if`, for game controllers) only build with
flatpak 1.17 or newer, and distros lag (Ubuntu 26.04 ships 1.16). It's
also what Flathub builds with, so local and CI builds match Flathub's.

Then, once, add the `flathub` remote for your user and install the build
dependencies:

```sh
flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
make flatpak-deps
```

`make flatpak-deps` installs (or updates) `org.flatpak.Builder`, then
runs it with `--user --install-deps-from=flathub --install-deps-only`
against `net.froemling.bombsquad.yml`, which installs (or updates) the
SDK, runtime and extensions the manifest names, so their versions live
only in the manifest. It's a separate step, not part of the build, because it
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
what `make flatpak-prefetch` fetches (see above), icon and
`releases.xml` included, and is extracted over the git checkout.

The app's Flathub repo is
[flathub/net.froemling.bombsquad](https://github.com/flathub/net.froemling.bombsquad).
Its `master` is protected: changes arrive only as pull requests, which
Flathub test-builds (the `flathub/build` check), and merging one
publishes that build.

Two jobs in the public repo's `.github/workflows/release.yml` handle
this. (`.github/` exists only in the public repo; pubsync never touches
it.) The first runs when the repo owner is `efroemling` or
`Loup-Garou911XD`; the second only for `efroemling`, so a release
tagged on a fork never opens a PR against the real app repo.

```
git tag v1.x.y ─► release.yml
                   │
                   ├─ release_flatpak_prebuilt_inputs
                   │    pcommand flatpak_add_release <tag>   (generates releases.xml up to <tag>)
                   │    make flatpak-prebuilt-inputs  ─► bombsquad_prebuilt_inputs.tar.xz
                   │    attach it to the GitHub release
                   │
                   └─ release_generate_flathub_manifest   (needs the job above)
                        clone flathub/net.froemling.bombsquad into build/flathub, branch update-<tag>
                        make flatpak-generate-flathub-manifest
                        push update-<tag>, open a PR into master
```

Re-running the second job force-pushes the same branch, which updates
the open PR rather than opening another. If the generated files already
match `master`, the job does nothing.

### Release history

`net.froemling.bombsquad.releases.xml` is generated, never edited or
committed: `CHANGELOG.md` is the only record of releases. `pcommand
flatpak_add_release [version]` rewrites the whole file from it, listing
the newest 10 changelog versions up to and including `version` (default:
the newest, which is what `make flatpak-prefetch` uses when the file is
missing or older than `CHANGELOG.md`). Each entry takes its date from its
changelog heading and has a one-line description plus a link to its
section of the public repo's `CHANGELOG.md`. The changelog itself is
written for modders and goes into code detail, so it isn't copied into
the descriptions that software centers show players.

Tags are the only trigger for Flathub: untagged pushes never touch this
file, and the nightly flatpak build only generates a throwaway copy.

`make flatpak-generate-flathub-manifest` runs `pcommand
generate_flathub_manifest` (in `tools/batools/pcommands3.py`), which:

1. Empties `build/flathub/` (keeping `.git` and any `flathub.json`), so
   the Flathub repo holds only what this step writes, then copies in the
   manifest, unchanged, and `python-build-env.yml`, which it includes as
   a module.
2. Queries the GitHub API for the release of the tag that triggered the
   workflow (or, run by hand, the **latest** release) of the repo
   (`GITHUB_REPOSITORY`, or else derived from `git remote.origin.url`),
   and finds its tag, the commit that tag points at, and the
   `bombsquad_prebuilt_inputs.tar.xz` asset and its SHA256 digest.
3. Writes `build/flathub/bombsquad-sources.yml`, the Flathub copy of the
   manifest's included project source: a `git` source (url, tag and
   commit) followed by an `archive` source for the prebuilt inputs.

The push and the PR use the `FLATHUB_PUSH_PAT` secret in the public
repo: a token from Eric's GitHub account, which has write access to
`flathub/net.froemling.bombsquad` (a classic PAT with `public_repo`
scope). The PR is opened as that account.

The `/push-public` skill then follows the PR: it waits for the
`flathub/build` check and merges the PR when it's green, and stops and
reports if it fails. Once the PR is merged, Flathub builds `master`
again and publishes it (the `flat-manager/*` statuses on the merge
commit).

(Until 2026-10, before the app was accepted, the job pushed to the
`net.froemling.bombsquad` branch of a fork, `efroemling/flathub`, which
was the submission PR's branch. That fork is no longer used.)

### Release checklist

- If the build starts needing a file that git doesn't have, add it to
  `flatpak_prebuilt_inputs`, or Flathub builds will fail while local ones
  (which see the whole working tree) still pass.
- Keep `python-build-env.yml` current with `make flatpak-build-env`,
  because the Flathub build uses the committed copy.
- Changes to `metainfo.xml` or the `.desktop` file reach Flathub on the
  next release. You can validate them with
  `flatpak run --command=flatpak-builder-lint org.flatpak.Builder appstream net.froemling.bombsquad.metainfo.xml`.
- Run by hand, the generator uses the *latest* GitHub release, so it has
  to run after that release (and its `bombsquad_prebuilt_inputs.tar.xz`)
  has been published.
