# Released under the MIT License. See LICENSE for details.
#
"""Codegen for the base asset set.

The third sibling of :mod:`batools.ui_assets` and
:mod:`batools.scene_assets` (see those for the shared reasoning).
Reads ``babasecodegen.base_assets`` and emits:

* ``babase/_generated/base_asset_set.py`` -- the ``BaseAssetSet``
  class an app-mode carries on its config and hands to
  ``babase.set_base_asset_set()``.
* ``base/generated/base_asset_set.h`` -- the C++ struct.
* ``base/generated/base_asset_set_unpack.inc`` -- the unpacker
  (handle-attr style, like the scene flavor).
* ``base/generated/base_asset_set_placeholders.inc`` -- the
  placeholder fill, unique to this set.

The placeholder fill is what makes base different from ui/scene:
base draws *before and between* app-modes (boot, construct-mode,
mode switches), so its set can never be allowed to be incomplete.
Instead of zombie guards in hot draw paths, every slot an app-mode
leaves unsupplied holds a placeholder, and the set is *restored* to
placeholders -- not cleared -- at app-mode switches. Placeholders are
chosen by slot kind and need no asset-package art: solid white
textures and black cube maps the engine generates itself, plus the
builtin ``image1x1`` mesh and ``blank`` sound (which the engine keeps
builtin for its own use anyway). A mode that supplies nothing gets a
plain world rather than crashes or another mode's art; a black cube
map specifically makes missing reflections a no-op, since reflections
are additive.

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
    CUBE_MAP_TEXTURE = 'cube_map_texture'
    MESH = 'mesh'
    SOUND = 'sound'


@dataclass(frozen=True)
class _KindInfo:
    """Per-kind bits the emitters need."""

    #: Python annotation for the handle form a slot holds.
    handletype: str

    #: C++ asset type held in the struct.
    cpptype: str

    #: Assets:: accessor loading one from (package key, name).
    loader: str

    #: Assets:: call (from inside Assets) giving this kind's placeholder.
    #: Boot-safe and package-free, or as good as: only things the engine
    #: generates or keeps builtin for its own use.
    placeholder: str


KIND_INFO = {
    Kind.TEXTURE: _KindInfo(
        handletype='TextureSpec',
        cpptype='base::TextureAsset',
        loader='GetPackageTexture',
        placeholder='SolidTexture(SolidTextureColor::kWhite)',
    ),
    Kind.CUBE_MAP_TEXTURE: _KindInfo(
        handletype='CubeMapTextureSpec',
        cpptype='base::TextureAsset',
        loader='GetPackageCubeMapTexture',
        placeholder='SolidCubeMapTexture(SolidTextureColor::kBlack)',
    ),
    Kind.MESH: _KindInfo(
        handletype='MeshSpec',
        cpptype='base::MeshAsset',
        loader='GetPackageMesh',
        placeholder='BuiltinMesh(BuiltinMeshID::kMeshesImage1x1)',
    ),
    Kind.SOUND: _KindInfo(
        handletype='SoundSpec',
        cpptype='base::SoundAsset',
        loader='GetPackageSound',
        placeholder='BuiltinSound(BuiltinSoundID::kAudioBlank)',
    ),
}


@dataclass
class Slot:
    """One asset base's classic-flavored draw paths need supplied."""

    #: Field name on both sides (snake_case); also the C++ member name.
    name: str

    #: What kind of asset this slot holds.
    kind: Kind

    #: One-line description, emitted as docs on both sides.
    doc: str


@dataclass
class Group:
    """A logical grouping of slots, emitted as section comments."""

    #: Group name (snake_case).
    name: str

    #: One-line description of what this group covers.
    doc: str

    #: The slots it holds.
    slots: list[Slot] = field(default_factory=list)


@dataclass
class BaseAssetSpec:
    """The complete set of assets base needs supplied to it."""

    groups: list[Group] = field(default_factory=list)


#: Top-level Python class / C++ struct name.
TOP_CLASS = 'BaseAssetSet'


def load_spec(projroot: str) -> BaseAssetSpec:
    """Import the spec module and return its spec."""
    sys.path.insert(0, os.path.abspath(os.path.join(projroot, 'src/codegen')))
    try:
        # Avoid cached import in tests.
        if 'babasecodegen.base_assets' in sys.modules:
            importlib.reload(sys.modules['babasecodegen.base_assets'])
        mod = importlib.import_module('babasecodegen.base_assets')
    finally:
        sys.path.pop(0)
    spec: BaseAssetSpec = mod.SPEC

    if not spec.groups:
        raise RuntimeError('base-asset spec is empty.')
    seen: set[str] = set()
    for group in spec.groups:
        if not group.slots:
            raise RuntimeError(f'base-asset group {group.name} is empty.')
        for slot in group.slots:
            if slot.name in seen:
                raise RuntimeError(
                    f'Duplicate base-asset slot name: {slot.name}'
                )
            seen.add(slot.name)
    return spec


