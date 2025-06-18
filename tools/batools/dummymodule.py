# Released under the MIT License. See LICENSE for details.
#
# pylint: disable=too-many-lines

"""Generates dummy .py modules based on binary modules.

This allows us to use code introspection tools such as pylint without spinning
up the engine, and also allows external scripts to import game scripts
successfully (albeit with limited functionality).
"""

from __future__ import annotations

import os

import types
import textwrap
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from efro.error import CleanError
from efro.terminal import Clr

if TYPE_CHECKING:
    from types import ModuleType
    from typing import Sequence, Any, Literal

    from batools.docs import AttributeInfo


class DummyModuleDef:
    """Defines custom dummy module generation behavior."""


def _get_varying_func_info(sig_in: str) -> tuple[str, str]:
    """Return overloaded signatures and return statements for varying funcs."""
    returns = 'return None'
    if sig_in == (
        'getdelegate(self, type: type,' ' doraise: bool = False) -> <varies>'
    ):
        sig = (
            '# Show that ur return type varies based on "doraise" value:\n'
            '@overload\n'
            'def getdelegate[T](self, type: type[T],'
            ' doraise: Literal[False] = False) -> T | None:\n'
            '    ...\n'
            '\n'
            '@overload\n'
            'def getdelegate[T](self, type: type[T],'
            ' doraise: Literal[True]) -> T:\n'
            '    ...\n'
            '\n'
            'def getdelegate(self, type: Any,'
            ' doraise: bool = False) -> Any:\n'
        )
    elif sig_in == (
        'getinputdevice(name: str, unique_id:'
        ' str, doraise: bool = True)   -> <varies>'
    ):
        sig = (
            '# Show that our return type varies based on "doraise" value:\n'
            '@overload\n'
            'def getinputdevice(name: str, unique_id: str,'
            ' doraise: Literal[True] = True) -> bascenev1.InputDevice:\n'
            '    ...\n'
            '\n'
            '@overload\n'
            'def getinputdevice(name: str, unique_id: str,'
            ' doraise: Literal[False]) -> bascenev1.InputDevice | None:\n'
            '    ...\n'
            '\n'
            'def getinputdevice(name: str, unique_id: str,'
            ' doraise: bool=True) -> Any:\n'
        )
    elif sig_in == 'getactivity(doraise: bool = True) -> <varies>':
        sig = (
            '# Show that our return type varies based on "doraise" value:\n'
            '@overload\n'
            'def getactivity(doraise: Literal[True] = True) ->'
            ' bascenev1.Activity:\n'
            '    ...\n'
            '\n'
            '\n'
            '@overload\n'
            'def getactivity(doraise: Literal[False])'
            ' -> bascenev1.Activity | None:\n'
            '    ...\n'
            '\n'
            '\n'
            'def getactivity(doraise: bool = True)'
            ' -> bascenev1.Activity | None:\n'
        )
    elif sig_in == 'getsession(doraise: bool = True) -> <varies>':
        sig = (
            '# Show that our return type varies based on "doraise" value:\n'
            '@overload\n'
            'def getsession(doraise: Literal[True] = True) ->'
            ' bascenev1.Session:\n'
            '    ...\n'
            '\n'
            '\n'
            '@overload\n'
            'def getsession(doraise: Literal[False])'
            ' -> bascenev1.Session | None:\n'
            '    ...\n'
            '\n'
            '\n'
            'def getsession(doraise: bool = True)'
            ' -> bascenev1.Session | None:\n'
        )

    else:
        raise RuntimeError(
            f'Unimplemented varying func: {Clr.RED}{sig_in}{Clr.RST}'
        )
    return sig, returns


