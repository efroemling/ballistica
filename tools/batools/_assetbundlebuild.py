# Released under the MIT License. See LICENSE for details.
#
"""Asset-bundle assembly for builds (the ``asset_bundle_build`` pcommand).

Assembles a named bundle profile (see :mod:`batools.assetbundleprofiles`)
into ``.cache/asset_bundle/<cache-dir>/`` for ``stage_build`` to copy
into a build's ``ba_data/``. Split out of :mod:`batools.pcommands2` to
keep that module under the line limit.
"""

import sys
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

    from batools.assetbundleprofiles import BundlePackage


def build(projroot: str, args: list[str]) -> None:
    """Assemble a named bundle profile for the projectconfig pins.

    Args: a bundle-profile name (see :mod:`batools.assetbundleprofiles`)
    plus ``--form-factor <desktop|mobile>`` for form-factor-specific
    profiles (``store``). A profile names the set of asset packages
    baked into a build, each with its texture profiles / tier /
    languages: ``gui-minimal`` / ``headless-minimal`` carry just the
    builtin construct package at baseline flavors; ``store`` carries
    every package the bundled code requires (meta-scanned) at the
    device-native texture flavor with every language, so a store build
    boots and plays offline in any locale.

    Assembles every (package, texture-profile, language) combination
    via ``bacloud assetpackage _assemble`` -- one call each, since the
    resolve meta-build is keyed on that exact triple -- and deep-merges
    the resulting flavor coords into one
    ``.cache/asset_bundle/<cache-dir>/manifest.json`` plus CAS-keyed
    bucket manifests + data blobs under ``.cache/assetdata/`` (shared
    across profiles for CAS dedup). ``stage_build`` copies the matching
    cache dir into ``<staged>/ba_data/`` based on the build target.

    Steady-state early-out: if the cache already holds exactly the
    expected package set at these apverids with every expected flavor
    coord present, nothing runs. ``BA_ASSET_BUNDLE_FORCE_REFETCH=1``
    bypasses that (a server-side pipeline bump changes built output
    without moving the pin).
    """
    import os
    import json
    import time
    from pathlib import Path

    from efro.error import CleanError
    from efro.terminal import Clr
    from efro.util import extract_arg

    from batools.assetbundleprofiles import (
        get_profile,
        bundle_cache_dirname,
        materialize_profile,
    )

    form_factor = extract_arg(args, '--form-factor')
    if len(args) != 1:
        raise CleanError(
            'Expected 1 positional arg (bundle-profile name),'
            ' optionally with --form-factor.'
        )
    profile = get_profile(args[0])
    cache_dir = bundle_cache_dirname(profile, form_factor)
    packages = materialize_profile(profile, form_factor, Path(projroot))

    bundle_path = os.path.join(
        projroot, '.cache/asset_bundle', cache_dir, 'manifest.json'
    )
    triples, expected_coords = _plan_assembles(packages)

    force_refetch = os.environ.get('BA_ASSET_BUNDLE_FORCE_REFETCH') == '1'
    if not force_refetch and os.path.exists(bundle_path):
        try:
            with open(bundle_path, encoding='utf-8') as infile:
                existing = json.load(infile)
        except Exception:
            existing = None
        if isinstance(existing, dict) and _bundle_satisfies(
            existing, expected_coords
        ):
            return

    print(
        f'{Clr.BLU}Assembling bundle profile {cache_dir!r}'
        f' ({len(packages)} package(s), {len(triples)} assemble(s))...'
        f'{Clr.RST}',
        flush=True,
    )
    t_start = time.monotonic()
    merged = _assemble_and_merge(projroot, triples)
    if not _bundle_satisfies(merged, expected_coords):
        raise CleanError(
            'Assembled bundle is missing expected flavor coords;'
            ' this is a bug in the profile/coord bookkeeping.'
        )

    os.makedirs(os.path.dirname(bundle_path), exist_ok=True)
    with open(bundle_path, 'w', encoding='utf-8') as outfile:
        # indent=1: newline-delimited for readability/debuggability while
        # staying maximally brief, matching the flavor-manifest blobs
        # (compute_bucket_manifest_blobs). sort_keys for stable diffs.
        # This top-level manifest is not content-addressed (stable path,
        # only json.load-parsed), so the format is free to change.
        json.dump(merged, outfile, indent=1, sort_keys=True)
    print(
        f'{Clr.GRN}Assembled bundle profile {cache_dir!r} in'
        f' {time.monotonic() - t_start:.1f}s.{Clr.RST}',
        flush=True,
    )


