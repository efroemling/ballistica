# Released under the MIT License. See LICENSE for details.
#
"""Generates a dummy _ba.py and _bainternal.py based on binary modules.

This allows us to use code introspection tools such as pylint without spinning
up the engine, and also allows external scripts to import game scripts
successfully (albeit with limited functionality).
"""

from __future__ import annotations

import os
import sys
import textwrap
import subprocess
from typing import TYPE_CHECKING

from efro.error import CleanError
from efro.terminal import Clr
from efrotools import get_files_hash

if TYPE_CHECKING:
    from types import ModuleType
    from typing import Sequence, Any
    from batools.docs import AttributeInfo


def _get_varying_func_info(sig_in: str) -> tuple[str, str]:
    """Return overloaded signatures and return statements for varying funcs."""
    returns = 'return None'
    if sig_in == (
        'getdelegate(self, type: type,' ' doraise: bool = False) -> <varies>'
    ):
        sig = (
            '# Show that ur return type varies based on "doraise" value:\n'
            '@overload\n'
            'def getdelegate(self, type: type[_T],'
            ' doraise: Literal[False] = False) -> _T | None:\n'
            '    ...\n'
            '\n'
            '@overload\n'
            'def getdelegate(self, type: type[_T],'
            ' doraise: Literal[True]) -> _T:\n'
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
            ' doraise: Literal[True] = True) -> ba.InputDevice:\n'
            '    ...\n'
            '\n'
            '@overload\n'
            'def getinputdevice(name: str, unique_id: str,'
            ' doraise: Literal[False]) -> ba.InputDevice | None:\n'
            '    ...\n'
            '\n'
            'def getinputdevice(name: str, unique_id: str,'
            ' doraise: bool=True) -> Any:'
        )
    elif sig_in == (
        'time(timetype: ba.TimeType = TimeType.SIM,'
        '   timeformat: ba.TimeFormat = TimeFormat.SECONDS)'
        '   -> <varies>'
    ):
        sig = (
            '# Overloads to return a type based on requested format.\n'
            '\n'
            '@overload\n'
            'def time(timetype: ba.TimeType = TimeType.SIM,\n'
            '        timeformat: Literal[TimeFormat.SECONDS]'
            ' = TimeFormat.SECONDS) -> float:\n'
            '    ...\n'
            '\n'
            '# This "*"'
            ' keyword-only hack lets us accept 1 arg'
            ' (timeformat=MILLISECS) forms.\n'
            '@overload\n'
            'def time(timetype: ba.TimeType = TimeType.SIM, *,\n'
            '         timeformat: Literal[TimeFormat.MILLISECONDS]) -> int:\n'
            '    ...\n'
            '\n'
            '@overload\n'
            'def time(timetype: ba.TimeType,\n'
            '         timeformat: Literal[TimeFormat.MILLISECONDS]) -> int:\n'
            '    ...\n'
            '\n'
            '\n'
            'def time(timetype: ba.TimeType = TimeType.SIM,\n'
            '         timeformat: ba.TimeFormat = TimeFormat.SECONDS)'
            ' -> Any:\n'
        )
    elif sig_in == 'getactivity(doraise: bool = True) -> <varies>':
        sig = (
            '# Show that our return type varies based on "doraise" value:\n'
            '@overload\n'
            'def getactivity(doraise: Literal[True] = True) -> ba.Activity:\n'
            '    ...\n'
            '\n'
            '\n'
            '@overload\n'
            'def getactivity(doraise: Literal[False])'
            ' -> ba.Activity | None:\n'
            '    ...\n'
            '\n'
            '\n'
            'def getactivity(doraise: bool = True) -> ba.Activity | None:'
        )
    elif sig_in == 'getsession(doraise: bool = True) -> <varies>':
        sig = (
            '# Show that our return type varies based on "doraise" value:\n'
            '@overload\n'
            'def getsession(doraise: Literal[True] = True) -> ba.Session:\n'
            '    ...\n'
            '\n'
            '\n'
            '@overload\n'
            'def getsession(doraise: Literal[False])'
            ' -> ba.Session | None:\n'
            '    ...\n'
            '\n'
            '\n'
            'def getsession(doraise: bool = True) -> ba.Session | None:'
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
        docstr = func.__doc__

        # We expect an empty line and take everything before that to be
        # the function signature.
        if '\n\n' not in docstr:
            raise Exception(f'docstr missing empty line: {func}')
        sig = docstr.split('\n\n')[0].replace('\n', ' ').strip()

        # Sanity check - make sure name is in the sig.
        if funcname + '(' not in sig:
            raise Exception(f'func name not found in sig for {funcname}')

        # If these are methods, add self.
        if as_method:
            if funcname + '()' in sig:
                sig = sig.replace(funcname + '()', funcname + '(self)')
            else:
                sig = sig.replace(funcname + '(', funcname + '(self, ')

        # We expect sig to have a -> denoting return type.
        if ' -> ' not in sig:
            raise Exception(f'no "->" found in docstr for {funcname}')
        returns = sig.split('->')[-1].strip()

        # Some functions don't have simple signatures; we need to hard-code
        # those here with overloads and whatnot.
        if '<varies>' in sig:
            overloadsigs, returnstr = _get_varying_func_info(sig)
            defsline = textwrap.indent(overloadsigs, indstr)
        else:
            defsline = f'{indstr}def {sig}:\n'

            # Types can be strings for forward-declaration cases.
            if (returns[0] == "'" and returns[-1] == "'") or (
                returns[0] == '"' and returns[-1] == '"'
            ):
                returns = returns[1:-1]
            if returns == 'None':
                returnstr = 'return None'
            elif returns == 'ba.Lstr':
                returnstr = (
                    'import ba  # pylint: disable=cyclic-import\n'
                    "return ba.Lstr(value='')"
                )
            elif returns in {'ba.Activity', 'ba.Activity | None'}:
                returnstr = (
                    'import ba  # pylint: disable=cyclic-import\nreturn '
                    + 'ba.Activity(settings={})'
                )
            elif returns in {'ba.Session', 'ba.Session | None'}:
                returnstr = (
                    'import ba  # pylint: disable=cyclic-import\nreturn '
                    + 'ba.Session([])'
                )
            elif returns == 'ba.SessionPlayer | None':
                returnstr = (
                    'import ba  # pylint: disable=cyclic-import\n'
                    'return ba.SessionPlayer()'
                )
            elif returns == 'ba.Player | None':
                returnstr = (
                    'import ba  # pylint: disable=cyclic-import\n'
                    'return ba.Player()'
                )
            elif returns.startswith('ba.') and ' | None' not in returns:
                # We cant import ba at module level so let's
                # do it within funcs as needed.
                returnstr = (
                    'import ba  # pylint: disable=cyclic-import\nreturn '
                    + returns
                    + '()'
                )

            elif returns in {'object', 'Any'}:
                # We use 'object' when we mean "can vary"
                # don't want pylint making assumptions in this case.
                returnstr = 'return _uninferrable()'
            elif returns == 'tuple[float, float]':
                returnstr = 'return (0.0, 0.0)'
            elif returns == 'str | None':
                returnstr = "return ''"
            elif returns == 'tuple[float, float, float, float]':
                returnstr = 'return (0.0, 0.0, 0.0, 0.0)'
            elif returns == 'ba.Widget | None':
                returnstr = 'return Widget()'
            elif returns == 'ba.InputDevice | None':
                returnstr = 'return InputDevice()'
            elif returns == 'list[ba.Widget]':
                returnstr = 'return [Widget()]'
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
                    'from ba import '
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
                'Model',
                'CollideModel',
                'team.Team',
                'Vec3',
                'Widget',
                'Node',
            ]:
                returnstr = 'return ' + returns + '()'
            else:
                raise Exception(
                    f'unknown returns value: {returns} for {funcname}'
                )
        returnspc = indstr + '    '
        returnstr = ('\n' + returnspc).join(returnstr.strip().splitlines())
        docstr_out = _formatdoc(
            _filterdoc(docstr, funcname=funcname), indent + 4
        )
        out += spcstr + defsline + docstr_out + f'{returnspc}{returnstr}\n'
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
            '    def __getitem__(self, typeargs: Any) -> Any:\n'
            '        return 0.0\n'
            '\n'
            '    def __len__(self) -> int:\n'
            '        return 3\n'
            '\n'
            '    # (for iterator access)\n'
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
            '    # now now since we have a single ba.Node type; in the\n'
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
            "    text: ba.Lstr | str = ''\n"
            '    texture: ba.Texture | None = None\n'
            '    tint_texture: ba.Texture | None = None\n'
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
            '    materials: Sequence[Material] = ()\n'
            '    roller_materials: Sequence[Material] = ()\n'
            "    name: str = ''\n"
            '    punch_materials: Sequence[ba.Material] = ()\n'
            '    pickup_materials: Sequence[ba.Material] = ()\n'
            '    extras_material: Sequence[ba.Material] = ()\n'
            '    rotate: float = 0.0\n'
            '    hold_node: ba.Node | None = None\n'
            '    hold_body: int = 0\n'
            '    host_only: bool = False\n'
            '    premultiplied: bool = False\n'
            '    source_player: ba.Player | None = None\n'
            '    model_opaque: ba.Model | None = None\n'
            '    model_transparent: ba.Model | None = None\n'
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
            '    knockout: float = 0.0\n'
            '    invincible: bool = False\n'
            '    stick_to_owner: bool = False\n'
            '    damage: int = 0\n'
            '    run: float = 0.0\n'
            '    move_up_down: float = 0.0\n'
            '    move_left_right: float = 0.0\n'
            '    curse_death_time: int = 0\n'
            '    boxing_gloves: bool = False\n'
            '    hockey: bool = False\n'
            '    use_fixed_vr_overlay: bool = False\n'
            '    allow_kick_idle_players: bool = False\n'
            '    music_continuous: bool = False\n'
            '    music_count: int = 0\n'
            '    hurt: float = 0.0\n'
            '    always_show_health_bar: bool = False\n'
            '    mini_billboard_1_texture: ba.Texture | None = None\n'
            '    mini_billboard_1_start_time: int = 0\n'
            '    mini_billboard_1_end_time: int = 0\n'
            '    mini_billboard_2_texture: ba.Texture | None = None\n'
            '    mini_billboard_2_start_time: int = 0\n'
            '    mini_billboard_2_end_time: int = 0\n'
            '    mini_billboard_3_texture: ba.Texture | None = None\n'
            '    mini_billboard_3_start_time: int = 0\n'
            '    mini_billboard_3_end_time: int = 0\n'
            '    boxing_gloves_flashing: bool = False\n'
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
            '    counter_texture: ba.Texture | None = None\n'
            '    shattered: int = 0\n'
            '    billboard_texture: ba.Texture | None = None\n'
            '    billboard_cross_out: bool = False\n'
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

    # Special case: need to be able to use the 'with' statement
    # on some classes.
    if classname in ['Context']:
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
    return out


