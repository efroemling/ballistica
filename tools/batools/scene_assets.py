# Released under the MIT License. See LICENSE for details.
#
"""Codegen for the scene_v1 asset set.

The sibling of :mod:`batools.ui_assets` (see that module's docstring
for the shared reasoning: one spec drives the Python class, the C++
struct, and the unpacker between them, so nothing can drift). Reads
``bascenev1codegen.scene_assets`` and emits:

* ``bascenev1/_generated/scene_asset_set.py`` -- the
  ``SceneV1AssetSet`` class an app-mode carries on its config and
  hands to ``bascenev1.set_scene_asset_set()``.
* ``scene_v1/generated/scene_asset_set.h`` -- the C++ struct.
* ``scene_v1/generated/scene_asset_set_unpack.inc`` -- the unpacker.

It differs from the ui flavor at the native boundary, in a way that
is load-bearing: slots hold *handles* end to end, and the C++
unpacker reads each handle's package id and name and loads the
underlying **base**-level asset itself (``Assets::GetPackageTexture``
etc.). It cannot pass loaded ``bascenev1.Texture`` objects the way
the ui flavor passes ``bauiv1.Texture`` ones, because scene-flavor
Python assets are *context-bound scene assets* (the streamed kind)
while the nodes draw raw engine assets client-locally. Reading the
private ``_apverid``/``_name`` attrs native-side is the sanctioned
boundary for that (same as ``ClassicPython::QualifiedRefFromHandle_``).

Every slot has a default (scene_v1's own package), so the set
constructs bare and an app-mode overrides only what it wants to
reskin. Nothing loads until the set is applied at activation, so
replaced defaults are never loaded at all.

Not imported at runtime -- this is build-time only.
"""

import os
import sys
import textwrap
import importlib
from enum import Enum
from dataclasses import dataclass, field


class Kind(Enum):
    """Kind of engine asset a slot holds."""

    TEXTURE = 'texture'
    MESH = 'mesh'
    SOUND = 'sound'


@dataclass(frozen=True)
class _KindInfo:
    """Per-kind bits the emitters need."""

    #: Python annotation for the handle form a slot holds.
    handletype: str

    #: C++ asset type held in the struct.
    cpptype: str

    #: Assets:: accessor loading one from (apverid, name).
    loader: str


KIND_INFO = {
    Kind.TEXTURE: _KindInfo(
        handletype='TextureHandle',
        cpptype='base::TextureAsset',
        loader='GetPackageTexture',
    ),
    Kind.MESH: _KindInfo(
        handletype='MeshHandle',
        cpptype='base::MeshAsset',
        loader='GetPackageMesh',
    ),
    Kind.SOUND: _KindInfo(
        handletype='SoundHandle',
        cpptype='base::SoundAsset',
        loader='GetPackageSound',
    ),
}


@dataclass
class Slot:
    """One asset the scene_v1 node layer needs supplied to it."""

    #: Field name on both sides (snake_case); also the C++ member name.
    name: str

    #: What kind of asset this slot holds.
    kind: Kind

    #: One-line description, emitted as docs on both sides.
    doc: str

    #: Attr path of this slot's fallback art on the group's
    #: ``default_module``, e.g. ``'meshes.eye_ball'``. Deliberately not
    #: derived from ``name`` -- a slot and the asset backing it are
    #: free to be named differently (see ``scorch_mesh``).
    default: str


@dataclass
class Group:
    """A logical grouping of slots, emitted as section comments."""

    #: Group name (snake_case).
    name: str

    #: One-line description of what this group covers.
    doc: str

    #: Wrapper module the slots' ``default`` paths hang off.
    default_module: str

    #: The slots it holds.
    slots: list[Slot] = field(default_factory=list)


@dataclass
class SceneAssetSpec:
    """The complete set of assets scene_v1 needs supplied to it."""

    groups: list[Group] = field(default_factory=list)


#: Top-level Python class / C++ struct name.
TOP_CLASS = 'SceneV1AssetSet'


def load_spec(projroot: str) -> SceneAssetSpec:
    """Import the spec module and return its spec."""
    sys.path.insert(0, os.path.abspath(os.path.join(projroot, 'src/codegen')))
    try:
        # Avoid cached import in tests.
        if 'bascenev1codegen.scene_assets' in sys.modules:
            importlib.reload(sys.modules['bascenev1codegen.scene_assets'])
        mod = importlib.import_module('bascenev1codegen.scene_assets')
    finally:
        sys.path.pop(0)
    spec: SceneAssetSpec = mod.SPEC

    if not spec.groups:
        raise RuntimeError('scene-asset spec is empty.')
    seen: set[str] = set()
    for group in spec.groups:
        if not group.slots:
            raise RuntimeError(f'scene-asset group {group.name} is empty.')
        for slot in group.slots:
            # One shared field namespace on both sides; a collision
            # would silently drop a slot.
            if slot.name in seen:
                raise RuntimeError(
                    f'Duplicate scene-asset slot name: {slot.name}'
                )
            seen.add(slot.name)
    return spec