def _slots(spec: BaseAssetSpec) -> list[tuple[Group, Slot]]:
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
    """Emit the BaseAssetSet class and the apply function."""
    spec = load_spec(projroot)
    pairs = _slots(spec)

    out = [
        '# Released under the MIT License. See LICENSE for details.',
        '#',
        '# AUTO-GENERATED by `tools/pcommand gen_base_asset_set_py`.',
        '# DO NOT EDIT BY HAND.',
        '#',
        '# Generated from src/codegen/babasecodegen/base_assets.py.',
        '"""Supplying base with the assets its classic-flavored art'
        ' uses."""',
        '',
        'from typing import TYPE_CHECKING',
        '',
        'import _babase',
        '',
        'if TYPE_CHECKING:',
        # Slots are annotated with the *spec base types*: the set's
        # contract is exactly a spec (a package id + name pair), so any
        # wrapper flavor's handle satisfies it -- classic supplies
        # bascenev1-flavor handles, and every flavor's handles are spec
        # subclasses.
        '    from bacommon.assetspec import (',
        '        CubeMapTextureSpec,',
        '        MeshSpec,',
        '        SoundSpec,',
        '        TextureSpec,',
        '    )',
        '',
        '',
        f'class {TOP_CLASS}:',
        '    """Assets for the classic-flavored art baked into base.',
        '',
        '    Base draws a few things whose *look* belongs to the classic',
        '    game -- explosion debris, smoke, the VR boxing-glove hands,',
        '    the reflection environment maps -- but whose draw code is',
        '    engine-level. An app-mode carries one of these on its',
        '    app-mode config and hands it to',
        '    :func:`babase.set_base_asset_set` when activating to supply',
        '    that art.',
        '',
        '    Slots hold asset *references* (any wrapper flavor works);',
        '    nothing loads until the set is applied. A slot left at',
        '    ``None`` gets a neutral placeholder the engine provides',
        '    itself (white texture, black cube map, flat quad mesh,',
        '    silent sound), so a bare ``BaseAssetSet()`` renders a plain',
        '    but coherent world: white debris, no reflections (a black',
        '    cube map contributes nothing, since reflections are',
        '    additive).',
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
            out.append(f'    {slot.name}: {htype} | None')
    out += [
        '',
        '    def __init__(self) -> None:',
        '        # All slots start unsupplied (engine placeholders).',
    ]
    for _group, slot in pairs:
        out.append(f'        self.{slot.name} = None')
    out += [
        '',
        '',
        f'def set_base_asset_set(assets: {TOP_CLASS}) -> None:',
        '    """Supply the art for base\'s classic-flavored draw paths.',
        '',
        '    Called by an app-mode during activation (normally from',
        '    :meth:`~babase.AppMode.on_activate`, with the',
        f'    :class:`{TOP_CLASS}` carried by its app-mode config).',
        '',
        '    Loading happens native-side as the set is applied. Slots',
        '    left at ``None`` get engine placeholders. At every app-mode',
        '    switch the native set is *restored to placeholders* (not',
        '    cleared -- base draws between modes too), so a mode can',
        "    never inherit a previous mode's art.",
        '    """',
        '    # Positional, in spec order -- the native side is generated',
        '    # from the same spec, so the two cannot drift.',
        '    _babase.set_base_asset_set_native(',
    ]
    for _group, slot in pairs:
        out.append(f'        assets.{slot.name},')
    out += ['    )']

    _write(out_path, '\n'.join(out).rstrip('\n') + '\n')


def generate_cpp(projroot: str, out_path: str) -> None:
    """Emit one of the C++ outputs."""
    base = os.path.basename(out_path)
    spec = load_spec(projroot)
    if base.endswith('.h'):
        _write(out_path, _gen_cpp_header(spec))
    elif base.endswith('_unpack.inc'):
        _write(out_path, _gen_cpp_unpack(spec))
    elif base.endswith('_placeholders.inc'):
        _write(out_path, _gen_cpp_placeholders(spec))
    else:
        raise RuntimeError(
            f'gen_base_asset_set_cpp got unexpected output name: {base!r}.'
        )


def _cppheader() -> list[str]:
    return [
        '// Released under the MIT License. See LICENSE for details.',
        '//',
        '// AUTO-GENERATED by `tools/pcommand gen_base_asset_set_cpp`.',
        '// DO NOT EDIT BY HAND.',
        '//',
        '// Generated from src/codegen/babasecodegen/base_assets.py.',
    ]


def _gen_cpp_header(spec: BaseAssetSpec) -> str:
    guard = 'BALLISTICA_BASE_GENERATED_BASE_ASSET_SET_H_'
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
        'namespace ballistica::base {',
        '',
        '/// Warn (once per slot) that a base asset slot handed out its',
        '/// placeholder. Defined in assets.cc.',
        'void NoteBaseAssetPlaceholderUse(const char* slot);',
        '',
        '/// Classic-flavored art base draws itself with, supplied by',
        '/// the active app-mode (see babase.set_base_asset_set).',
        '/// Boot-filled with neutral engine placeholders and restored',
        '/// to them at app-mode switches (and any slot a mode leaves',
        '/// unsupplied gets one), so it is never incomplete -- base',
        '/// draws before and between app-modes.',
        '///',
        '/// Read slots through their accessors (``smoke()``, ...), not',
        '/// the ``*_ref`` members: an accessor warns (once per slot) when',
        '/// what it hands back is a placeholder, so art that never got',
        '/// supplied shows up in the log rather than as an unexplained',
        '/// white flash.',
        f'struct {TOP_CLASS} {{',
    ]
    allslots = [s for _g, s in _slots(spec)]
    if len(allslots) > 64:
        raise RuntimeError('base-asset placeholder bits overflow uint64_t.')
    index = 0
    for i, group in enumerate(spec.groups):
        if i:
            out.append('')
        out += _wrap(f'-- {group.doc}', '  /// ')
        for slot in group.slots:
            cpptype = KIND_INFO[slot.kind].cpptype
            out += [
                f'  /// {slot.doc}',
                f'  auto {slot.name}() const -> {cpptype}* {{',
                f'    if (placeholders & (uint64_t{{1}} << {index})) {{',
                f'      NoteBaseAssetPlaceholderUse("{slot.name}");',
                '    }',
                f'    return {slot.name}_ref.get();',
                '  }',
            ]
            if slot.kind is Kind.SOUND:
                # Sounds can simply be skipped, which beats a silent
                # placeholder for things that may fire before any
                # app-mode supplies the set (device jingles).
                out += [
                    '  /// The same, or nullptr (and no warning) while it',
                    '  /// holds its placeholder.',
                    f'  auto {slot.name}_if_supplied() const -> {cpptype}* {{',
                    f'    return (placeholders & (uint64_t{{1}} << {index}))',
                    '               ? nullptr',
                    f'               : {slot.name}_ref.get();',
                    '  }',
                ]
            out += [f'  Object::Ref<{cpptype}> {slot.name}_ref;']
            index += 1
    out += [
        '',
        '  /// Bit per slot (spec order): set while it holds a placeholder.',
        '  uint64_t placeholders{};',
        '',
        '  /// True once every member has been supplied.',
        '  auto complete() const -> bool {',
        '    return '
        + '\n           && '.join(f'{s.name}_ref.exists()' for s in allslots)
        + ';',
        '  }',
        '};',
        '',
        '}  // namespace ballistica::base',
        '',
        f'#endif  // {guard}',
    ]
    return '\n'.join(out) + '\n'