def _filterdoc(docstr: str, funcname: str | None = None) -> str:
    docslines = docstr.splitlines()

    if (
        funcname
        and docslines
        and docslines[0]
        and docslines[0].startswith(funcname)
    ):
        # Remove this signature from python docstring
        # as not to repeat ourselves.
        _, docstr = docstr.split('\n\n', maxsplit=1)
        docslines = docstr.splitlines()

    # Assuming that each line between 'Attributes:' and '\n\n' belongs to
    # attrs descriptions.
    empty_lines_count = 0
    attributes_line: int | None = None
    attrs_definitions_last_line: int | None = None
    for i, line in enumerate(docslines):
        if line.strip() in ['Attrs:', 'Attributes:']:
            if attributes_line is not None:
                raise Exception("Multiple 'Attributes:' lines found")
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
    no_end_newline: bool = False,
    inner_indent: int = 0,
) -> str:
    out = ''
    indentstr = indent * ' '
    inner_indent_str = inner_indent * ' '
    docslines = docstr.splitlines()

    if len(docslines) == 1:
        out += '\n' + indentstr + '"""' + docslines[0] + '"""\n'
    else:
        for i, line in enumerate(docslines):
            if i != 0 and line != '':
                docslines[i] = indentstr + inner_indent_str + line
        out += (
            '\n'
            + indentstr
            + '"""'
            + '\n'.join(docslines)
            + ('' if no_end_newline else '\n' + indentstr)
            + '"""\n'
        )
    return out