def _writefuncs(
    parent: Any,
    funcnames: Sequence[str],
    indent: int,
    spacing: int,
    as_method: bool,
) -> str:
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-locals
    out = ''
    spcstr = '\n' * spacing
    indstr = ' ' * indent
    for funcname in funcnames:
        # Skip some that are not in public builds.
        if funcname in {'master_hash_dump'}:
            continue

        func = getattr(parent, funcname)

        # Classmethods on classes have type BuiltinMethodType instead
        # of the usual MethodDescriptorType; treat them special.
        is_classmethod = isinstance(
            getattr(parent, funcname), types.BuiltinMethodType
        ) and isinstance(parent, type)

        docstr = func.__doc__

        # We expect an empty line and take everything before that to be
        # the function signature.
        if '\n\n' not in docstr:
            raise RuntimeError(f'docstr missing empty line: {func}')
        sig = docstr.split('\n\n', maxsplit=1)[0].replace('\n', ' ').strip()

        # Make sure supplied signature matches the filtered function name.
        if not sig.startswith(f'{funcname}('):
            raise RuntimeError(
                f'Expected signature for function {funcname} to start'
                f" with '{funcname}'."
            )

        # If these are methods, add self.
        if as_method:
            slf = 'cls' if is_classmethod else 'self'
            if funcname + '()' in sig:
                sig = sig.replace(f'{funcname}()', f'{funcname}({slf})')
            else:
                sig = sig.replace(f'{funcname}(', f'{funcname}({slf}, ')

        # We expect sig to have a -> denoting return type.
        if ' -> ' not in sig:
            raise RuntimeError(f'no "->" found in docstr for {funcname}')
        returns = sig.split('->')[-1].strip()

        # Some functions don't have simple signatures; we need to hard-code
        # those here with overloads and whatnot.
        if '<varies>' in sig:
            overloadsigs, returnstr = _get_varying_func_info(sig)
            defslines = textwrap.indent(overloadsigs, indstr)
        else:
            defslines = f'{indstr}def {sig}:\n'

            if is_classmethod:
                defslines = f'{indstr}@classmethod\n{defslines}'

            if funcname in {'quit', 'newnode', 'basetimer'}:
                defslines = (
                    f'{indstr}# noinspection PyShadowingBuiltins\n'
                    f'{defslines}'
                )

            if funcname in {'basetimer', 'timer'}:
                defslines = (
                    f'{indstr}# noinspection PyShadowingNames\n' f'{defslines}'
                )

            # Types can be strings for forward-declaration cases.
            if (returns[0] == "'" and returns[-1] == "'") or (
                returns[0] == '"' and returns[-1] == '"'
            ):
                returns = returns[1:-1]
            if returns == 'None':
                returnstr = 'return None'
            elif returns == 'babase.Lstr':
                returnstr = (
                    'import babase  # pylint: disable=cyclic-import\n'
                    "return babase.Lstr(value='')"
                )
            elif returns == 'babase.AppTime':
                returnstr = (
                    'import babase  # pylint: disable=cyclic-import\n'
                    'return babase.AppTime(0.0)'
                )
            elif returns == 'bascenev1.BaseTime':
                returnstr = (
                    'import bascenev1  # pylint: disable=cyclic-import\n'
                    'return bascenev1.BaseTime(0.0)'
                )
            elif returns == 'bascenev1.Time':
                returnstr = (
                    'import bascenev1  # pylint: disable=cyclic-import\n'
                    'return bascenev1.Time(0.0)'
                )
            elif returns == 'bascenev1.HostInfo | None':
                returnstr = (
                    'import bascenev1  # pylint: disable=cyclic-import\n'
                    'return bascenev1.HostInfo(\'dummyname\', -1,'
                    ' \'dummy_addr\', -1)'
                )
            elif returns == 'babase.DisplayTime':
                returnstr = (
                    'import babase  # pylint: disable=cyclic-import\n'
                    'return babase.DisplayTime(0.0)'
                )
            elif returns in {'bascenev1.Activity', 'bascenev1.Activity | None'}:
                returnstr = (
                    'import bascenev1  # pylint: disable=cyclic-import\nreturn '
                    + 'bascenev1.Activity(settings={})'
                )
            elif returns in {'bascenev1.Session', 'bascenev1.Session | None'}:
                returnstr = (
                    'import bascenev1  # pylint: disable=cyclic-import\nreturn '
                    + 'bascenev1.Session([])'
                )
            elif returns == 'bascenev1.SessionPlayer | None':
                returnstr = (
                    'import bascenev1  # pylint: disable=cyclic-import\n'
                    'return bascenev1.SessionPlayer()'
                )
            elif returns == 'bascenev1.Player | None':
                returnstr = (
                    'import bascenev1  # pylint: disable=cyclic-import\n'
                    'return bascenev1.Player()'
                )
            elif returns.startswith('babase.') and ' | None' not in returns:
                # We cant import babase at module level so let's
                # do it within funcs as needed.
                returnstr = (
                    f'import babase  # pylint: disable=cyclic-import\n'
                    f'return {returns}()'
                )
            elif returns.startswith('bascenev1.') and ' | None' not in returns:
                # We cant import babase at module level so let's
                # do it within funcs as needed.
                returnstr = (
                    f'import bascenev1  # pylint: disable=cyclic-import\n'
                    f'return {returns}()'
                )
            elif returns.startswith('bauiv1.') and ' | None' not in returns:
                # We cant import babase at module level so let's
                # do it within funcs as needed.
                returnstr = (
                    f'import bauiv1  # pylint: disable=cyclic-import\n'
                    f'return {returns}()'
                )

            elif returns in {'object', 'Any'}:
                # We use 'object' when we mean "can vary"
                # don't want pylint making assumptions in this case.
                returnstr = 'return _uninferrable()'
            elif returns == 'tuple[float, float]':
                returnstr = 'return (0.0, 0.0)'
            elif returns == 'tuple[float, float, float]':
                returnstr = 'return (0.0, 0.0, 0.0)'
            elif returns == 'str | None':
                returnstr = "return ''"
            elif returns == 'int | None':
                returnstr = 'return 0'
            elif returns == 'tuple[float, float, float, float]':
                returnstr = 'return (0.0, 0.0, 0.0, 0.0)'
            elif returns == 'bauiv1.Widget | None':
                returnstr = 'import bauiv1\nreturn bauiv1.Widget()'
            elif returns == 'bascenev1.InputDevice | None':
                returnstr = 'return InputDevice()'
            elif returns == 'list[bauiv1.Widget]':
                returnstr = 'import bauiv1\nreturn [bauiv1.Widget()]'
            elif returns == 'tuple[float, ...]':
                returnstr = 'return (0.0, 0.0, 0.0)'
            elif returns == 'list[str]':
                returnstr = "return ['blah', 'blah2']"
            elif returns == 'float | int':
                returnstr = 'return 0.0'
            elif returns == 'dict[str, Any]':
                returnstr = "return {'foo': 'bar'}"
            elif returns in {'tuple[int, int] | None', 'tuple[int, int]'}:
                returnstr = 'return (0, 0)'
            elif returns == 'list[dict[str, Any]]':
                returnstr = "return [{'foo': 'bar'}]"
            elif returns in {
                'session.Session',
                'team.Team',
                '_app.App',
                'appconfig.AppConfig',
            }:
                returnstr = (
                    'from babase import '
                    + returns.split('.')[0]
                    + '; return '
                    + returns
                    + '()'
                )
            elif returns in [
                'bool',
                'str',
                'int',
                'list',
                'dict',
                'tuple',
                'float',
                'SessionData',
                'ActivityData',
                'Player',
                'SessionPlayer',
                'InputDevice',
                'Sound',
                'Texture',
                'Mesh',
                'CollisionMesh',
                'SimpleSound',
                'team.Team',
                'Vec3',
                'Widget',
                'Node',
                'ContextRef',
            ]:
                returnstr = 'return ' + returns + '()'
            else:
                raise RuntimeError(
                    f'Unknown returns value: {returns} for {funcname}'
                )
            returnstr = (
                f'# This is a dummy stub;'
                f' the actual implementation is native code.\n{returnstr}'
            )

        returnspc = indstr + '    '
        returnstr = ('\n' + returnspc).join(returnstr.strip().splitlines())
        docstr_out = _formatdoc(
            _filterdoc(docstr, funcname=funcname), indent + 4, form='str'
        )
        out += spcstr + defslines + docstr_out + f'{returnspc}{returnstr}\n'
    return out


