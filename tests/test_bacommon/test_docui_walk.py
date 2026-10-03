# Released under the MIT License. See LICENSE for details.
#
"""Testing the shared doc-ui page traversal.

Several consumers need to reach every string slot or asset reference in
a page. They used to each walk it themselves, and each missed a
decoration type at some point -- silently, since an unmatched type
contributes nothing and the walk still returns a plausible answer. The
traversal lives in one place now; these check it reaches everything and
that it cannot quietly stop covering a new decoration type.
"""

# pylint: disable=protected-access

from typing import TYPE_CHECKING

import bacommon.docui.v2 as dui2
from bacommon.assetspec import TextureSpec, MeshSpec
from bacommon.docui.walk import walk_page
from bacommon.langstr import LangStrSpecResource
from bacommon.assetpackage import ApverNum
from efro.dataclassio import dataclass_to_json

if TYPE_CHECKING:
    from bacommon.langstr import LangStrSpec

PKG = ApverNum(1)


def _res(name: str) -> LangStrSpecResource:
    return LangStrSpecResource(apvernum=PKG, name=name)


def _text(name: str) -> dui2.Text:
    return dui2.Text(text=_res(name), position=(0.0, 0.0), size=(0.0, 0.0))


def _image(pkg: ApverNum) -> dui2.Image:
    return dui2.Image(
        texture=TextureSpec(pkg, 'textures/a'),
        tint_texture=TextureSpec(pkg, 'textures/b'),
        mesh_opaque=MeshSpec(pkg, 'meshes/c'),
        position=(0.0, 0.0),
        size=(1.0, 1.0),
    )


def _names(page: dui2.Page) -> set[str]:
    out: list['LangStrSpec | int'] = []

    def _collect(lstr: 'LangStrSpec | int') -> None:
        out.append(lstr)

    walk_page(page, langstr=_collect)
    return {s.name for s in out if isinstance(s, LangStrSpecResource)}


def _apvernums(page: dui2.Page) -> set[ApverNum]:
    acc: set[ApverNum] = set()

    def _ref(ref: TextureSpec | MeshSpec | int, _kind: object) -> None:
        assert not isinstance(ref, int)
        acc.add(ref._apvernum)

    walk_page(page, assetref=_ref)
    return acc


def test_reaches_every_string_slot() -> None:
    """Titles, subtitles, labels, decorations and effect messages."""
    import bacommon.clienteffect as clfx

    page = dui2.Page(
        title=_res('pagetitle'),
        rows=[
            dui2.ButtonRow(
                title=_res('rowtitle'),
                subtitle=_res('rowsub'),
                header_decorations_left=[_text('hdrleft')],
                header_decorations_center=[_text('hdrcenter')],
                header_decorations_right=[_text('hdrright')],
                buttons=[
                    dui2.Button(
                        size=(1, 1),
                        label=_res('label'),
                        decorations=[_text('deco')],
                        action=dui2.Local(
                            immediate_client_effects=[
                                clfx.ScreenMessageV2(message=_res('effect'))
                            ]
                        ),
                    )
                ],
            )
        ],
    )
    assert _names(page) == {
        'pagetitle',
        'rowtitle',
        'rowsub',
        'hdrleft',
        'hdrcenter',
        'hdrright',
        'label',
        'deco',
        'effect',
    }


def test_reaches_refs_including_text_images() -> None:
    """Every texture and mesh slot, including a text's end images.

    A text-image texture the walk missed would never be resolved (or,
    indexed, never de-indexed) and would fail at render time.
    """
    text = _text('priced')
    text.image_left = dui2.TextImage(
        texture=TextureSpec(ApverNum(11), 'textures/l'), size=(1.0, 1.0)
    )
    text.image_right = dui2.TextImage(
        texture=TextureSpec(ApverNum(12), 'textures/r'), size=(1.0, 1.0)
    )
    page = dui2.Page(
        title=_res('t'),
        rows=[
            dui2.ButtonRow(
                buttons=[
                    dui2.Button(
                        size=(1, 1),
                        texture=TextureSpec(ApverNum(13), 'textures/btn'),
                        decorations=[_image(ApverNum(14)), text],
                    )
                ]
            )
        ],
    )
    assert _apvernums(page) == {
        ApverNum(13),
        ApverNum(14),
        ApverNum(11),
        ApverNum(12),
    }