def _slots(spec: SceneAssetSpec) -> list[tuple[Group, Slot]]:
    """Every slot in spec order, paired with its group."""
    return [(g, s) for g in spec.groups for s in g.slots]


def _wrap(text: str, prefix: str) -> list[str]:
    """Wrap one doc line to fit our line-length limit."""
    return textwrap.wrap(
        text,
        width=79 - len(prefix),
        initial_indent=prefix,
        subsequent_indent=prefix,
    )


def generate_python(projroot: str, out_path: str) -> None:
    """Emit the SceneV1AssetSet class and the apply function."""
    spec = load_spec(projroot)
    pairs = _slots(spec)

    out = [
        '# Released under the MIT License. See LICENSE for details.',
        '#',
        '# AUTO-GENERATED by `tools/pcommand gen_scene_asset_set_py`.',
        '# DO NOT EDIT BY HAND.',
        '#',
        '# Generated from src/codegen/bascenev1codegen/scene_assets.py.',
        '"""Supplying scene_v1 with the assets it draws itself with."""',
        '',
        'from typing import TYPE_CHECKING',
        '',
        'import _bascenev1',
        '',
    ]
    # Wrapper modules the defaults hang off. Imported for real since
    # the init lines reference them; importing a wrapper only builds
    # its tree, it loads no assets.
    for mod in dict.fromkeys(g.default_module for g in spec.groups):
        out.append(f'from bascenev1 import {mod}')
    out += [
        '',
        'if TYPE_CHECKING:',
        '    from bascenev1._assetref import (',
        '        MeshHandle,',
        '        SoundHandle,',
        '        TextureHandle,',
        '    )',
        '',
        '',
        f'class {TOP_CLASS}:',
        '    """The assets the scene_v1 node layer draws itself with.',
        '',
        '    An app-mode using scene_v1 carries one of these on its',
        '    app-mode config and hands it to',
        '    :func:`bascenev1.set_scene_asset_set` when activating,',
        '    which is what lets an app-mode (or a plugin amending its',
        '    config) reskin the art scene_v1 nodes draw themselves',
        '    with.',
        '',
        '    Slots hold asset *handles*, not loaded assets; nothing',
        '    loads until the set is applied at activation, so art that',
        '    gets replaced is never loaded at all. Every slot defaults',
        "    to scene_v1's own art, so a bare ``SceneV1AssetSet()`` is",
        '    complete and a supplier names only what it changes.',
        '    """',
        '',
        '    # One attr per slot is the whole point of this class; the',
        '    # complexity limits are aimed at hand-written code where',
        '    # this shape signals trouble.',
        '    # pylint: disable=too-many-instance-attributes',
    ]
    for group in spec.groups:
        out.append('')
        out += _wrap(f'-- {group.doc}', '    # ')
        for slot in group.slots:
            htype = KIND_INFO[slot.kind].handletype
            out += _wrap(slot.doc, '    #: ')
            out.append(f'    {slot.name}: {htype}')
    out += [
        '',
        '    def __init__(self) -> None:',
        '        # All slots start at scene_v1\'s own art (handles only;',
        '        # nothing is loaded here).',
    ]
    for group, slot in pairs:
        expr = f'{group.default_module}.{slot.default}'
        flat = f'        self.{slot.name} = {expr}'
        if len(flat) <= 79:
            out.append(flat)
        else:
            out += [
                f'        self.{slot.name} = (',
                f'            {expr}',
                '        )',
            ]
    out += [
        '',
        '',
        f'def set_scene_asset_set(assets: {TOP_CLASS}) -> None:',
        '    """Supply the assets the scene_v1 node layer draws with.',
        '',
        '    Called by an app-mode during activation (normally from',
        '    :meth:`~babase.AppMode.on_activate`, with the',
        f'    :class:`{TOP_CLASS}` carried by its app-mode config),',
        '    before any scene sessions exist. Unlike the ui set this is',
        '    supplied on headless builds too -- servers run scenes.',
        '',
        '    Loading happens native-side as the set is applied, so',
        '    replaced defaults are never loaded. The supplied art is',
        "    wiped by scene_v1's app-subsystem",
        '    :meth:`~babase.AppSubsystem.reset` at every app-mode',
        "    switch, so a mode can never inherit a previous mode's art.",
        '    """',
        '    # Positional, in spec order -- the native side is generated',
        '    # from the same spec, so the two cannot drift.',
        '    _bascenev1.set_scene_asset_set_native(',
    ]
    for _group, slot in pairs:
        out.append(f'        assets.{slot.name},')
    out += ['    )']

    _write(out_path, '\n'.join(out).rstrip('\n') + '\n')