def _special_class_cases(classname: str) -> str:
    out = ''

    # Special case: define a fallback attr getter with a random
    # return type in cases where our class handles attrs itself.
    if classname in ['Vec3']:
        out += (
            '\n'
            '    # pylint: disable=function-redefined\n'
            '\n'
            '    @overload\n'
            '    def __init__(self) -> None:\n'
            '        pass\n'
            '\n'
            '    @overload\n'
            '    def __init__(self, value: float):\n'
            '        pass\n'
            '\n'
            '    @overload\n'
            '    def __init__(self, values: Sequence[float]):\n'
            '        pass\n'
            '\n'
            '    @overload\n'
            '    def __init__(self, x: float, y: float, z: float):\n'
            '        pass\n'
            '\n'
            '    def __init__(self, *args: Any, **kwds: Any):\n'
            '        pass\n'
            '\n'
            '    def __add__(self, other: Vec3) -> Vec3:\n'
            '        return self\n'
            '\n'
            '    def __sub__(self, other: Vec3) -> Vec3:\n'
            '        return self\n'
            '\n'
            '    @overload\n'
            '    def __mul__(self, other: float) -> Vec3:\n'
            '        return self\n'
            '\n'
            '    @overload\n'
            '    def __mul__(self, other: Sequence[float]) -> Vec3:\n'
            '        return self\n'
            '\n'
            '    def __mul__(self, other: Any) -> Any:\n'
            '        return self\n'
            '\n'
            '    @overload\n'
            '    def __rmul__(self, other: float) -> Vec3:\n'
            '        return self\n'
            '\n'
            '    @overload\n'
            '    def __rmul__(self, other: Sequence[float]) -> Vec3:\n'
            '        return self\n'
            '\n'
            '    def __rmul__(self, other: Any) -> Any:\n'
            '        return self\n'
            '\n'
            '    # (for index access)\n'
            '    @override\n'
            '    def __getitem__(self, typeargs: Any) -> Any:\n'
            '        return 0.0\n'
            '\n'
            '    @override\n'
            '    def __len__(self) -> int:\n'
            '        return 3\n'
            '\n'
            '    # (for iterator access)\n'
            '    @override\n'
            '    def __iter__(self) -> Any:\n'
            '        return self\n'
            '\n'
            '    def __next__(self) -> float:\n'
            '        return 0.0\n'
            '\n'
            '    def __neg__(self) -> Vec3:\n'
            '        return self\n'
            '\n'
            '    def __setitem__(self, index: int, val: float) -> None:\n'
            '        pass\n'
        )
    if classname in ['Node']:
        out += (
            '\n'
            '    # Note attributes:\n'
            '    # NOTE: I\'m just adding *all* possible node attrs here\n'
            '    # now now since we have a single bascenev1.Node type; in the\n'
            '    # future I hope to create proper individual classes\n'
            '    # corresponding to different node types with correct\n'
            '    # attributes per node-type.\n'
            '    color: Sequence[float] = (0.0, 0.0, 0.0)\n'
            '    size: Sequence[float] = (0.0, 0.0, 0.0)\n'
            '    position: Sequence[float] = (0.0, 0.0, 0.0)\n'
            '    position_center: Sequence[float] = (0.0, 0.0, 0.0)\n'
            '    position_forward: Sequence[float] = (0.0, 0.0, 0.0)\n'
            '    punch_position: Sequence[float] = (0.0, 0.0, 0.0)\n'
            '    punch_velocity: Sequence[float] = (0.0, 0.0, 0.0)\n'
            '    velocity: Sequence[float] = (0.0, 0.0, 0.0)\n'
            '    name_color: Sequence[float] = (0.0, 0.0, 0.0)\n'
            '    tint_color: Sequence[float] = (0.0, 0.0, 0.0)\n'
            '    tint2_color: Sequence[float] = (0.0, 0.0, 0.0)\n'
            "    text: babase.Lstr | str = ''\n"
            '    texture: bascenev1.Texture | None = None\n'
            '    tint_texture: bascenev1.Texture | None = None\n'
            '    times: Sequence[int] = (1,2,3,4,5)\n'
            '    values: Sequence[float] = (1.0, 2.0, 3.0, 4.0)\n'
            '    offset: float = 0.0\n'
            '    input0: float = 0.0\n'
            '    input1: float = 0.0\n'
            '    input2: float = 0.0\n'
            '    input3: float = 0.0\n'
            '    flashing: bool = False\n'
            '    scale: float | Sequence[float] = 0.0\n'  # FIXME
            '    opacity: float = 0.0\n'
            '    loop: bool = False\n'
            '    time1: int = 0\n'
            '    time2: int = 0\n'
            '    timemax: int = 0\n'
            '    client_only: bool = False\n'
            '    materials: Sequence[bascenev1.Material] = ()\n'
            '    roller_materials: Sequence[bascenev1.Material] = ()\n'
            "    name: str = ''\n"
            '    punch_materials: Sequence[bascenev1.Material] = ()\n'
            '    pickup_materials: Sequence[bascenev1.Material] = ()\n'
            '    extras_material: Sequence[bascenev1.Material] = ()\n'
            '    rotate: float = 0.0\n'
            '    hold_node: bascenev1.Node | None = None\n'
            '    hold_body: int = 0\n'
            '    host_only: bool = False\n'
            '    premultiplied: bool = False\n'
            '    source_player: bascenev1.Player | None = None\n'
            '    mesh_opaque: bascenev1.Mesh | None = None\n'
            '    mesh_transparent: bascenev1.Mesh | None = None\n'
            '    damage_smoothed: float = 0.0\n'
            '    gravity_scale: float = 1.0\n'
            '    punch_power: float = 0.0\n'
            '    punch_momentum_linear: Sequence[float] = '
            '(0.0, 0.0, 0.0)\n'
            '    punch_momentum_angular: float = 0.0\n'
            '    rate: int = 0\n'
            '    vr_depth: float = 0.0\n'
            '    is_area_of_interest: bool = False\n'
            '    jump_pressed: bool = False\n'
            '    pickup_pressed: bool = False\n'
            '    punch_pressed: bool = False\n'
            '    bomb_pressed: bool = False\n'
            '    fly_pressed: bool = False\n'
            '    hold_position_pressed: bool = False\n'
            '    #: Available on spaz node.\n'
            '    knockout: float = 0.0\n'
            '    invincible: bool = False\n'
            '    stick_to_owner: bool = False\n'
            '    damage: int = 0\n'
            '    #: Available on spaz node.\n'
            '    run: float = 0.0\n'
            '    #: Available on spaz node.\n'
            '    move_up_down: float = 0.0\n'
            '    #: Available on spaz node.\n'
            '    move_left_right: float = 0.0\n'
            '    curse_death_time: int = 0\n'
            '    boxing_gloves: bool = False\n'
            '    hockey: bool = False\n'
            '    use_fixed_vr_overlay: bool = False\n'
            '    #: Available on globals node.\n'
            '    allow_kick_idle_players: bool = False\n'
            '    music_continuous: bool = False\n'
            '    music_count: int = 0\n'
            '    #: Available on spaz node.\n'
            '    hurt: float = 0.0\n'
            '    #: On shield node.\n'
            '    always_show_health_bar: bool = False\n'
            '    #: Available on spaz node.\n'
            '    mini_billboard_1_texture: bascenev1.Texture | None = None\n'
            '    #: Available on spaz node.\n'
            '    mini_billboard_1_start_time: int = 0\n'
            '    #: Available on spaz node.\n'
            '    mini_billboard_1_end_time: int = 0\n'
            '    #: Available on spaz node.\n'
            '    mini_billboard_2_texture: bascenev1.Texture | None = None\n'
            '    #: Available on spaz node.\n'
            '    mini_billboard_2_start_time: int = 0\n'
            '    #: Available on spaz node.\n'
            '    mini_billboard_2_end_time: int = 0\n'
            '    #: Available on spaz node.\n'
            '    mini_billboard_3_texture: bascenev1.Texture | None = None\n'
            '    #: Available on spaz node.\n'
            '    mini_billboard_3_start_time: int = 0\n'
            '    #: Available on spaz node.\n'
            '    mini_billboard_3_end_time: int = 0\n'
            '    #: Available on spaz node.\n'
            '    boxing_gloves_flashing: bool = False\n'
            '    #: Available on spaz node.\n'
            '    dead: bool = False\n'
            '    floor_reflection: bool = False\n'
            '    debris_friction: float = 0.0\n'
            '    debris_kill_height: float = 0.0\n'
            '    vr_near_clip: float = 0.0\n'
            '    shadow_ortho: bool = False\n'
            '    happy_thoughts_mode: bool = False\n'
            '    shadow_offset: Sequence[float] = (0.0, 0.0)\n'
            '    paused: bool = False\n'
            '    time: int = 0\n'
            '    ambient_color: Sequence[float] = (1.0, 1.0, 1.0)\n'
            "    camera_mode: str = 'rotate'\n"
            '    frozen: bool = False\n'
            '    area_of_interest_bounds: Sequence[float]'
            ' = (-1, -1, -1, 1, 1, 1)\n'
            '    shadow_range: Sequence[float] = (0, 0, 0, 0)\n'
            "    counter_text: str = ''\n"
            '    counter_texture: bascenev1.Texture | None = None\n'
            '    #: Available on spaz node.\n'
            '    shattered: int = 0\n'
            '    #: Available on spaz node.\n'
            '    billboard_texture: bascenev1.Texture | None = None\n'
            '    #: Available on spaz node.\n'
            '    billboard_cross_out: bool = False\n'
            '    #: Available on spaz node.\n'
            '    billboard_opacity: float = 0.0\n'
            '    slow_motion: bool = False\n'
            "    music: str = ''\n"
            '    vr_camera_offset: Sequence[float] = (0.0, 0.0, 0.0)\n'
            '    vr_overlay_center: Sequence[float] = (0.0, 0.0, 0.0)\n'
            '    vr_overlay_center_enabled: bool = False\n'
            '    vignette_outer: Sequence[float] = (0.0, 0.0)\n'
            '    vignette_inner: Sequence[float] = (0.0, 0.0)\n'
            '    tint: Sequence[float] = (1.0, 1.0, 1.0)\n'
        )

    # Special case: ContextCall needs to be callable.
    if classname in ['ContextCall']:
        out += (
            '\n'
            '    def __call__(self) -> None:\n'
            '        """Support for calling."""\n'
            '        pass\n'
        )

    # Special case: need to be able to use the 'with' statement
    # on some classes.
    # TODO - determine these cases programmatically if possible.
    if classname in ['Context', 'ContextRef']:
        out += (
            '\n'
            '    def __enter__(self) -> None:\n'
            '        """Support for "with" statement."""\n'
            '        pass\n'
            '\n'
            '    def __exit__(self, exc_type: Any, exc_value: Any, '
            'traceback: Any) -> Any:\n'
            '        """Support for "with" statement."""\n'
            '        pass\n'
        )

    # Define bool functionality for classes that support it internally.
    # (lets mypy know these are safe to use in bool evaluation)
    # TODO - determine these cases programmatically if possible.
    if classname in [
        'Widget',
        'Node',
        'InputDevice',
        'SessionPlayer',
    ]:
        out += (
            '\n'
            '    def __bool__(self) -> bool:\n'
            '        """Support for bool evaluation."""\n'
            '        return bool(True) # Slight obfuscation.\n'
        )

    return out


