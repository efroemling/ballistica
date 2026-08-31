# Released under the MIT License. See LICENSE for details.
#
"""Codegen for the ui_v1 asset set.

Reads a spec module (``bauiv1codegen.ui_assets``) naming every asset
the ui_v1 widget layer draws itself with, and emits:

* ``bauiv1/_generated/ui_asset_set.py`` -- the mutable ``UIAssetSet``
  class an app-mode builds (as part of its app-mode config) and the
  ``set_ui_asset_set()`` function that applies one.
* ``ui_v1/generated/ui_asset_set.h`` -- the C++ structs holding the
  resolved assets.
* ``ui_v1/generated/ui_asset_set_unpack.inc`` -- the Python-object ->
  struct unpacker, ``#include``-d from a hand-written ``.cc``.

Generating all three from one spec is the whole point: the unpacker is
the real drift surface (it is what ties a Python attr name to a
struct member), so hand-writing it would relocate the sync problem
rather than remove it. With it generated, a renamed or dropped slot is
a compile error at every C++ use site *and* a type error at the Python
site that builds the set.

Type definitions live here rather than in the spec module so that
spinoff projects which omit the ``ui_v1`` featureset still type-check
the codegen module cleanly, and so the spec module is
self-typecheckable in spinoffs that lack ``tools/batoolsinternal/``.
Same rationale as ``batools.android_messages``; see
``docs/design/spinoff.md``.

Not imported at runtime -- this is build-time only.

Groups
------
Slots are organized into named *groups* (``chrome``, ``toolbar``),
each emitted as its own dataclass/struct nested inside the top-level
set. Groups are a **logical** division of what the ui draws -- window
furniture versus the persistent toolbar -- and deliberately not a
division by which asset-package the art happens to live in. ui_v1
declares what it needs; filling those slots from one package or five
is entirely the supplying app-mode's business, and moving an asset
between packages must never change anything here.

Every group is required. A partially-supplied set is not
representable, which is what lets the C++ side treat every member as
non-null while widgets are drawing. If some group later becomes
genuinely optional (a ui with no toolbar at all), that is a
spec-level change -- make its field ``| None`` and give the struct a
presence flag -- rather than something callers can do by accident.

Where defaults live
-------------------
A slot's fallback art (for the slots ui_v1 has art of its own for) is
named in the spec as an attr path on the group's ``default_module``
(e.g. ``'textures.back_icon'``) and emitted into the generated
``UIAssetSet.__init__`` as plain attribute access on the wrapper
module. Every default is thus a real typed expression: rename an
asset and the wrapper attribute disappears, so mypy fails on the
regenerated module; add a slot with no default and every
``UIAssetSet(...)`` construction is missing an argument, so mypy
fails at the app-mode that builds one. Nothing can drift without a
type error, and no raw logical-path string ever reaches runtime.

Slots with defaults are also what makes restyling cheap: an app-mode
constructs a set supplying only the required slots and then reassigns
whichever defaulted attrs it wants changed, so new slots never break
existing skins.
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

    #: Python annotation for a slot of this kind (the loaded asset).
    pytype: str

    #: Python annotation for the *handle* form a slot holds (loaded
    #: lazily when the set is applied).
    handletype: str

    #: C++ asset type held in the struct.
    cpptype: str

    #: Python-class wrapper used to unpack one from a PyObject.
    pyclass: str

    #: Accessor on that wrapper yielding the underlying asset.
    accessor: str


KIND_INFO = {
    Kind.TEXTURE: _KindInfo(
        pytype='bauiv1.Texture',
        handletype='bauiv1.TextureHandle',
        cpptype='base::TextureAsset',
        pyclass='PythonClassUITexture',
        accessor='texture',
    ),
    Kind.MESH: _KindInfo(
        pytype='bauiv1.Mesh',
        handletype='bauiv1.MeshHandle',
        cpptype='base::MeshAsset',
        pyclass='PythonClassUIMesh',
        accessor='mesh',
    ),
    Kind.SOUND: _KindInfo(
        pytype='bauiv1.Sound',
        handletype='bauiv1.SoundHandle',
        cpptype='base::SoundAsset',
        pyclass='PythonClassUISound',
        accessor='sound',
    ),
}


@dataclass
class Slot:
    """One asset the ui_v1 widget layer needs supplied to it."""

    #: Field name on both sides (snake_case); also the C++ member name.
    name: str

    #: What kind of asset this slot holds.
    kind: Kind

    #: One-line description, emitted as docs on both sides.
    doc: str

    #: Attr path of this slot's fallback art on the group's
    #: ``default_module``, e.g. ``'textures.window_hsmall_vmed'``. The
    #: generator emits it as plain attribute access, so a wrong path is
    #: a type error in the generated module rather than a runtime
    #: surprise. Deliberately *not* derived from ``name`` -- a slot and
    #: the asset backing it are free to be named differently.
    #:
    #: ``None`` means ui_v1 has no art of its own for this slot, so
    #: whoever builds the set must supply it.
    default: str | None = None


@dataclass
class Group:
    """A logical grouping of slots, emitted as its own nested type."""

    #: Field name of the group on the top-level set (snake_case).
    name: str

    #: One-line description of what this group covers.
    doc: str

    #: The slots it holds.
    slots: list[Slot] = field(default_factory=list)

    #: Wrapper module the slots' ``default`` paths hang off, imported
    #: by the generated module. Required if any slot has a default.
    default_module: str | None = None

    def all_defaulted(self) -> bool:
        """Whether every slot here has fallback art.

        Only then can the group as a whole be omitted when building a
        set.
        """
        return all(s.default is not None for s in self.slots)

    def clsname(self) -> str:
        """The generated class/struct name for this group."""
        return (
            ''.join(p.capitalize() for p in self.name.split('_')) + 'AssetSet'
        )


@dataclass
class UIAssetSpec:
    """The complete set of assets ui_v1 needs supplied to it."""

    groups: list[Group] = field(default_factory=list)


#: Top-level Python class / C++ struct name.
TOP_CLASS = 'UIAssetSet'


def load_spec(projroot: str) -> UIAssetSpec:
    """Import the spec module and return its spec."""
    sys.path.insert(0, os.path.abspath(os.path.join(projroot, 'src/codegen')))
    try:
        # Avoid cached import in tests.
        if 'bauiv1codegen.ui_assets' in sys.modules:
            importlib.reload(sys.modules['bauiv1codegen.ui_assets'])
        mod = importlib.import_module('bauiv1codegen.ui_assets')
    finally:
        sys.path.pop(0)
    spec: UIAssetSpec = mod.SPEC

    if not spec.groups:
        raise RuntimeError('ui-asset spec is empty.')
    seen: set[str] = set()
    seengroups: set[str] = set()
    for group in spec.groups:
        if not group.slots:
            raise RuntimeError(f'ui-asset group {group.name} is empty.')
        if group.name in seengroups:
            raise RuntimeError(f'Duplicate ui-asset group: {group.name}.')
        seengroups.add(group.name)
        if any(s.default is not None for s in group.slots):
            if group.default_module is None:
                raise RuntimeError(
                    f'ui-asset group {group.name} has slot defaults but no'
                    f' default_module.'
                )
        for slot in group.slots:
            # Textures and meshes share one field namespace on both
            # sides, so a collision across kinds would silently drop a
            # slot. Names are checked across *all* groups so that a slot
            # moving between groups can never briefly exist in both.
            if slot.name in seen:
                raise RuntimeError(f'Duplicate ui-asset slot name: {slot.name}')
            seen.add(slot.name)
    return spec


def _wrap(text: str, prefix: str) -> list[str]:
    """Wrap one doc line to fit our line-length limit."""
    return textwrap.wrap(
        text,
        width=79 - len(prefix),
        initial_indent=prefix,
        subsequent_indent=prefix,
    )


def _slots(spec: 'UIAssetSpec') -> list[tuple['Group', 'Slot']]:
    """Every slot in spec order, paired with its group."""
    return [(g, s) for g in spec.groups for s in g.slots]


def generate_python(projroot: str, out_path: str) -> None:
    """Emit the UIAssetSet class and the apply function app-modes call."""
    spec = load_spec(projroot)
    pairs = _slots(spec)

    out = [
        '# Released under the MIT License. See LICENSE for details.',
        '#',
        '# AUTO-GENERATED by `tools/pcommand gen_ui_asset_set_py`.',
        '# DO NOT EDIT BY HAND.',
        '#',
        '# Generated from src/codegen/bauiv1codegen/ui_assets.py.',
        '"""Supplying ui_v1 with the assets it draws itself with."""',
        '',
        'from typing import TYPE_CHECKING',
        '',
        'import _bauiv1',
        '',
    ]
    # Wrapper modules the initial values hang off. Imported for real
    # (not under TYPE_CHECKING) since the init lines call into them;
    # importing a wrapper only builds its tree, it loads no assets.
    for mod in dict.fromkeys(
        g.default_module for g in spec.groups if g.default_module
    ):
        out.append(f'from bauiv1 import {mod}')
    out += [
        '',
        'if TYPE_CHECKING:',
        '    import bauiv1',
        '',
        '',
        f'class {TOP_CLASS}:',
        '    """The assets the ui_v1 widget layer draws itself with.',
        '',
        '    An app-mode that uses ui_v1 builds one of these (normally as',
        '    part of the config returned by its',
        '    :meth:`~babase.AppMode.new_app_mode_config`) and hands it to',
        '    :func:`bauiv1.set_ui_asset_set` when activating; this is what',
        '    lets an app-mode skin the ui. Supplying the art this way,',
        '    rather than ui_v1 reaching for it itself, is what keeps ui_v1',
        '    ignorant of which asset-packages the art lives in.',
        '',
        '    Slots hold asset *handles* (e.g.',
        '    :class:`~bauiv1.TextureHandle`), not loaded assets; nothing',
        '    loads until the set is applied at activation, so art that a',
        '    mode subclass or plugin replaces is never loaded at all.',
        '',
        '    Slots ui_v1 has no art of its own for are constructor',
        '    arguments, so a set is complete by construction. The rest',
        '    start out at ui_v1\'s own art. All slots are plain mutable',
        '    attributes, so an app-mode subclass or plugin amending a',
        '    config can restyle any of them before the set is applied.',
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
    required = [(g, s) for g, s in pairs if s.default is None]
    out += [
        '',
        '    def __init__(',
        '        self,',
        '        *,',
    ]
    for _group, slot in required:
        htype = KIND_INFO[slot.kind].handletype
        out.append(f'        {slot.name}: {htype},')
    out += [
        '    ) -> None:',
        '        # pylint: disable=too-many-arguments',
        '        # pylint: disable=too-many-statements',
    ]
    for _group, slot in required:
        out.append(f'        self.{slot.name} = {slot.name}')
    fills = [(g, s) for g, s in pairs if s.default is not None]
    if fills:
        out.append('')
        out.append('        # Slots ui_v1 has art of its own for start at it')
        out.append('        # (handles only; nothing is loaded here).')
    for group, slot in fills:
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
        f'def set_ui_asset_set(assets: {TOP_CLASS}) -> None:',
        '    """Supply the assets the ui_v1 widget layer draws itself with.',
        '',
        '    Called by an app-mode during activation (normally from',
        '    :meth:`~babase.AppMode.on_activate`, with the',
        f'    :class:`{TOP_CLASS}` carried by its app-mode config), before',
        '    asking the native layer to activate the mode -- ui_v1 reads',
        '    the set as it builds its widgets. Calling more than once is',
        '    fine: the last call before an activation is the one that',
        '    takes effect. Note that a call made while ui_v1 is already',
        '    active does not restyle the live ui; it applies at the next',
        '    activation (which happens on every session change).',
        '',
        '    The supplied art is wiped by ui_v1\'s app-subsystem',
        '    :meth:`~babase.AppSubsystem.reset` at every app-mode switch,',
        '    so a mode can never inherit a previous mode\'s art. A',
        '    ui-using mode that never supplies its own gets a disabled',
        '    (\'zombie\') ui and a logged error rather than a crash.',
        '    """',
        '    # This is where loading actually happens: slots hold handles',
        '    # until applied, so replaced defaults are never loaded.',
        '    # Positional, in spec order -- the native side is generated',
        '    # from the same spec, so the two cannot drift.',
        '    loaded: list[bauiv1.Texture | bauiv1.Mesh | bauiv1.Sound] = []',
        '    for name, handle in (',
    ]
    for _group, slot in pairs:
        flat = f"        ('{slot.name}', assets.{slot.name}),"
        if len(flat) <= 79:
            out.append(flat)
        else:
            out += [
                '        (',
                f"            '{slot.name}',",
                f'            assets.{slot.name},',
                '        ),',
            ]
    out += [
        '    ):',
        '        try:',
        '            loaded.append(handle.get())',
        '        except Exception as exc:',
        '            # The chained error names the exact asset and',
        '            # package; the slot is what it cannot know.',
        '            raise RuntimeError(',
        "                f'Error loading the ui asset for slot {name!r}.'",
        '            ) from exc',
        '    _bauiv1.set_ui_asset_set_native(*loaded)',
    ]

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
            f'gen_ui_asset_set_cpp got unexpected output name: {base!r}.'
        )