def _gen_cpp_unpack(spec: BaseAssetSpec) -> str:
    pairs = _slots(spec)
    n = len(pairs)
    out = _cppheader() + [
        '',
        f'// Body of {TOP_CLASS}FromPyArgs(); included from a',
        '// hand-written .cc so the build need not predict generated',
        '// .cc files (see docs/design/codegen.md).',
        '',
        '// Args arrive positionally in spec order; each is an asset',
        '// handle whose private (_apvernum, _name) parts are read here',
        '// and the base-level asset loaded from them (the sanctioned',
        '// boundary for those attrs; see batools.scene_assets), or',
        '// None, which leaves the slot empty for the placeholder fill.',
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
        'Assets::AssetListLock lock;',
    ]
    for i, (_group, slot) in enumerate(pairs):
        loader = KIND_INFO[slot.kind].loader
        out += [
            f'if (a{i} != Py_None) {{',
            f'  PythonRef h(a{i}, PythonRef::kAcquire);',
            f'  out->{slot.name}_ref = g_base->assets->{loader}(',
            '      std::to_string(h.GetAttr("_apvernum").ValueAsInt()),',
            '      h.GetAttr("_name").ValueAsString());',
            '}',
        ]
    out.append('return true;')
    return '\n'.join(out) + '\n'


def _gen_cpp_placeholders(spec: BaseAssetSpec) -> str:
    out = _cppheader() + [
        '',
        f'// Body of the {TOP_CLASS} placeholder fill; included from',
        '// a hand-written Assets method. Fills every empty slot in',
        "// 'out' with its kind's engine placeholder (package-free and",
        '// boot-safe). This is what keeps the set complete before and',
        '// between app-modes; see batools.base_assets.',
    ]
    for index, (_group, slot) in enumerate(_slots(spec)):
        expr = KIND_INFO[slot.kind].placeholder
        out += [
            f'if (!out->{slot.name}_ref.exists()) {{',
            f'  out->{slot.name}_ref = {expr};',
            f'  out->placeholders |= uint64_t{{1}} << {index};',
            '}',
        ]
    return '\n'.join(out) + '\n'


def _write(outpath: str, contents: str) -> None:
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    existing: str | None = None
    if os.path.exists(outpath):
        with open(outpath, encoding='utf-8') as infile:
            existing = infile.read()
    if existing == contents:
        # Leave the bytes alone (no spurious rebuilds downstream) but
        # bump the mtime so make sees the target as newer than the
        # spec; otherwise a spec change that leaves this output
        # unchanged keeps it perpetually 'out of date'.
        os.utime(outpath, None)
        return
    with open(outpath, 'w', encoding='utf-8') as outfile:
        outfile.write(contents)