def _filterdoc(docstr: str, funcname: str | None = None) -> str:
    docslines = docstr.splitlines()

    if (
        funcname
        and docslines
        and docslines[0]
        and docslines[0].startswith(funcname)
    ):
        if '\n' in docstr:
            # Remove this signature from python docstring
            # as not to repeat ourselves.
            _, docstr = docstr.split('\n\n', maxsplit=1)
            docslines = docstr.splitlines()
        else:
            docstr = ''

    # Assuming that each line between 'Attributes:' and '\n\n' belongs to
    # attrs descriptions.
    empty_lines_count = 0
    attributes_line: int | None = None
    attrs_definitions_last_line: int | None = None
    for i, line in enumerate(docslines):
        if line.strip() in ['Attrs:', 'Attributes:']:
            if attributes_line is not None:
                raise RuntimeError("Multiple 'Attributes:' lines found")
            attributes_line = i
        if not line.strip():
            empty_lines_count += 1
        else:
            empty_lines_count = 0
        if empty_lines_count >= 2 and attributes_line is not None:
            # It seems attribute definitions ended.
            attrs_definitions_last_line = i
            break
    if attrs_definitions_last_line is None:
        attrs_definitions_last_line = len(docslines) - 1

    return '\n'.join(
        docslines[:attributes_line]
        + docslines[attrs_definitions_last_line + 1 :]
    )