def test_depictions_add_nothing_to_the_page() -> None:
    """Depictions are self-sufficient: no refs reach the page's walk.

    An image depiction's texture must not be gathered for the page to
    resolve first (or indexed against the page's packages); it is
    fetched on demand behind a standin. Same for the page's viewer.
    """
    import bacommon.depiction as bdep

    image = bdep.ImageDepiction(
        texture=TextureSpec(ApverNum(15), 'textures/chest'),
        tint_texture=TextureSpec(ApverNum(15), 'textures/tint'),
    )
    page = dui2.Page(
        title=_res('t'),
        viewer=bdep.CharacterViewerDepiction('{}'),
        rows=[
            dui2.ButtonRow(
                buttons=[
                    dui2.Button(
                        size=(1, 1),
                        decorations=[
                            dui2.Depiction(
                                image, position=(0.0, 0.0), size=(1.0, 1.0)
                            )
                        ],
                    )
                ]
            )
        ],
    )
    assert _apvernums(page) == set()


def test_decoration_strings_are_reached() -> None:
    """Strings in a button's decorations count like any other."""
    page = dui2.Page(
        title=_res('t'),
        rows=[
            dui2.ButtonRow(
                buttons=[
                    dui2.Button(size=(1, 1), decorations=[_text('indeco')])
                ]
            )
        ],
    )
    assert 'indeco' in _names(page)


def test_callbacks_replace_in_place() -> None:
    """Returning a value rewrites the slot; None leaves it alone."""
    replacement = _res('replaced')
    text = _text('original')
    page = dui2.Page(
        title=_res('t'),
        rows=[
            dui2.ButtonRow(
                buttons=[dui2.Button(size=(1, 1), decorations=[text])]
            )
        ],
    )

    walk_page(page, langstr=lambda _s: replacement)
    assert text.text is replacement
    assert page.title is replacement

    # A read-only visitor returns None and must change nothing.
    walk_page(page, langstr=lambda _s: None)
    assert text.text is replacement


def test_every_decoration_type_is_handled() -> None:
    """No decoration type may fall through the traversal unnoticed.

    The traversal dispatches on the type-id with ``assert_never`` at
    the end, so a new decoration type is a build-time error rather than
    a slot nothing visits. This checks the runtime half of that: every
    id the multitype knows about walks without raising.
    """
    for type_id in dui2.DecorationTypeID:
        deco = dui2.Decoration.get_type(type_id)
        # Build a minimal instance of each; a few need arguments.
        if type_id is dui2.DecorationTypeID.TEXT:
            inst: dui2.Decoration = _text('x')
        elif type_id is dui2.DecorationTypeID.IMAGE:
            inst = _image(PKG)
        elif type_id is dui2.DecorationTypeID.DEPICTION:
            import bacommon.depiction as bdep

            inst = dui2.Depiction(
                bdep.CharacterIconDepiction('{}'),
                position=(0.0, 0.0),
                size=(1.0, 1.0),
            )
        else:
            inst = deco()  # UnknownDecoration takes no args.

        page = dui2.Page(
            title=_res('t'),
            rows=[
                dui2.ButtonRow(
                    buttons=[dui2.Button(size=(1, 1), decorations=[inst])]
                )
            ],
        )
        # Must not raise for any known decoration type.
        walk_page(page, langstr=lambda s: None, assetref=lambda r, k: None)


def test_walk_reaches_client_effect_sounds() -> None:
    """A button's client-effect sound is visited, not just its message.

    The regression this guards: the page walk used to reach into
    client-effects for ``ScreenMessageV2.message`` while ignoring
    ``PlaySoundV2.sound``, so the page/effects boundary was arbitrary.
    An indexed sound would then never have been de-indexed and would
    have failed at play time.
    """
    import bacommon.clienteffect as clfx
    from bacommon.assetspec import SoundSpec

    seen: list[object] = []

    page = dui2.Page(
        title=_res('t'),
        rows=[
            dui2.ButtonRow(
                buttons=[
                    dui2.Button(
                        size=(1, 1),
                        action=dui2.Local(
                            immediate_client_effects=[
                                clfx.PlaySoundV2(
                                    sound=SoundSpec(PKG, 'audio/swish')
                                ),
                                clfx.ScreenMessageV2(message=_res('hi')),
                            ]
                        ),
                    )
                ]
            )
        ],
    )

    def _ref(ref: object, _kind: object) -> None:
        seen.append(ref)

    walk_page(page, assetref=_ref)
    assert seen == [SoundSpec(PKG, 'audio/swish')]


def test_walk_effects_replaces_sound() -> None:
    """The effects walk can rewrite a sound slot in place."""
    import bacommon.clienteffect as clfx
    from bacommon.assetspec import SoundSpec

    effects: list[clfx.Effect] = [
        clfx.PlaySoundV2(sound=SoundSpec(PKG, 'audio/swish'))
    ]

    clfx.walk_effects(effects, assetref=lambda r, k: 42)

    assert isinstance(effects[0], clfx.PlaySoundV2)
    assert effects[0].sound == 42