def _writeclasses(module: ModuleType, classnames: Sequence[str]) -> str:
    # pylint: disable=too-many-branches
    import types
    from batools.docs import parse_docs_attrs

    out = ''
    for classname in classnames:
        cls = getattr(module, classname)
        if cls is None:
            raise Exception('unexpected')
        out += '\n' '\n'

        # Special case:
        if classname == 'Vec3':
            out += f'class {classname}(Sequence[float]):\n'
        else:
            out += f'class {classname}:\n'

        docstr = cls.__doc__
        # classname is constructor name
        out += _formatdoc(_filterdoc(docstr, funcname=classname), 4)

        # Create a public constructor if it has one.
        # If the first docs line appears to be a function signature
        # and not category or a usage statement ending with a period,
        # assume it has a public constructor.
        has_constructor = False
        if (
            'category:' not in docstr.splitlines()[0].lower()
            and not docstr.splitlines()[0].endswith('.')
            and docstr != '(internal)'
        ):
            # Ok.. looks like the first line is a signature.
            # Make sure we've got a signature followed by a blank line.
            if '\n\n' not in docstr:
                raise Exception(
                    f'Constructor docstr missing empty line for {cls}.'
                )
            sig = docstr.split('\n\n')[0].replace('\n', ' ').strip()

            # Sanity check - make sure name is in the sig.
            if classname + '(' not in sig:
                raise Exception(
                    f'Class name not found in constructor sig for {cls}.'
                )
            sig = sig.replace(classname + '(', '__init__(self, ')
            out += '    def ' + sig + ':\n        pass\n'
            has_constructor = True

        # Scan its doc-string for attribute info; drop in typed
        # declarations for any that we find.
        attrs: list[AttributeInfo] = []
        parse_docs_attrs(attrs, docstr)
        if attrs:
            for attr in attrs:
                if attr.attr_type is not None:
                    out += f'    {attr.name}: {attr.attr_type}\n'
                    if attr.docs:
                        out += _formatdoc(
                            _filterdoc(attr.docs),
                            indent=4,
                            inner_indent=3,
                            no_end_newline=True,
                        )
                        out += '\n'
                else:
                    raise Exception(
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
            else:
                raise Exception(f'Unhandled obj {entry} in {cls}')
        funcnames.sort()
        functxt = _writefuncs(
            cls, funcnames, indent=4, spacing=1, as_method=True
        )
        if functxt == '' and not has_constructor:
            out += '    pass\n'
        else:
            out += functxt

    return out


def generate(mname: str, sources_hash: str, outfilename: str) -> None:
    """Run the actual generation from within the game."""
    # pylint: disable=too-many-locals
    import types

    from efrotools import get_public_license
    from efrotools.code import format_python_str

    module = __import__(mname)

    funcnames = []
    classnames = []
    for entry in (e for e in dir(module) if not e.startswith('__')):
        if isinstance(getattr(module, entry), types.BuiltinFunctionType):
            funcnames.append(entry)
        elif isinstance(getattr(module, entry), type):
            classnames.append(entry)
        elif mname == '_ba' and entry == 'app':
            # Ignore _ba.app.
            continue
        else:
            raise Exception(
                f'found unknown obj {entry}, {getattr(module, entry)}'
            )
    funcnames.sort()
    classnames.sort()
    typing_imports = (
        'TYPE_CHECKING, overload, Sequence, TypeVar'
        if mname == '_ba'
        else 'TYPE_CHECKING, TypeVar'
    )
    typing_imports_tc = (
        'Any, Callable, Literal' if mname == '_ba' else 'Any, Callable'
    )
    tc_import_lines_extra = (
        '    from ba._app import App\n' '    import ba\n'
        if mname == '_ba'
        else ''
    )
    app_declare_lines = 'app: App\n' '\n' if mname == '_ba' else ''
    enum_import_lines = (
        'from ba._generated.enums import TimeFormat, TimeType\n' '\n'
        if mname == '_ba'
        else ''
    )
    out = (
        get_public_license('python') + '\n'
        '#\n'
        f'"""A dummy stub module for the real {mname}.\n'
        '\n'
        f'The real {mname} is a compiled extension module'
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
        '\n'
        "_T = TypeVar('_T')\n"
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
    out += _writefuncs(module, funcnames, indent=0, spacing=2, as_method=False)

    # Lastly format it.
    out = format_python_str(out)

    outhashpath = os.path.join(
        os.path.dirname(outfilename), f'.{mname}_sources_hash'
    )

    with open(outfilename, 'w', encoding='utf-8') as outfile:
        outfile.write(out)

    with open(outhashpath, 'w', encoding='utf-8') as outfile:
        outfile.write(sources_hash)


def _dummy_module_dirty(mname: str) -> tuple[bool, str]:
    """Test hashes on the dummy-module to see if it needs updates."""

    # Let's generate a hash from all sources under the python source dir.
    pysources = []
    exts = ['.cc', '.c', '.h']
    for root, _dirs, files in os.walk('src/ballistica/python'):
        for fname in files:
            if any(fname.endswith(ext) for ext in exts):
                pysources.append(os.path.join(root, fname))

    # Also lets add this script so we re-create when it changes.
    pysources.append(__file__)

    outpath = f'assets/src/ba_data/python/.{mname}_sources_hash'
    if not os.path.exists(outpath):
        existing_hash = ''
    else:
        with open(outpath, encoding='utf-8') as infile:
            existing_hash = infile.read()

    # Important to keep this deterministic...
    pysources.sort()

    # Note: going with plain integers instead of hex so linters
    # don't see words and whine about spelling errors.
    pysources_hash = get_files_hash(pysources, int_only=True)
    dirty = existing_hash != pysources_hash
    return dirty, pysources_hash


def update(projroot: str, check: bool, force: bool) -> None:
    """Update dummy-modules as needed."""
    from pathlib import Path

    from efrotools import getconfig

    toolsdir = os.path.abspath(os.path.join(projroot, 'tools'))

    # Make sure we're running from the project root dir.
    os.chdir(projroot)

    public = getconfig(Path('.'))['public']

    # Force makes no sense in check mode.
    if force and check:
        raise Exception('cannot specify both force and check mode')

    for mname in ('_ba', '_bainternal'):
        # Skip internal module in public since it might
        # not exist and is read-only anyway.
        if mname == '_bainternal' and public:
            continue

        outfilename = os.path.abspath(
            os.path.join(projroot, f'assets/src/ba_data/python/{mname}.py')
        )

        dirty, sources_hash = _dummy_module_dirty(mname)

        if dirty:
            if check:
                print(
                    f'{Clr.RED}ERROR: dummy {mname} module'
                    f' is out of date.{Clr.RST}'
                )
                sys.exit(255)
        elif not force:
            # Dummy-module is clean and force is off; we're done here.
            print(f'Dummy-module {Clr.BLD}{mname}.py{Clr.RST} is up to date.')
            continue

        print(
            f'{Clr.MAG}Updating {Clr.BLD}{mname}.py{Clr.RST}{Clr.MAG}'
            f' dummy-module...{Clr.RST}'
        )

        # Let's build the cmake version; no sandboxing issues to contend with
        # there. Also going with the headless build; will need to revisit if
        # there's ever any functionality not available in that build.
        subprocess.run(['make', 'cmake-server-build'], check=True)

        # Launch ballisticacore and exec ourself from within it.
        print(
            f'Launching ballisticacore to generate'
            f' {Clr.BLD}{mname}.py{Clr.RST} dummy-module...'
        )
        try:
            subprocess.run(
                [
                    './ballisticacore',
                    '-exec',
                    f'try:\n'
                    f'    import sys\n'
                    f'    sys.path.append("{toolsdir}")\n'
                    f'    from batools import dummymodule\n'
                    f'    dummymodule.generate(mname="{mname}",\n'
                    f'        sources_hash="{sources_hash}",\n'
                    f'        outfilename="{outfilename}")\n'
                    f'    ba.quit()\n'
                    f'except Exception as exc:\n'
                    f'    import sys\n'
                    f'    import traceback\n'
                    f'    print("ERROR GENERATING {mname} DUMMY-MODULE")\n'
                    f'    traceback.print_exc()\n'
                    f'    sys.exit(255)\n',
                ],
                cwd='build/cmake/server-debug/dist',
                check=True,
            )
            print(
                f'{Clr.BLU}{mname} dummy-module generation complete.{Clr.RST}'
            )

        except Exception as exc2:
            # Keep our error simple here; we want focus to be on what went
            # wrong withing BallisticaCore.
            raise CleanError(
                'BallisticaCore dummy-module generation failed.'
            ) from exc2