def _formatdoc(
    docstr: str,
    indent: int,
    form: Literal['str', 'comment'],
    # *,
    # no_end_newline: bool = False,
    # inner_indent: int = 0,
) -> str:
    out = ''
    indentstr = indent * ' '
    # inner_indent_str = inner_indent * ' '
    # inner_indent_str = ''
    docslines = docstr.splitlines()

    if len(docslines) == 1 and form == 'str':
        out += indentstr + '"""' + docslines[0] + '"""\n'
    else:
        for i, line in enumerate(docslines):
            if form == 'comment':
                docslines[i] = indentstr + '#: ' + line
            else:
                if i != 0 and line != '':
                    docslines[i] = indentstr + line
        if form == 'comment':
            out += '\n'.join(docslines) + '\n'
        else:
            out += (
                indentstr
                + '"""'
                + '\n'.join(docslines)
                + '\n'
                + indentstr
                + '"""\n'
            )
    return out


def _writeclasses(module: ModuleType, classnames: Sequence[str]) -> str:
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-locals
    from batools.docs import parse_docs_attrs

    out = ''
    for classname in classnames:
        cls = getattr(module, classname)
        if cls is None:
            raise RuntimeError('unexpected')
        out += '\n\n'

        # Special case: get PyCharm to shut up about Node's methods
        # shadowing builtin types.
        if classname in {'Node', 'SessionPlayer'}:
            out += '# noinspection PyShadowingBuiltins\n'
        if classname in {'Timer', 'BaseTimer'}:
            out += '# noinspection PyShadowingNames\n'

        # Special case:
        if classname == 'Vec3':
            out += f'class {classname}(Sequence[float]):\n'
        else:
            out += f'class {classname}:\n'

        docstr = cls.__doc__

        # Classname is constructor name.
        out += _formatdoc(_filterdoc(docstr, funcname=classname), 4, form='str')

        # Create a public constructor if it has one. If the first docs
        # line appears to be a function signature and not category or a
        # usage statement ending with a period, assume it has a public
        # constructor.
        has_constructor = False
        if (
            'category:' not in docstr.splitlines()[0].lower()
            and not docstr.splitlines()[0].endswith('.')
            and docstr != '(internal)'
        ):
            # Ok.. looks like the first line is a signature. Make sure
            # we've got a signature followed by a blank line.
            if '\n\n' not in docstr:
                raise RuntimeError(
                    f'Constructor docstr missing empty line for {cls}.'
                )
            sig = docstr.split('\n\n')[0].replace('\n', ' ').strip()

            # Make sure supplied signature matches the filtered class name.
            if not sig.startswith(classname + '('):
                raise RuntimeError(
                    f'Expected constructor signature for class {classname}'
                    f" to start with '{classname}'."
                )
            sig = classname + sig.removeprefix(classname)
            sig = sig.replace(classname + '(', '__init__(self, ')
            out += '    def ' + sig + ' -> None:\n        pass\n'
            has_constructor = True

        # Scan its doc-string for attribute info; drop in typed
        # declarations for any that we find.
        attrs: list[AttributeInfo] = []
        parse_docs_attrs(attrs, docstr)
        has_attrs = False
        if attrs:
            for attr in attrs:
                if attr.attr_type is not None:
                    if attr.docs:
                        out += '\n'
                        out += _formatdoc(
                            _filterdoc(attr.docs), indent=4, form='comment'
                        )
                    has_attrs = True
                    out += f'    {attr.name}: {attr.attr_type}\n'
                else:
                    raise RuntimeError(
                        f'Found untyped attr in'
                        f' {classname} docs: {attr.name}'
                    )

        # Special cases such as attributes we add.
        out += _special_class_cases(classname)

        # Print its methods.
        funcnames = []
        for entry in (e for e in dir(cls) if not e.startswith('__')):
            if isinstance(getattr(cls, entry), types.MethodDescriptorType):
                funcnames.append(entry)
            elif isinstance(getattr(cls, entry), types.BuiltinMethodType):
                # We get this for classmethods
                funcnames.append(entry)
            else:
                entrytype = type(getattr(cls, entry))
                raise RuntimeError(
                    f'Unhandled obj \'{entry}\' in {cls} (type {entrytype})'
                )
        funcnames.sort()
        functxt = _writefuncs(
            cls, funcnames, indent=4, spacing=1, as_method=True
        )
        if functxt == '' and not has_constructor and not has_attrs:
            out += '    pass\n'
        else:
            out += functxt

    return out