def _cppheader() -> list[str]:
    return [
        '// Released under the MIT License. See LICENSE for details.',
        '//',
        '// AUTO-GENERATED by `tools/pcommand gen_ui_asset_set_cpp`.',
        '// DO NOT EDIT BY HAND.',
        '//',
        '// Generated from src/codegen/bauiv1codegen/ui_assets.py.',
    ]


def _gen_cpp_header(spec: UIAssetSpec) -> str:
    guard = 'BALLISTICA_UI_V1_GENERATED_UI_ASSET_SET_H_'
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
        'namespace ballistica::ui_v1 {',
        '',
        '/// Assets the widget layer draws itself with, supplied by the',
        '/// active app-mode (see bauiv1.set_ui_asset_set) and wiped at',
        '/// app-mode switches (UIV1AppSubsystem.reset()). An incomplete',
        '/// set at activation means the ui goes into zombie mode and',
        '/// builds no widgets, so members are never null while widgets',
        '/// are drawing.',
        f'struct {TOP_CLASS} {{',
    ]
    for i, group in enumerate(spec.groups):
        if i:
            # No blank line right after the opening brace.
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
        '}  // namespace ballistica::ui_v1',
        '',
        f'#endif  // {guard}',
    ]
    return '\n'.join(out) + '\n'


def _gen_cpp_unpack(spec: UIAssetSpec) -> str:
    pairs = _slots(spec)
    n = len(pairs)
    out = _cppheader() + [
        '',
        f'// Body of {TOP_CLASS}FromPyArgs(); included from a hand-written',
        '// .cc so the build need not predict generated .cc files (see',
        '// docs/design/codegen.md "Caveat: .cc generation").',
        '',
        '// Args arrive positionally in spec order; the Python-side',
        '// wrapper that sends them is generated from the same spec.',
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
    ]
    for i, (_group, slot) in enumerate(pairs):
        info = KIND_INFO[slot.kind]
        out += [
            '{',
            f'  if (!{info.pyclass}::Check(a{i})) {{',
            '    throw Exception(',
            f'        "Bad type for ui asset \'{slot.name}\';",',
            '        PyExcType::kType);',
            '  }',
            f'  out->{slot.name} =',
            f'      &{info.pyclass}::FromPyObj(a{i}).{info.accessor}();',
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
