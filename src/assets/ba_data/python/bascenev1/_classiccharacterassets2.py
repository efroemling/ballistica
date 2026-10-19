# Released under the MIT License. See LICENSE for details.
#
# Auto-generated; do not edit by hand.
"""Asset-package wrapper for ``a-0.baclassiccharacterassets2.261009``
(bascenev1).

Classic characters whose sources are not intended to go public: each a whole
character (body textures and color masks, body part meshes, voice sounds, icon
and icon color mask, display name and .bchar definition), kept apart from
baclassiccharacterassets because that package's workspace is offered to everyone
to copy from. Bundled with the game beside it. Nothing here is offered as a
template or featured.
"""

# ba_meta require api 9
# ba_meta require asset-package 545

# pylint: disable=useless-suppression
# pylint: disable=too-many-lines
# pylint: disable=too-few-public-methods, disallowed-name

from typing import TYPE_CHECKING

from bacommon.assetpackage import ApverNum

from bascenev1._assetref import AssetGroup, CharacterGroup

from babase import LangStrDir

# a-0.baclassiccharacterassets2.261009
_ASSET_PACKAGE = ApverNum(545)

if TYPE_CHECKING:
    from bascenev1._assetref import (
        CharacterHandle,
        MeshHandle,
        SoundHandle,
        TextureHandle,
    )
    from babase import LangStr

    class AudioGroup:
        """
        ::

            Character voice and body sounds.

            See source for the full asset list.
        """

        ali1: SoundHandle
        ali2: SoundHandle
        ali3: SoundHandle
        ali4: SoundHandle
        ali_death: SoundHandle
        ali_fall: SoundHandle
        ali_hit1: SoundHandle
        ali_hit2: SoundHandle

    class MeshesGroup:
        """
        ::

            Character body part meshes.

            See source for the full asset list.
        """

        ali_fore_arm: MeshHandle
        ali_hand: MeshHandle
        ali_head: MeshHandle
        ali_lower_leg: MeshHandle
        ali_pelvis: MeshHandle
        ali_toes: MeshHandle
        ali_torso: MeshHandle
        ali_upper_arm: MeshHandle
        ali_upper_leg: MeshHandle

    class StringsCharactersGroup:
        """
        ::

            Playable character display names.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Character display name shown in the store, inventory, character
        #:     picker, and gameplay UIs. Chinese locales use the official mascot
        #:     name 淘公仔; others translate "Taobao Mascot" ("Taobao" stays as the
        #:     brand).
        #:
        #:     English: "Taobao Mascot"
        taobao_mascot: LangStr

    class StringsGroup:
        """
        ::

            Character display names.

            See source for the full asset list.
        """

        characters: StringsCharactersGroup

    class TexturesGroup:
        """
        ::

            Character body and icon textures and their color masks.

            See source for the full asset list.
        """

        ali_color: TextureHandle
        ali_color_mask: TextureHandle
        ali_icon: TextureHandle
        ali_icon_color_mask: TextureHandle

    class CharactersGroup:
        """Character-group type; see source for the full list."""

        taobao_mascot: CharacterHandle

    #: The ``audio`` group - 8 assets (``ali1``, ``ali2``, ``ali3``, ``ali4``,
    #: ``ali_death``, and 3 more). Full list in source.
    audio: AudioGroup

    #: The ``meshes`` group - 9 assets (``ali_fore_arm``, ``ali_hand``,
    #: ``ali_head``, ``ali_lower_leg``, ``ali_pelvis``, and 4 more). Full list
    #: in source.
    meshes: MeshesGroup

    #: The ``strings`` group - 1 string (``characters``). Full list in source.
    strings: StringsGroup

    #: The ``textures`` group - 4 assets (``ali_color``, ``ali_color_mask``,
    #: ``ali_icon``, ``ali_icon_color_mask``). Full list in source.
    textures: TexturesGroup

    #: The ``characters`` group - 1 character (``taobao_mascot``). Full list in
    #: source.
    characters: CharactersGroup

_TREE = {
    'audio': {
        'ali1': 's',
        'ali2': 's',
        'ali3': 's',
        'ali4': 's',
        'ali_death': 's',
        'ali_fall': 's',
        'ali_hit1': 's',
        'ali_hit2': 's',
    },
    'meshes': {
        'ali_fore_arm': 'm',
        'ali_hand': 'm',
        'ali_head': 'm',
        'ali_lower_leg': 'm',
        'ali_pelvis': 'm',
        'ali_toes': 'm',
        'ali_torso': 'm',
        'ali_upper_arm': 'm',
        'ali_upper_leg': 'm',
    },
    'strings': {'characters': {'taobao_mascot': ()}},
    'textures': {
        'ali_color': 't',
        'ali_color_mask': 't',
        'ali_icon': 't',
        'ali_icon_color_mask': 't',
    },
}

_CHARACTERS = {
    'characters': {
        'taobao_mascot': (
            (
                '{"b":{"ct":{"a":545,"n":"textures/ali_color"},'
                '"cm":{"a":545,"n":"textures/ali_color_mask"},'
                '"mh":{"a":545,"n":"meshes/ali_head"},'
                '"mt":{"a":545,"n":"meshes/ali_torso"},'
                '"mua":{"a":545,"n":"meshes/ali_upper_arm"},'
                '"mul":{"a":545,"n":"meshes/ali_upper_leg"},'
                '"mll":{"a":545,"n":"meshes/ali_lower_leg"},'
                '"mto":{"a":545,"n":"meshes/ali_toes"},'
                '"mfa":{"a":545,"n":"meshes/ali_fore_arm"},'
                '"mhn":{"a":545,"n":"meshes/ali_hand"},'
                '"sj":[{"a":545,"n":"audio/ali1"},{"a":545,'
                '"n":"audio/ali2"},{"a":545,"n":"audio/ali3"},'
                '{"a":545,"n":"audio/ali4"}],"sa":[{"a":545,'
                '"n":"audio/ali1"},{"a":545,"n":"audio/ali2"},'
                '{"a":545,"n":"audio/ali3"},{"a":545,'
                '"n":"audio/ali4"}],"si":[{"a":545,'
                '"n":"audio/ali_hit1"},{"a":545,"n":"audio/ali_hit2"}],'
                '"sd":[{"a":545,"n":"audio/ali_death"}],'
                '"sp":[{"a":545,"n":"audio/ali1"},{"a":545,'
                '"n":"audio/ali2"},{"a":545,"n":"audio/ali3"},'
                '{"a":545,"n":"audio/ali4"}],"sf":[{"a":545,'
                '"n":"audio/ali_fall"}],"cl":[1.0,0.5,0.0],"hl":[1.0,1.0,'
                '1.0],"tr":0.11,"so":[0.03,-0.05,0.0],"le":"n","re":"n",'
                '"rs":0.25}}'
            ),
            (
                '{"j":"{\\"b\\":{\\"tx\\":{\\"a\\":545,'
                '\\"n\\":\\"textures/ali_icon\\"},\\"cm\\":{\\"a\\":545,'
                '\\"n\\":\\"textures/ali_icon_color_mask\\"},\\"cl\\":[1.0,'
                '0.5,0.0],\\"hl\\":[1.0,1.0,1.0]}}","_t":"ci"}'
            ),
            'strings/characters/taobao_mascot',
        ),
    },
}


if not TYPE_CHECKING:
    audio = AssetGroup(_ASSET_PACKAGE, _TREE['audio'], 'audio')
    meshes = AssetGroup(_ASSET_PACKAGE, _TREE['meshes'], 'meshes')
    strings = LangStrDir(_ASSET_PACKAGE, _TREE['strings'], 'strings')
    textures = AssetGroup(_ASSET_PACKAGE, _TREE['textures'], 'textures')
    characters = CharacterGroup(
        _ASSET_PACKAGE, _CHARACTERS['characters'], 'characters'
    )