def test_walk_effects_covers_every_effect_type() -> None:
    """Every effect type is handled; none falls through assert_never."""
    import bacommon.clienteffect as clfx

    for type_id in clfx.EffectTypeID:
        effect = clfx.Effect.get_type(type_id)
        if type_id is clfx.EffectTypeID.SCREEN_MESSAGE_V2:
            inst: clfx.Effect = clfx.ScreenMessageV2(message=_res('m'))
        elif type_id is clfx.EffectTypeID.SOUND_V2:
            from bacommon.assetspec import SoundSpec

            inst = clfx.PlaySoundV2(sound=SoundSpec(PKG, 'audio/x'))
        elif type_id is clfx.EffectTypeID.LEGACY_SCREEN_MESSAGE:
            inst = clfx.LegacyScreenMessage(message='m')
        elif type_id is clfx.EffectTypeID.SCREEN_MESSAGE:
            inst = clfx.ScreenMessage(message='m')
        elif type_id is clfx.EffectTypeID.SOUND:
            inst = clfx.PlaySound(sound=clfx.Sound.ERROR)
        elif type_id is clfx.EffectTypeID.DELAY:
            inst = clfx.Delay(seconds=1.0)
        elif type_id is clfx.EffectTypeID.CHEST_WAIT_TIME_ANIMATION:
            import datetime

            now = datetime.datetime.now(datetime.UTC)
            inst = clfx.ChestWaitTimeAnimation(
                chestid='c', duration=1.0, startvalue=now, endvalue=now
            )
        elif type_id is clfx.EffectTypeID.TICKETS_ANIMATION:
            inst = clfx.TicketsAnimation(duration=1.0, startvalue=0, endvalue=1)
        elif type_id is clfx.EffectTypeID.TOKENS_ANIMATION:
            inst = clfx.TokensAnimation(duration=1.0, startvalue=0, endvalue=1)
        elif type_id is clfx.EffectTypeID.KEYFRAME_ANIMATION:
            inst = clfx.KeyframeAnimation(
                target='t', keys=[clfx.Keyframe(time=0.0)]
            )
        else:
            inst = effect()  # Unknown takes no args.

        # Must not raise for any known effect type.
        clfx.walk_effects(
            [inst], langstr=lambda s: None, assetref=lambda r, k: None
        )


def test_read_only_walk_leaves_asset_slots_intact() -> None:
    """A visitor returning None must not blank the slot.

    Regression guard for a live bug: the asset path assigned the
    visitor's return value unconditionally, so every read-only walk --
    ``collect_apvernums`` above all -- set each texture, icon and mesh
    slot to None. That stripped the art off every v2 page during
    resolve. The string path always handled None correctly; only assets
    did not.
    """
    page = dui2.Page(
        title=_res('t'),
        rows=[
            dui2.ButtonRow(
                buttons=[
                    dui2.Button(
                        size=(1, 1),
                        texture=TextureSpec(PKG, 'textures/btn'),
                        icon=TextureSpec(PKG, 'textures/icon'),
                        decorations=[_image(PKG)],
                    )
                ]
            )
        ],
    )
    before = dataclass_to_json(page)

    # A pure reader: returns None everywhere.
    walk_page(page, langstr=lambda s: None, assetref=lambda r, k: None)

    assert dataclass_to_json(page) == before


def _menu_page() -> dui2.Page:
    import bacommon.clienteffect as clfx

    return dui2.Page(
        title=_res('t'),
        rows=[
            dui2.ButtonRow(
                buttons=[
                    dui2.Button(
                        size=(1, 1),
                        label=_res('menubutton'),
                        action=dui2.Menu(
                            items=[
                                dui2.MenuItem(
                                    label=_res('item1'),
                                    action=dui2.Local(
                                        immediate_client_effects=[
                                            clfx.ScreenMessageV2(
                                                message=_res('itemeffect')
                                            )
                                        ],
                                        sets={'a': 1},
                                    ),
                                ),
                                dui2.MenuItem(
                                    label=_res('item2'), disabled=True
                                ),
                            ]
                        ),
                    )
                ]
            )
        ],
    )


def test_menus_are_reached() -> None:
    """A menu's item labels and its items' actions are page content."""
    from bacommon.docui.walk import page_actions

    page = _menu_page()
    assert _names(page) == {
        't',
        'menubutton',
        'item1',
        'item2',
        'itemeffect',
    }

    # The menu itself, then its one item with an action.
    actions = list(page_actions(page))
    assert [type(a) for a in actions] == [dui2.Menu, dui2.Local]