def _plan_assembles(
    packages: list[BundlePackage],
) -> tuple[list[tuple[str, str, str, str]], dict[str, set[str]]]:
    """Every (package, texture-profile, tier, language) to assemble,
    plus the flavor coords each package's merged entry must end up
    with (drives the early-out and a post-assemble sanity check).

    Coord formation mirrors the runtime's ``_desired_coords``; the
    non-language/non-texture buckets ride along with every call.
    """
    triples: list[tuple[str, str, str, str]] = []
    expected_coords: dict[str, set[str]] = {}
    for pkg in packages:
        # Keyed like the bundle manifest: the numeric id as text.
        pkgkey = str(pkg.apvernum)
        coords = expected_coords.setdefault(pkgkey, set())
        for language in pkg.languages:
            triples.append(
                (pkgkey, pkg.texture_profile, pkg.texture_tier, language)
            )
            coords.add(f'language/{language}')
        coords.add(f'textures/{pkg.texture_profile}.gamma.{pkg.texture_tier}')
        # Extra texture flavors ride a single (first-language) call each;
        # the textures coord is language-independent.
        for tprofile in pkg.extra_texture_profiles:
            triples.append(
                (pkgkey, tprofile, pkg.texture_tier, pkg.languages[0])
            )
            coords.add(f'textures/{tprofile}.gamma.{pkg.texture_tier}')
    return triples, expected_coords


def _assemble_and_merge(
    projroot: str, triples: list[tuple[str, str, str, str]]
) -> dict[str, dict]:
    """Assemble every triple and deep-merge into one bundle manifest.

    Groups triples by (package, texture-profile, tier) and assembles
    each group in ONE master call carrying every language (the server
    ensures one resolve meta-build per language -- keyed on that exact
    triple -- in parallel and merges their outputs), so a store bundle
    is a handful of calls rather than one per locale, and cold language
    leaves build concurrently on the server instead of serially here.

    Entries are keyed by apverid and each carries a ``flavor_manifests``
    coord map, so merging = union of coords per package (a coord's hash
    is a pure function of the package content, so repeats agree).
    """
    import time

    groups: dict[tuple[str, str, str], list[str]] = {}
    for apverid, tprofile, tier, language in triples:
        groups.setdefault((apverid, tprofile, tier), []).append(language)

    from concurrent.futures import ThreadPoolExecutor

    names = _package_names(projroot)

    def run_one(
        indexed: tuple[int, tuple[tuple[str, str, str], list[str]]],
    ) -> dict[str, Any]:
        i, ((apverid, tprofile, tier), languages) = indexed
        # Lead with the readable string id; the numeric one (what the
        # bundle and the engine actually key on) follows for reference.
        name = names.get(apverid)
        label = f'{name} (#{apverid})' if name is not None else f'#{apverid}'
        # Several of these run at once, so every line a call prints
        # carries a short tag saying whose it is.
        tag = f'{i}/{len(groups)}'
        _say(
            f'  [{tag}] {label} {tprofile}.{tier}'
            f' ({len(languages)} language(s))'
        )
        t_one = time.monotonic()
        one = _assemble_with_retry(
            projroot, apverid, tprofile, tier, languages, tag=tag
        )
        _say(f'  [{tag}] done ({time.monotonic() - t_one:.1f}s)')
        return one

    # Assemble a few packages at a time. Each call mostly waits -- on
    # the server building, then on its own downloads -- so overlapping
    # them is nearly free here, and server-side it lets one package's
    # builds run while another's are queued. Capped low on purpose:
    # every in-flight call is a live poll against the master's
    # front-end, which is not the place to fan out wide.
    with ThreadPoolExecutor(max_workers=_ASSEMBLE_CONCURRENCY) as pool:
        results = list(pool.map(run_one, enumerate(groups.items(), 1)))

    merged: dict[str, dict] = {'asset_package_versions': {}}
    # Merged in plan order (pool.map preserves it), so the manifest does
    # not depend on which call happened to finish first.
    for one in results:
        for apv, entry in one['asset_package_versions'].items():
            dst = merged['asset_package_versions'].setdefault(apv, {})
            for key, val in entry.items():
                if key == 'flavor_manifests':
                    dst.setdefault(key, {}).update(val)
                else:
                    dst[key] = val
    return merged