class Generator:
    """Context for a module generation pass."""

    def __init__(self, projroot: str, modulename: str, outfilename: str):
        self.projroot = projroot
        self.mname = modulename
        self.outfilename = outfilename

    def run(self) -> None:
        """Run the actual generation from within the app context."""

        from efrotools.project import get_public_legal_notice
        from efrotools.code import format_python_str

        module = __import__(self.mname)

        funcnames = []
        classnames = []
        for entry in (e for e in dir(module) if not e.startswith('__')):
            if isinstance(getattr(module, entry), types.BuiltinFunctionType):
                funcnames.append(entry)
            elif isinstance(getattr(module, entry), type):
                classnames.append(entry)
            elif self.mname == '_babase' and entry == 'app':
                # Ignore _babase.app.
                continue
            elif entry == '_ba_feature_set_data':
                # Ignore the C++ data we stuff into our feature-set modules.
                continue
            elif entry == '_REACHED_END_OF_MODULE':
                # Ignore this marker we use to debug import ordering.
                continue
            else:
                raise RuntimeError(
                    f'found unknown obj {entry}, {getattr(module, entry)}'
                )
        funcnames.sort()
        classnames.sort()
        typing_imports = (
            'TYPE_CHECKING, overload, override, Sequence'
            if self.mname == '_babase'
            else (
                'TYPE_CHECKING, overload, override'
                if self.mname == '_bascenev1'
                else 'TYPE_CHECKING, override'
            )
        )
        typing_imports_tc = (
            'Any, Callable'
            if self.mname == '_babase'
            else (
                'Any, Callable, Literal, Sequence'
                if self.mname == '_bascenev1'
                else (
                    'Any, Callable, Literal, Sequence'
                    if self.mname == '_bauiv1'
                    else 'Any, Callable'
                )
            )
        )
        tc_import_lines_extra = ''
        if self.mname == '_babase':
            tc_import_lines_extra += (
                '    import bacommon.app\n'
                '    from babase import App\n'
                '    import babase\n'  # hold
            )
        elif self.mname == '_bascenev1':
            tc_import_lines_extra += '    import babase\n    import bascenev1\n'
        elif self.mname == '_bauiv1':
            tc_import_lines_extra += '    import babase\n    import bauiv1\n'
        app_declare_lines = 'app: App\n\n' if self.mname == '_babase' else ''
        enum_import_lines = (
            ''
            if self.mname == '_babase'
            # else 'from babase._mgen.enums import TimeFormat, TimeType\n\n'
            else '' if self.mname == '_bascenev1' else ''
        )
        out = (
            get_public_legal_notice('python') + '\n'
            '#\n'
            f'"""A dummy stub module for the real {self.mname}.\n'
            '\n'
            f'The real {self.mname} is a compiled extension module'
            ' and only available\n'
            'in the live engine. This dummy-module allows Pylint/Mypy/etc. to\n'
            'function reasonably well outside of that environment.\n'
            '\n'
            'Make sure this file is never included'
            ' in dirs seen by the engine!\n'
            '\n'
            'In the future perhaps this can be a stub (.pyi) file, but'
            ' we will need\n'
            'to make sure that it works with all our tools'
            ' (mypy, pylint, pycharm).\n'
            '\n'
            'NOTE: This file was autogenerated by ' + __name__ + '; '
            'do not edit by hand.\n'
            '"""\n'
            '\n'
            # '# (hash we can use to see if this file is out of date)\n'
            # '# SOURCES_HASH='+sources_hash+'\n'
            # '\n'
            '# I\'m sorry Pylint. I know this file saddens you. Be strong.\n'
            '# pylint: disable=useless-suppression\n'
            '# pylint: disable=unnecessary-pass\n'
            '# pylint: disable=use-dict-literal\n'
            '# pylint: disable=use-list-literal\n'
            '# pylint: disable=unused-argument\n'
            '# pylint: disable=missing-docstring\n'
            '# pylint: disable=too-many-locals\n'
            '# pylint: disable=redefined-builtin\n'
            '# pylint: disable=too-many-lines\n'
            '# pylint: disable=redefined-outer-name\n'
            '# pylint: disable=invalid-name\n'
            '# pylint: disable=no-value-for-parameter\n'
            '# pylint: disable=unused-import\n'
            '# pylint: disable=too-many-positional-arguments\n'
            '\n'
            'from __future__ import annotations\n'
            '\n'
            f'from typing import {typing_imports}\n'
            '\n'
            f'{enum_import_lines}'
            'if TYPE_CHECKING:\n'
            f'    from typing import {typing_imports_tc}\n'
            f'{tc_import_lines_extra}'
            '\n'
            # '\n'
            # "_T = TypeVar('_T')\n"
            '\n'
            f'{app_declare_lines}'
            'def _uninferrable() -> Any:\n'
            '    """Get an "Any" in mypy and "uninferrable" in Pylint."""\n'
            '    # pylint: disable=undefined-variable\n'
            '    return _not_a_real_variable  # type: ignore'
            '\n'
            '\n'
        )

        out += _writeclasses(module, classnames)
        out += _writefuncs(
            module, funcnames, indent=0, spacing=2, as_method=False
        )

        # Lastly format it.
        out = format_python_str(Path(self.projroot), out)

        os.makedirs(os.path.dirname(self.outfilename), exist_ok=True)
        with open(self.outfilename, 'w', encoding='utf-8') as outfile:
            outfile.write(out)