def test_every_action_type_is_handled() -> None:
    """As for decorations: every known action type walks without raising."""
    for typeid in dui2.ActionTypeID:
        actiontype = dui2.Action.get_type(typeid)
        action: dui2.Action
        if actiontype is dui2.Browse or actiontype is dui2.Replace:
            action = actiontype(request=dui2.Request('/'))
        elif actiontype is dui2.Menu:
            action = dui2.Menu(items=[dui2.MenuItem(label=_res('item'))])
        else:
            action = actiontype()
        page = dui2.Page(
            title=_res('t'),
            rows=[
                dui2.ButtonRow(
                    buttons=[dui2.Button(size=(1, 1), action=action)]
                )
            ],
        )
        walk_page(page, langstr=lambda s: None, assetref=lambda r, k: None)


def test_menu_wire_round_trip() -> None:
    """Menus survive the wire, and degrade to unknown for old readers."""
    from efro.dataclassio import dataclass_from_json, dataclass_to_dict

    page = _menu_page()
    out = dataclass_from_json(dui2.Page, dataclass_to_json(page))
    assert out == page

    # What a client predating menus makes of one: an action type-id it
    # has never heard of, which the multitype hands back as unknown.
    button = page.rows[0]
    assert isinstance(button, dui2.ButtonRow)
    raw = dataclass_to_dict(button.buttons[0])
    assert raw['a']['_t'] == 'm'
    raw['a']['_t'] = 'somethingnew'
    from efro.dataclassio import dataclass_from_dict

    old = dataclass_from_dict(dui2.Button, raw, lossy=True)
    assert isinstance(old.action, dui2.UnknownAction)


def test_menus_are_refused_as_on_change() -> None:
    """Input rows can't pop up menus any more than windows."""
    import pytest

    from bacommon.docui.routes.docuitest import WidgetTestState

    with pytest.raises(ValueError):
        WidgetTestState.checkbox_row(
            lambda s: s.plain,
            on_change=dui2.Menu(items=[dui2.MenuItem(label=_res('item'))]),
        )


def _button_control_page() -> dui2.Page:
    import bacommon.clienteffect as clfx

    return dui2.Page(
        title=_res('t'),
        rows=[
            dui2.ButtonControlRow(
                title=_res('rowtitle'),
                subtitle=_res('rowsub'),
                label=_res('rowlabel'),
                footnote=_res('rowfoot'),
                header_decorations_left=[_text('hdrleft')],
                button=dui2.Button(
                    size=(1, 1),
                    label=_res('buttonlabel'),
                    texture=TextureSpec(ApverNum(13), 'textures/btn'),
                    icon=TextureSpec(ApverNum(16), 'textures/icon'),
                    decorations=[_text('deco'), _image(ApverNum(17))],
                    action=dui2.Local(
                        immediate_client_effects=[
                            clfx.ScreenMessageV2(message=_res('effect'))
                        ]
                    ),
                ),
            )
        ],
    )


def test_button_control_rows_are_reached() -> None:
    """The row's own text plus everything its button holds."""
    from bacommon.docui.walk import page_actions

    page = _button_control_page()
    assert _names(page) == {
        't',
        'rowtitle',
        'rowsub',
        'rowlabel',
        'rowfoot',
        'hdrleft',
        'buttonlabel',
        'deco',
        'effect',
    }
    assert _apvernums(page) == {ApverNum(13), ApverNum(16), ApverNum(17)}
    assert [type(a) for a in page_actions(page)] == [dui2.Local]


def test_button_control_row_wire_round_trip() -> None:
    """The row survives the wire; a control row, but not an input row."""
    from efro.dataclassio import dataclass_from_json

    page = _button_control_page()
    out = dataclass_from_json(dui2.Page, dataclass_to_json(page))
    assert out == page
    assert dui2.is_control_row(out.rows[0])
    assert not dui2.is_input_row(out.rows[0])


def test_input_rows_are_control_rows() -> None:
    """Every input row type is a control row; button rows are neither."""
    from bacommon.docui.routes.docuitest import WidgetTestState

    checkbox = WidgetTestState.checkbox_row(lambda s: s.plain)
    assert dui2.is_input_row(checkbox)
    assert dui2.is_control_row(checkbox)

    buttons = dui2.ButtonRow(buttons=[dui2.Button(size=(1, 1))])
    assert not dui2.is_input_row(buttons)
    assert not dui2.is_control_row(buttons)


def test_button_control_row_state_keys_are_validated() -> None:
    """Its button's action is held to the page's state like any other."""
    import pytest

    from bacommon.docui.routes import validate_page_state
    from bacommon.docui.routes.docuitest import WidgetTestState

    def _page(key: str) -> dui2.Page:
        return dui2.Page(
            title=_res('t'),
            state=WidgetTestState().encode(),
            rows=[
                dui2.ButtonControlRow(
                    button=dui2.Button(
                        size=(1, 1), action=dui2.Local(sets={key: True})
                    )
                )
            ],
        )

    validate_page_state(_page('plain'))
    with pytest.raises(ValueError):
        validate_page_state(_page('nosuchkey'))