def _package_names(projroot: str) -> dict[str, str]:
    """Numeric asset-package-version id (as text) -> readable string id.

    For progress output only, and best-effort: bundles are planned and
    keyed purely by numeric id, which tells a person nothing. Every
    generated wrapper module carries both forms -- its ``# ba_meta
    require asset-package <num>`` line and an ``Asset-package wrapper
    for ``<string id>``` docstring line -- so we read the pairing off
    those. A package with no wrapper in the tree is simply absent (the
    caller falls back to the bare number).
    """
    import os
    import re

    re_num = re.compile(r'^# ba_meta require asset-package (\d+)\s*$', re.M)
    re_name = re.compile(r'Asset-package wrapper for ``([^`]+)``')
    names: dict[str, str] = {}
    root = os.path.join(projroot, 'src/assets/ba_data/python')
    for dirpath, _dirnames, filenames in os.walk(root):
        for filename in filenames:
            if not filename.endswith('assets.py'):
                continue
            try:
                with open(
                    os.path.join(dirpath, filename), encoding='utf-8'
                ) as infile:
                    text = infile.read()
            except OSError:
                continue
            num = re_num.search(text)
            name = re_name.search(text)
            if num is not None and name is not None:
                names[num.group(1)] = name.group(1)
    return names


def _bundle_satisfies(
    bundle: dict[str, Any], expected_coords: dict[str, set[str]]
) -> bool:
    """Does a bundle manifest hold exactly these packages with all coords?"""
    apvs = bundle.get('asset_package_versions')
    if not isinstance(apvs, dict) or set(apvs) != set(expected_coords):
        return False
    for apverid, coords in expected_coords.items():
        entry = apvs.get(apverid)
        if not isinstance(entry, dict):
            return False
        have = entry.get('flavor_manifests')
        if not isinstance(have, dict) or not coords <= set(have):
            return False
    return True


#: Substrings of bacloud's error text that mean the interactive session
#: to the basn node was lost (reconnect budget exhausted, etc.) rather
#: than the assemble itself failing. A cold store assemble polls for
#: minutes; one network blip that outlasts the session's reconnect
#: budget must not fail the whole build when the server-side builds
#: are still progressing and a fresh call simply resumes polling them.
_SESSION_LOSS_MARKERS = ('session closed', 'reconnect budget')

_ASSEMBLE_ATTEMPTS = 4

#: How many package assembles run at once (see ``_assemble_and_merge``).
_ASSEMBLE_CONCURRENCY = 3

_g_say_lock = threading.Lock()


def _say(line: str) -> None:
    """Print one whole line; safe from the concurrent assemble threads."""
    with _g_say_lock:
        print(line, flush=True)


def _assemble_with_retry(
    projroot: str,
    apverid: str,
    texture_profile: str,
    texture_tier: str,
    languages: list[str],
    *,
    tag: str,
) -> dict[str, Any]:
    """``_assemble_one`` with a bounded retry on session loss."""
    import time

    from efro.error import CleanError

    for attempt in range(1, _ASSEMBLE_ATTEMPTS + 1):
        try:
            return _assemble_one(
                projroot,
                apverid,
                texture_profile,
                texture_tier,
                languages,
                tag=tag,
            )
        except CleanError as exc:
            lost = any(m in str(exc) for m in _SESSION_LOSS_MARKERS)
            if not lost or attempt == _ASSEMBLE_ATTEMPTS:
                raise
            _say(
                f'  [{tag}] (bacloud session lost; retrying assemble,'
                f' attempt {attempt + 1} of {_ASSEMBLE_ATTEMPTS})'
            )
            time.sleep(5.0)
    raise RuntimeError('unreachable')