def generate_cpp(projroot: str, out_path: str) -> None:
    """Emit the C++ struct header or the unpacker include."""
    base = os.path.basename(out_path)
    spec = load_spec(projroot)
    if base.endswith('.h'):
        _write(out_path, _gen_cpp_header(spec))
    elif base.endswith('_unpack.inc'):
        _write(out_path, _gen_cpp_unpack(spec))
    else:
        raise RuntimeError(
            f'gen_scene_asset_set_cpp got unexpected output name: {base!r}.'
        )


def _cppheader() -> list[str]:
    return [
        '// Released under the MIT License. See LICENSE for details.',
        '//',
        '// AUTO-GENERATED by `tools/pcommand gen_scene_asset_set_cpp`.',
        '// DO NOT EDIT BY HAND.',
        '//',
        '// Generated from src/codegen/bascenev1codegen/scene_assets.py.',
    ]


def _gen_cpp_header(spec: SceneAssetSpec) -> str:
    guard = 'BALLISTICA_SCENE_V1_GENERATED_SCENE_ASSET_SET_H_'
    out = _cppheader() + [
        '',
        f'#ifndef {guard}',
        f'#define {guard}',
        '',
        '#include "ballistica/base/assets/mesh_asset.h"',
        '#include "ballistica/base/assets/sound_asset.h"',
        '#include "ballistica/base/assets/texture_asset.h"',
        '#include "ballistica/shared/foundation/object.h"',
        '',
        'namespace ballistica::scene_v1 {',
        '',
        '/// Assets the node layer draws itself with, supplied by the',
        '/// active app-mode (see bascenev1.set_scene_asset_set) and',
        '/// wiped at app-mode switches. Members are base-level engine',
        '/// assets (nodes draw these client-locally; they are not',
        '/// scene-stream assets).',
        f'struct {TOP_CLASS} {{',
    ]
    for i, group in enumerate(spec.groups):
        if i:
            out.append('')
        out += _wrap(f'-- {group.doc}', '  /// ')
        for slot in group.slots:
            cpptype = KIND_INFO[slot.kind].cpptype
            out.append(f'  /// {slot.doc}')
            out.append(f'  Object::Ref<{cpptype}> {slot.name};')
    allslots = [s for _g, s in _slots(spec)]
    out += [
        '',
        '  /// True once every member has been supplied.',
        '  auto complete() const -> bool {',
        '    return '
        + '\n           && '.join(f'{s.name}.exists()' for s in allslots)
        + ';',
        '  }',
        '};',
        '',
        '}  // namespace ballistica::scene_v1',
        '',
        f'#endif  // {guard}',
    ]
    return '\n'.join(out) + '\n'


def _gen_cpp_unpack(spec: SceneAssetSpec) -> str:
    pairs = _slots(spec)
    n = len(pairs)
    out = _cppheader() + [
        '',
        f'// Body of {TOP_CLASS}FromPyArgs(); included from a',
        '// hand-written .cc so the build need not predict generated',
        '// .cc files (see docs/design/codegen.md).',
        '',
        '// Args arrive positionally in spec order; the Python-side',
        '// wrapper that sends them is generated from the same spec.',
        '// Each is an asset *handle*; its private (_apverid, _name)',
        '// parts are read here and the base-level asset loaded from',
        '// them -- the sanctioned boundary for those attrs (see',
        '// batools.scene_assets).',
    ]
    for i in range(n):
        out.append(f'PyObject* a{i};')
    out.append('static const char* kFmt =')
    for i in range(0, n, 10):
        chunk = 'O' * len(range(i, min(i + 10, n)))
        end = ';' if i + 10 >= n else ''
        out.append(f'    "{chunk}"{end}')
    out += [
        'if (!PyArg_ParseTuple(',
        '        args, kFmt,',
    ]
    for i in range(0, n, 8):
        args = ', '.join(f'&a{j}' for j in range(i, min(i + 8, n)))
        end = ')) {' if i + 8 >= n else ','
        out.append(f'        {args}{end}')
    out += [
        '  return false;',
        '}',
        'base::Assets::AssetListLock lock;',
    ]
    for i, (_group, slot) in enumerate(pairs):
        loader = KIND_INFO[slot.kind].loader
        out += [
            '{',
            f'  PythonRef h(a{i}, PythonRef::kAcquire);',
            f'  out->{slot.name} = g_base->assets->{loader}(',
            '      h.GetAttr("_apverid").ValueAsString(),',
            '      h.GetAttr("_name").ValueAsString());',
            '}',
        ]
    out.append('return true;')
    return '\n'.join(out) + '\n'


def _write(outpath: str, contents: str) -> None:
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    existing: str | None = None
    if os.path.exists(outpath):
        with open(outpath, encoding='utf-8') as infile:
            existing = infile.read()
    if existing == contents:
        return
    with open(outpath, 'w', encoding='utf-8') as outfile:
        outfile.write(contents)
