# Released under the MIT License. See LICENSE for details.
#
"""Generate C++ id-enum + load-block code for the construct asset-package.

Reads the cached bundle manifest at ``.cache/asset_bundle/gui/manifest.json``,
walks each per-bucket CAS manifest, and emits two files under
``src/ballistica/base/generated/``:

* ``builtin_asset_ids.h`` — the four ``BuiltinTextureID`` /
  ``BuiltinCubeMapTextureID`` / ``BuiltinSoundID`` / ``BuiltinMeshID``
  enums plus the ``kBuiltinAssetsApverid`` apverid string constant.
* ``builtin_asset_load.inc`` — one
  ``LoadBuiltinTexture(BuiltinTextureID::kFooBar, "<apverid>:foo/bar")``
  call per entry, ``#include``-able into ``Assets::StartLoading()``.

See ``docs/design/codegen.md`` for why outputs land in ``generated/``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from efro.error import CleanError

if TYPE_CHECKING:
    pass


class AssetKind(Enum):
    """Which of the four C++ enums an entry belongs to."""

    TEXTURE = 'texture'
    CUBE_MAP_TEXTURE = 'cube_map_texture'
    SOUND = 'sound'
    MESH = 'mesh'

    @property
    def cpp_enum_name(self) -> str:
        """C++ enum class name for this kind."""
        return {
            AssetKind.TEXTURE: 'BuiltinTextureID',
            AssetKind.CUBE_MAP_TEXTURE: 'BuiltinCubeMapTextureID',
            AssetKind.SOUND: 'BuiltinSoundID',
            AssetKind.MESH: 'BuiltinMeshID',
        }[self]

    @property
    def cpp_loader_name(self) -> str:
        """C++ ``LoadBuiltin*`` function name for this kind."""
        return {
            AssetKind.TEXTURE: 'LoadBuiltinTexture',
            AssetKind.CUBE_MAP_TEXTURE: 'LoadBuiltinCubeMapTexture',
            AssetKind.SOUND: 'LoadBuiltinSound',
            AssetKind.MESH: 'LoadBuiltinMesh',
        }[self]


# Map bucket-id-prefix → (asset-kind, ba_data subdir prefix to strip).
# Bucket ids look like e.g. ``textures/fallback_v1_regular`` or just
# ``constant``. The first path-segment of the bucket id (before the
# slash, if any) drives the dispatch.
_TEXTURE_EXTS = {'.dds', '.ktx', '.ktx2', '.pvr'}
_MESH_EXTS = {'.bob', '.bmsh'}
_SOUND_EXTS = {'.ogg', '.wav'}


@dataclass
class AssetEntry:
    """One asset, post-grouping & validation."""

    kind: AssetKind
    # Logical name within the package (no leading ba_data/<bucket>/
    # prefix, no extension). E.g. ``mydir/helloworld``.
    logical_name: str
    # Original logical path including bucket prefix + extension.
    # Kept for error messages / debugging.
    full_logical_path: str

    @property
    def cpp_enum_entry(self) -> str:
        """``kMydirHelloworld`` form."""
        return 'k' + ''.join(
            _pascal_case(seg) for seg in self.logical_name.split('/')
        )


@dataclass
class BuildResult:
    """Output collected before writing to disk."""

    apverid: str
    entries: list[AssetEntry] = field(default_factory=list)

    def entries_for(self, kind: AssetKind) -> list[AssetEntry]:
        """Entries of a given asset kind, sorted by enum-entry name."""
        return sorted(
            (e for e in self.entries if e.kind == kind),
            key=lambda e: e.cpp_enum_entry,
        )


def _pascal_case(segment: str) -> str:
    """``some_thing`` → ``SomeThing``; ``foo-bar`` → invalid."""
    if not re.fullmatch(r'[a-z0-9_]+', segment):
        raise CleanError(
            f'Asset-path segment {segment!r} is not lowercase '
            'ascii letters/digits/underscores; rename in the workspace.'
        )
    return ''.join(part.capitalize() for part in segment.split('_'))


# Bucket-id head → fixed AssetKind for buckets that hold a single kind.
_FIXED_BUCKET_KIND: dict[str, AssetKind] = {
    'cube_map_textures': AssetKind.CUBE_MAP_TEXTURE,
    'meshes': AssetKind.MESH,
    'sounds': AssetKind.SOUND,
}

# Bucket-id heads that contribute no entries to the four asset enums.
_SKIP_BUCKET_HEADS: frozenset[str] = frozenset({'language'})


def _kind_for(bucket_id: str, logical_path: str) -> AssetKind | None:
    """Map a (bucket, logical-path) pair to an AssetKind, or None to skip.

    The bucket id's first segment is the primary driver; for ``constant``
    we look at file extension since it mixes sounds + collision-meshes.
    """
    head = bucket_id.split('/', 1)[0]
    ext = Path(logical_path).suffix.lower()
    if head == 'textures':
        if ext not in _TEXTURE_EXTS:
            raise CleanError(
                f'Texture-bucket entry {logical_path!r} has '
                f'unexpected extension {ext!r}.'
            )
        return AssetKind.TEXTURE
    if head == 'constant':
        # Constant bucket can hold sounds + collision-meshes; partition
        # by extension. Anything we don't recognize gets skipped silently
        # — generator stays forward-compatible with future kinds.
        if ext in _SOUND_EXTS:
            return AssetKind.SOUND
        if ext in _MESH_EXTS:
            return AssetKind.MESH
        return None
    if head in _SKIP_BUCKET_HEADS:
        return None
    fixed = _FIXED_BUCKET_KIND.get(head)
    if fixed is not None:
        return fixed
    raise CleanError(f'Unknown asset-bundle bucket type {bucket_id!r}.')


_BUCKET_STAGED_PREFIX = re.compile(r'^ba_data/[^/]+/')


def _strip_logical_prefix(logical_path: str) -> str:
    """``ba_data/textures/foo/bar.dds`` → ``foo/bar``."""
    stripped = _BUCKET_STAGED_PREFIX.sub('', logical_path, count=1)
    return str(Path(stripped).with_suffix(''))


def collect(projroot: Path) -> BuildResult:
    """Read cached manifests and produce a validated build result.

    The manifest is produced by ``make env``'s ``assets-resolve``
    step before ``codegen`` runs, so by the time we read it the
    file exists and matches projectconfig's ``"assets"`` apverid.
    Anything else is a build-system bug we want to surface, not
    paper over.
    """
    # pylint: disable=import-outside-toplevel, too-many-locals
    from efrotools.project import getprojectconfig

    bundle_path = projroot / '.cache/asset_bundle/gui/manifest.json'
    if not bundle_path.is_file():
        raise CleanError(
            f'Asset-bundle manifest not found at {bundle_path}; '
            'run `make env` first to produce it.'
        )
    bundle = json.loads(bundle_path.read_text())
    packages = bundle.get('asset_packages') or []
    if len(packages) != 1:
        raise CleanError(
            f'Expected exactly one entry in asset_packages at '
            f'{bundle_path}; got {len(packages)}.'
        )
    pkg = packages[0]
    apverid: str = pkg['apverid']

    projectconfig_apverid = getprojectconfig(projroot).get('assets')
    if projectconfig_apverid != apverid:
        raise CleanError(
            f"Bundle manifest apverid {apverid!r} does not match "
            f"projectconfig 'assets' {projectconfig_apverid!r}; "
            '`make env` should have refreshed the bundle. '
            'Try `make assets-resolve-clean && make env`.'
        )

    cas_root = projroot / '.cache/assetdata'

    result = BuildResult(apverid=apverid)
    errors: list[str] = []

    for bucket_id, manifest_sha in pkg['bundled_buckets'].items():
        bucket_path = cas_root / manifest_sha[:2] / manifest_sha[2:]
        if not bucket_path.is_file():
            raise CleanError(
                f"Bucket manifest blob missing: {bucket_path} "
                f'(bucket {bucket_id!r}).'
            )
        bucket = json.loads(bucket_path.read_text())
        for logical_path in sorted(bucket.get('h', {}).keys()):
            kind = _kind_for(bucket_id, logical_path)
            if kind is None:
                continue
            logical_name = _strip_logical_prefix(logical_path)
            segments = logical_name.split('/')
            if len(segments) < 2:
                errors.append(
                    f'Asset {logical_path!r} is at workspace root; '
                    'move into a category subdir (e.g. ui/, test/).'
                )
                continue
            try:
                for seg in segments:
                    _pascal_case(seg)  # validation only
            except CleanError as exc:
                errors.append(str(exc))
                continue
            result.entries.append(
                AssetEntry(
                    kind=kind,
                    logical_name=logical_name,
                    full_logical_path=logical_path,
                )
            )

    # Cross-kind collision check: same logical_name appearing under two
    # AssetKinds is ambiguous since the wrapper namespace is flat.
    by_name: dict[str, list[AssetEntry]] = {}
    for entry in result.entries:
        by_name.setdefault(entry.logical_name, []).append(entry)
    for name, entries in by_name.items():
        kinds = {e.kind for e in entries}
        if len(kinds) > 1:
            errors.append(
                f'Logical name {name!r} appears across multiple asset '
                f'types ({sorted(k.value for k in kinds)}); rename to '
                'disambiguate.'
            )

    if errors:
        raise CleanError(
            'Asset-package validation failed:\n  - ' + '\n  - '.join(errors)
        )

    return result


def render_header(result: BuildResult) -> str:
    """Build the contents of ``builtin_asset_ids.h``."""

    lines: list[str] = [
        '// Released under the MIT License. See LICENSE for details.',
        '//',
        '// Auto-generated by tools/batools/builtinassetids.py.',
        '// Do not edit by hand; rerun `make update`.',
        '#ifndef BALLISTICA_BASE_GENERATED_BUILTIN_ASSET_IDS_H_',
        '#define BALLISTICA_BASE_GENERATED_BUILTIN_ASSET_IDS_H_',
        '',
        '#include <cstdint>',
        '',
        'namespace ballistica::base {',
        '',
        '/// Apverid of the construct asset-package this build targets.',
        '/// Generated from projectconfig.json `"assets"`; prepended onto',
        '/// each load-call name to form a CAS-qualified ref.',
        'inline constexpr const char* kBuiltinAssetsApverid =',
        f'    "{result.apverid}";',
        '',
    ]

    for kind in AssetKind:
        entries = result.entries_for(kind)
        lines.append(f'enum class {kind.cpp_enum_name} : uint16_t {{')
        for entry in entries:
            lines.append(
                f'  {entry.cpp_enum_entry},  ' f'// {entry.full_logical_path}'
            )
        lines.append('};')
        lines.append('')

    lines.extend(
        [
            '}  // namespace ballistica::base',
            '',
            '#endif  // BALLISTICA_BASE_GENERATED_BUILTIN_ASSET_IDS_H_',
            '',
        ]
    )
    return '\n'.join(lines)


def render_load_inc(result: BuildResult) -> str:
    """Build the contents of ``builtin_asset_load.inc``."""

    lines: list[str] = [
        '// Released under the MIT License. See LICENSE for details.',
        '//',
        '// Auto-generated by tools/batools/builtinassetids.py.',
        '// Do not edit by hand; rerun `make update`.',
        '//',
        '// Designed to be #include\'d from Assets::StartLoading().',
        '',
    ]

    for kind in AssetKind:
        entries = result.entries_for(kind)
        if not entries:
            continue
        lines.append(f'// {kind.value}s')
        for entry in entries:
            full = f'{result.apverid}:{entry.logical_name}'
            lines.append(
                f'{kind.cpp_loader_name}('
                f'{kind.cpp_enum_name}::{entry.cpp_enum_entry}, '
                f'"{full}");'
            )
        lines.append('')

    return '\n'.join(lines)


def generate(projroot: Path, check: bool = False) -> bool:
    """Generate (or check) the two output files.

    Returns True if anything was (or would be) changed.
    """

    out_dir = projroot / 'src/ballistica/base/generated'
    header_path = out_dir / 'builtin_asset_ids.h'
    inc_path = out_dir / 'builtin_asset_load.inc'

    result = collect(projroot)
    header_text = render_header(result)
    inc_text = render_load_inc(result)

    changed = False
    for path, text in ((header_path, header_text), (inc_path, inc_text)):
        existing = path.read_text() if path.is_file() else None
        if existing == text:
            continue
        changed = True
        if check:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return changed
