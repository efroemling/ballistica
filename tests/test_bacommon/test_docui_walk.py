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
from efro.dataclassio import dataclass_to_json

if TYPE_CHECKING:
    from bacommon.langstr import LangStrSpec

PKG = 'a-0.pkg.1'


def _res(name: str) -> LangStrSpecResource:
    return LangStrSpecResource(apverid=PKG, name=name)


def _text(name: str) -> dui2.Text:
    return dui2.Text(text=_res(name), position=(0.0, 0.0), size=(0.0, 0.0))


def _image(pkg: str) -> dui2.Image:
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


def _apverids(page: dui2.Page) -> set[str]:
    acc: set[str] = set()

    def _ref(ref: TextureSpec | MeshSpec | int, _kind: object) -> None:
        assert not isinstance(ref, int)
        acc.add(ref._apverid)

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


def test_reaches_refs_including_inside_frames() -> None:
    """Every texture and mesh slot, however deeply nested."""
    deep = dui2.Frame(decorations=[_image('a-0.deep.1')], position=(0.0, 0.0))
    page = dui2.Page(
        title=_res('t'),
        rows=[
            dui2.ButtonRow(
                buttons=[
                    dui2.Button(
                        size=(1, 1),
                        texture=TextureSpec('a-0.btn.1', 'textures/btn'),
                        decorations=[
                            _image('a-0.loose.1'),
                            dui2.Frame(decorations=[deep], position=(0.0, 0.0)),
                        ],
                    )
                ]
            )
        ],
    )
    assert _apverids(page) == {'a-0.btn.1', 'a-0.loose.1', 'a-0.deep.1'}


def test_strings_inside_frames_are_reached() -> None:
    """The omission that motivated consolidating this."""
    frame = dui2.Frame(decorations=[_text('inframe')], position=(0.0, 0.0))
    page = dui2.Page(
        title=_res('t'),
        rows=[
            dui2.ButtonRow(
                buttons=[dui2.Button(size=(1, 1), decorations=[frame])]
            )
        ],
    )
    assert 'inframe' in _names(page)


def test_callbacks_replace_in_place() -> None:
    """Returning a value rewrites the slot; None leaves it alone."""
    replacement = _res('replaced')
    text = _text('original')
    frame = dui2.Frame(decorations=[text], position=(0.0, 0.0))
    page = dui2.Page(
        title=_res('t'),
        rows=[
            dui2.ButtonRow(
                buttons=[dui2.Button(size=(1, 1), decorations=[frame])]
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
        elif type_id is dui2.DecorationTypeID.FRAME:
            inst = dui2.Frame(decorations=[], position=(0.0, 0.0))
        elif type_id is dui2.DecorationTypeID.DISPLAY_ITEM:
            import bacommon.legacydisplayitem as lditm

            inst = dui2.DisplayItem(
                wrapper=lditm.Wrapper.for_item(lditm.Test()),
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
    ``collect_apverids`` above all -- set each texture, icon and mesh
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
