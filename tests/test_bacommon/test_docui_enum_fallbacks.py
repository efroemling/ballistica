# Released under the MIT License. See LICENSE for details.
#
"""Testing that enum values on the doc-ui v2 wire can grow safely.

A client in the field decodes whatever a newer server sends it. An enum
field with no fallback turns one unrecognized value into a failed
decode of the whole response, so every enum field on the wire needs
one; these check that they all do and that the fallbacks behave.
"""

import dataclasses
import types
import typing
from enum import Enum
from typing import Annotated

import pytest

import bacommon.docui.v2 as dui2
from bacommon.langstr import LangStrSpecValue
from efro.dataclassio import (
    IOAttrs,
    dataclass_from_dict,
    dataclass_to_dict,
)


def _enum_fields() -> list[tuple[str, type[Enum], IOAttrs | None]]:
    """Return every enum-typed dataclass field in the v2 wire module."""
    out: list[tuple[str, type[Enum], IOAttrs | None]] = []
    for name, cls in sorted(vars(dui2).items()):
        if not (isinstance(cls, type) and dataclasses.is_dataclass(cls)):
            continue
        if cls.__module__ != dui2.__name__:
            continue
        hints = typing.get_type_hints(cls, include_extras=True)
        for field in dataclasses.fields(cls):
            anntype = hints[field.name]
            ioattrs: IOAttrs | None = None
            if typing.get_origin(anntype) is Annotated:
                args = typing.get_args(anntype)
                anntype = args[0]
                for arg in args[1:]:
                    if isinstance(arg, IOAttrs):
                        ioattrs = arg
            members: tuple[object, ...]
            if typing.get_origin(anntype) in (typing.Union, types.UnionType):
                members = typing.get_args(anntype)
            else:
                members = (anntype,)
            for member in members:
                if isinstance(member, type) and issubclass(member, Enum):
                    out.append((f'{name}.{field.name}', member, ioattrs))
    return out


def test_every_enum_field_has_a_fallback() -> None:
    """A new enum field can't quietly go without a fallback."""
    fields = _enum_fields()

    # Sanity check that we are actually finding things.
    found = {path for path, _enumtype, _ioattrs in fields}
    assert 'Button.style' in found
    assert 'ButtonRow.layout' in found
    assert 'ButtonRow.title_align' in found
    assert 'Text.h_align' in found

    missing = [
        path
        for path, enumtype, ioattrs in fields
        if ioattrs is None or not isinstance(ioattrs.enum_fallback, enumtype)
    ]
    assert not missing, (
        f'doc-ui v2 enum fields without an enum_fallback: {missing}.'
        f' An unrecognized value in one of these fails the whole'
        f' response on builds predating it.'
    )


def _button_row_dict() -> dict[str, typing.Any]:
    row = dui2.ButtonRow(
        buttons=[
            dui2.Button(
                label=LangStrSpecValue.literal('hi'),
                style=dui2.ButtonStyle.TAB,
                decorations=[
                    dui2.Text(
                        text=LangStrSpecValue.literal('t'),
                        position=(0.0, 0.0),
                        size=(10.0, 10.0),
                        h_align=dui2.HAlign.LEFT,
                        v_align=dui2.VAlign.TOP,
                    )
                ],
            )
        ],
        layout=dui2.ButtonRowLayout.FILL,
        content_align=dui2.HAlign.RIGHT,
        title_align=dui2.HAlign.RIGHT,
    )
    return dataclass_to_dict(row)