def generate_dummy_modules(projroot: str) -> None:
    """Generate all dummy-modules."""
    # pylint: disable=cyclic-import

    from batools.featureset import FeatureSet
    from batools import apprun

    toolsdir = os.path.abspath(os.path.join(projroot, 'tools'))

    # Make sure we're running from the project root dir.
    if os.path.abspath(projroot) != os.getcwd():
        raise RuntimeError(
            f"We expect to be running from '{projroot}'"
            f" but cwd is '{os.getcwd()}'."
        )

    binary_path = apprun.acquire_binary(
        assets=True, purpose='dummy-module generation'
    )

    # We need access to things like black that are installed into the project
    # venv.
    venvpath = '.venv/bin'
    if not os.path.isdir(venvpath):
        raise RuntimeError(
            f'Expected project venv binary path not found: "{venvpath}".'
        )
    pycmd = (
        f'import sys\n'
        f'sys.path.append("build/assets/ba_data/python")\n'
        f'sys.path.append("build/assets/ba_data/python-site-packages")\n'
        f'sys.path.append("{toolsdir}")\n'
        f'from batools import dummymodule\n'
    )

    # Generate a dummy module for each featureset that has a binary module.
    featuresets = FeatureSet.get_all_for_project(project_root=projroot)
    featuresets = [f for f in featuresets if f.has_python_binary_module]
    mnames: list[str] = [fs.name_python_binary_module for fs in featuresets]

    builddir = 'build/dummymodules'
    os.makedirs(builddir, exist_ok=True)

    gencount = 0
    for mname in mnames:
        gencount += 1
        outfilename = os.path.abspath(
            os.path.join(projroot, builddir, f'{mname}.py')
        )
        pycmd += (
            f'dummymodule.Generator(projroot=".", modulename="{mname}",'
            f' outfilename="{outfilename}").run()\n'
        )

    # Launch ballisticakit and exec ourself from within it.
    print(
        f'{Clr.SMAG}Launching ballisticakit to generate'
        f' {gencount} dummy-modules...{Clr.RST}',
        flush=True,
    )
    try:
        # Note: Ask Python to kindly *not* scatter __pycache__ files
        # throughout our build output.
        #
        # Also pass our .venv path so any recursive invocations of Python
        # will properly pick up our modules (for things like black formatting).

        # pylint: disable=inconsistent-quotes
        subprocess.run(
            [binary_path, '--command', pycmd],
            env=dict(
                os.environ,
                PYTHONDONTWRITEBYTECODE='1',
                PATH=f'.venv/bin:{os.environ["PATH"]}',
            ),
            check=True,
        )
        print(
            f'{Clr.BLD}{Clr.BLU}Generated {gencount} dummy-modules'
            f' {Clr.RST}(in {builddir}){Clr.RST}{Clr.BLD}{Clr.BLU}.{Clr.RST}',
            flush=True,
        )

    except Exception as exc:
        if bool(False):
            import logging

            logging.exception('ERROR')

        # Keep our error simple here; we want focus to be on what went
        # wrong within BallisticaKit.
        raise CleanError('Dummy-module generation failed.') from exc