def _run_tagged(
    cmd: list[str], env: dict[str, str], tag: str
) -> tuple[int, str]:
    """Run a command, relaying its stdout live; return (exit code, stderr).

    Stdout is relayed line by line as it arrives, each line tagged with
    which assemble it belongs to (several run at once), so a slow
    build's progress still streams out live. Stderr -- where bacloud
    reports why it failed, quoting the master server verbatim -- is
    captured so a failure can be explained precisely; it goes to a file
    rather than a pipe so nothing can stall on a full pipe while we are
    reading stdout.
    """
    import tempfile
    import subprocess

    with (
        tempfile.TemporaryFile(mode='w+') as errfile,
        subprocess.Popen(
            cmd, env=env, stdout=subprocess.PIPE, stderr=errfile, text=True
        ) as proc,
    ):
        assert proc.stdout is not None
        for line in proc.stdout:
            _say(f'  [{tag}] {line.rstrip()}')
        returncode = proc.wait()
        errfile.seek(0)
        return returncode, errfile.read()


def _assemble_one(
    projroot: str,
    apverid: str,
    texture_profile: str,
    texture_tier: str,
    languages: list[str],
    *,
    tag: str,
) -> dict[str, Any]:
    """Assemble one (package, texture-profile) x languages via bacloud.

    Blobs land in the shared ``.cache/assetdata``; the single-package
    manifest is written to a temp path and returned parsed so the
    caller can merge it into the profile's combined manifest.
    """
    import os
    import json
    import tempfile
    import subprocess

    from efro.error import CleanError
    from batools.version import get_current_version
    from batools.assetpins import describe_apverid_fetch_failure

    tmpdir = os.path.join(projroot, 'build/tmp')
    os.makedirs(tmpdir, exist_ok=True)
    fd, tmppath = tempfile.mkstemp(suffix='.json', dir=tmpdir)
    os.close(fd)

    # Report the target build to bacloud so master picks the matching
    # asset-manifest path-format epoch (bacloud itself can't see baenv in
    # this subprocess context; see _caller_build_number there).
    # get_current_version reads projectconfig.json, which is present in
    # every asset-build cloudshell env (pcommand locates PROJROOT by it).
    _version, build_number = get_current_version(str(projroot))
    env = dict(os.environ)
    env['BA_BUILD_NUMBER'] = str(build_number)
    errtext = ''
    try:
        returncode, errtext = _run_tagged(
            [
                f'{projroot}/tools/bacloud',
                'assetpackage',
                '_assemble',
                apverid,
                '--texture-profile',
                texture_profile,
                '--texture-tier',
                texture_tier,
                *(arg for lang in languages for arg in ('--language', lang)),
                '--bundle-path',
                tmppath,
            ],
            env,
            tag,
        )
        if returncode != 0:
            raise subprocess.CalledProcessError(returncode, 'bacloud')
        # Succeeded, but bacloud may still have had something to say
        # (retry notices, verbose diagnostics); don't eat it.
        if errtext:
            sys.stderr.write(errtext)
        with open(tmppath, encoding='utf-8') as infile:
            manifest: dict[str, Any] = json.load(infile)
        return manifest
    except Exception as exc:
        raise CleanError(
            describe_apverid_fetch_failure(
                apverid,
                action=(
                    f'assemble package {apverid!r} (texture-profile'
                    f' {texture_profile!r}, languages {languages!r})'
                ),
                exc=exc,
                output=errtext,
            )
        ) from exc
    finally:
        if os.path.exists(tmppath):
            os.unlink(tmppath)