def test_unknown_enum_values_fall_back() -> None:
    """Values from a newer server decode to each field's fallback."""
    data = _button_row_dict()

    # Sanity check: the known values round-trip.
    row = dataclass_from_dict(dui2.ButtonRow, data, lossy=True)
    assert row.layout is dui2.ButtonRowLayout.FILL
    assert row.content_align is dui2.HAlign.RIGHT
    assert row.buttons[0].style is dui2.ButtonStyle.TAB

    # Now pretend a newer server sent values we have never heard of.
    bogus = '_unknown_'
    data['lo'] = bogus
    data['ca'] = bogus
    data['ta'] = bogus
    button = data['b'][0]
    button['y'] = bogus
    button['c'][0]['ha'] = bogus
    button['c'][0]['va'] = bogus

    row = dataclass_from_dict(dui2.ButtonRow, data, lossy=True)
    assert row.layout is dui2.ButtonRowLayout.SCROLL
    assert row.content_align is dui2.HAlign.LEFT
    assert row.title_align is dui2.HAlign.LEFT
    assert row.buttons[0].style is dui2.ButtonStyle.SQUARE
    decorations = row.buttons[0].decorations
    assert decorations is not None
    text = decorations[0]
    assert isinstance(text, dui2.Text)
    assert text.h_align is dui2.HAlign.CENTER
    assert text.v_align is dui2.VAlign.CENTER

    # Fallbacks change data, so they only apply to lossy loads (which
    # is how clients decode responses).
    with pytest.raises(ValueError):
        dataclass_from_dict(dui2.ButtonRow, data)


def test_unknown_window_layout_falls_back() -> None:
    """A window layout from a newer server shows as WIDE_TALL.

    (A middling shape, rarely far off. An *omitted* layout is another
    matter: that has always meant LARGE and must keep doing so.)
    """
    browse = dui2.Browse(dui2.Request('/foo'), layout=dui2.WindowLayout.VIEWER)
    data = dataclass_to_dict(browse)
    data['lo'] = '_unknown_'
    loaded = dataclass_from_dict(dui2.Browse, data, lossy=True)
    assert loaded.layout is dui2.WindowLayout.WIDE_TALL

    del data['lo']
    loaded = dataclass_from_dict(dui2.Browse, data, lossy=True)
    assert loaded.layout is dui2.WindowLayout.LARGE


def test_window_layout_defaults_keep_wire_meaning() -> None:
    """Layouts default to WIDE_TALL without changing what omission means.

    Clients in the field read an omitted ``Browse`` layout as LARGE
    and an omitted host-button layout as WIDE, so the new default must
    be written out and those old meanings must still be what's omitted.
    """
    # TODO(2026-11-23): Goes with the soft_defaults on Browse.layout and
    # hostui.Button.layout; when those go, omission means WIDE_TALL.
    import bacommon.hostui as hui

    req = dui2.Request('/foo')

    browse = dui2.Browse(req)
    assert browse.layout is dui2.WindowLayout.WIDE_TALL
    assert dataclass_to_dict(browse)['lo'] == 'wt'
    assert 'lo' not in dataclass_to_dict(
        dui2.Browse(req, layout=dui2.WindowLayout.LARGE)
    )

    button = hui.Button(
        label=LangStrSpecValue.literal('x'),
        placement=hui.ButtonPlacement.PARTY_MENU,
        request=req,
    )
    assert button.layout is dui2.WindowLayout.WIDE_TALL
    data = dataclass_to_dict(button)
    assert data['w'] == 'wt'
    del data['w']
    assert (
        dataclass_from_dict(hui.Button, data).layout is dui2.WindowLayout.WIDE
    )


def test_host_button_browse_keeps_legacy_fields() -> None:
    """A host button made from a browse still reads right on old builds.

    Builds before ``BUTTON_BROWSE_BUILD`` read only ``request`` (with
    any state folded in) and ``layout``; newer ones read ``browse``.
    """
    # TODO: Goes with the deprecated hostui.Button request/layout
    # fields (removed along with api 9 support).
    import bacommon.hostui as hui

    browse = dui2.Browse(
        dui2.Request('/foo', args={'a': 1}),
        state={'s': 2},
        layout=dui2.WindowLayout.WIDE,
        background_color=(0.1, 0.2, 0.3),
    )
    button = hui.Button.for_browse(
        label=LangStrSpecValue.literal('x'),
        placement=hui.ButtonPlacement.PARTY_MENU,
        browse=browse,
    )
    data = dataclass_to_dict(button)

    # What an old client sees.
    legacy = dict(data)
    del legacy['b']
    old = dataclass_from_dict(hui.Button, legacy)
    assert old.browse is None
    assert old.get_browse().request == dui2.Request(
        '/foo', args={'a': 1}, state={'s': 2}
    )
    assert old.get_browse().layout is dui2.WindowLayout.WIDE

    # What a new one sees.
    new = dataclass_from_dict(hui.Button, data)
    assert new.get_browse() == browse
