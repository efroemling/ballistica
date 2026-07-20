# Released under the MIT License. See LICENSE for details.
#
# Auto-generated; do not edit by hand.
"""Asset-package wrapper for ``a-0.babuiltinassets.260719g`` (bauiv1).

Bare minimum assets always bundled with the engine.

These are loaded at launch and always available in the C++ layer.
"""

# ba_meta require api 9
# ba_meta require asset-package a-0.babuiltinassets.260719g

# pylint: disable=useless-suppression
# pylint: disable=too-many-lines
# pylint: disable=too-few-public-methods, disallowed-name

__asset_package__ = 'a-0.babuiltinassets.260719g'

from typing import TYPE_CHECKING

from bauiv1._assetref import AssetRefDir

from bacommon.langstr import LangStrDir

if TYPE_CHECKING:
    from bauiv1._assetref import MeshRef, SoundRef, TextureRef
    from bacommon.langstr import LangStr

    class AudioGroup:
        """
        Sounds needed during engine bootstrap and early UI (clicks, errors, and
        other always-available effects).

        See source for the full asset list.
        """

        blank: SoundRef
        blip: SoundRef
        cash_register: SoundRef
        click01: SoundRef
        cork_pop: SoundRef
        deek: SoundRef
        ding: SoundRef
        error: SoundRef
        gun_cocking: SoundRef
        powerdown01: SoundRef
        punch01: SoundRef
        score_increase: SoundRef
        sparkle01: SoundRef
        sparkle02: SoundRef
        sparkle03: SoundRef
        swish: SoundRef
        swish2: SoundRef
        swish3: SoundRef
        tap: SoundRef
        ticking_crazy: SoundRef

    class MeshesGroup:
        """
        Meshes needed during engine bootstrap and early UI.

        See source for the full asset list.
        """

        action_button_bottom: MeshRef
        action_button_left: MeshRef
        action_button_right: MeshRef
        action_button_top: MeshRef
        arrow_back: MeshRef
        arrow_front: MeshRef
        box: MeshRef
        boxing_glove: MeshRef
        button_back_opaque: MeshRef
        button_back_small_opaque: MeshRef
        button_back_small_transparent: MeshRef
        button_back_transparent: MeshRef
        button_large_opaque: MeshRef
        button_large_transparent: MeshRef
        button_larger_opaque: MeshRef
        button_larger_transparent: MeshRef
        button_medium_opaque: MeshRef
        button_medium_transparent: MeshRef
        button_small_opaque: MeshRef
        button_small_transparent: MeshRef
        button_square_opaque: MeshRef
        button_square_transparent: MeshRef
        button_tab_opaque: MeshRef
        button_tab_transparent: MeshRef
        check_transparent: MeshRef
        cross_out: MeshRef
        cylinder: MeshRef
        eye_ball: MeshRef
        eye_ball_iris: MeshRef
        eye_lid: MeshRef
        flag_pole: MeshRef
        flag_stand: MeshRef
        flash: MeshRef
        hair_tuft1: MeshRef
        hair_tuft1b: MeshRef
        hair_tuft2: MeshRef
        hair_tuft3: MeshRef
        hair_tuft4: MeshRef
        image16x1: MeshRef
        image1x1: MeshRef
        image1x1_full_screen: MeshRef
        image1x1_vrfull_screen: MeshRef
        image2x1: MeshRef
        image4x1: MeshRef
        locator: MeshRef
        locator_box: MeshRef
        locator_circle: MeshRef
        locator_circle_outline: MeshRef
        overlay_guide: MeshRef
        scorch: MeshRef
        scroll_bar_thumb_opaque: MeshRef
        scroll_bar_thumb_short_opaque: MeshRef
        scroll_bar_thumb_short_simple: MeshRef
        scroll_bar_thumb_short_transparent: MeshRef
        scroll_bar_thumb_simple: MeshRef
        scroll_bar_thumb_transparent: MeshRef
        scroll_bar_trough_transparent: MeshRef
        shield: MeshRef
        shock_wave: MeshRef
        shrapnel1: MeshRef
        shrapnel_board: MeshRef
        shrapnel_slime: MeshRef
        soft_edge_inside: MeshRef
        soft_edge_outside: MeshRef
        text_box_transparent: MeshRef
        vr_fade: MeshRef
        vr_overlay: MeshRef
        window_hsmall_vmed_opaque: MeshRef
        window_hsmall_vmed_transparent: MeshRef
        window_hsmall_vsmall_opaque: MeshRef
        window_hsmall_vsmall_transparent: MeshRef
        wing: MeshRef

    class StringsAudioGroup:
        """
        Audio-related messages: music/custom-soundtrack playback errors.

        See source for the full asset list.
        """

        def music_play_error(self, *, music: str | LangStr) -> LangStr:
            """
            Error screen-message shown when a custom-soundtrack music file fails
            to play; the placeholder is the quoted filename.

            English: "Error playing music: {music}"
            """

    class StringsInputGroup:
        """
        Input-device strings: device display names and connect/disconnect
        notices.

        See source for the full asset list.
        """

        def axis(self, *, number: str | LangStr) -> LangStr:
            """
            Short lowercase label identifying a numbered joystick axis by index;
            used inline in axis-name displays such as the controls-configuration
            UI. The {number} placeholder is the axis index.

            English: "axis {number}"
            """

        def button(self, *, number: str | LangStr) -> LangStr:
            """
            Short lowercase label identifying a numbered controller button by
            index; used inline in button-name displays such as the
            controls-configuration UI. The {number} placeholder is the button
            index.

            English: "button {number}"
            """

        def controller_connected(self, *, controller: str | LangStr) -> LangStr:
            """
            Transient screen-message shown when a single game controller
            connects, naming the device (several connecting at once use a
            separate counted message).

            English: "{controller} connected."
            """

        #: Transient screen-message shown at app startup when exactly one game
        #: controller is detected (multiple controllers at startup use a
        #: separate counted message).
        #:
        #: English: "1 controller detected."
        controller_detected: LangStr

        def controller_disconnected(
            self, *, controller: str | LangStr
        ) -> LangStr:
            """
            Transient screen-message shown when a single game controller
            disconnects, naming the device (several disconnecting at once use a
            separate counted message).

            English: "{controller} disconnected."
            """

        def controller_reconnected(
            self, *, controller: str | LangStr
        ) -> LangStr:
            """
            Transient screen-message shown when a previously-connected game
            controller (e.g. a BombSquad Remote phone client) reconnects, naming
            the device.

            English: "{controller} reconnected."
            """

        def controllers_connected(self, *, count: int) -> LangStr:
            """
            Transient screen-message shown when multiple game controllers
            connect at the same time (a single controller connecting shows a
            different message naming that controller).

            English: (one) "# controller connected." / (other) "# controllers
            connected."
            """

        def controllers_detected(self, *, count: int) -> LangStr:
            """
            Transient screen-message shown at app startup when more than one
            game controller is detected at once (a single controller at startup
            uses a separate message).

            English: (one) "# controller detected." / (other) "# controllers
            detected."
            """

        def controllers_disconnected(self, *, count: int) -> LangStr:
            """
            Transient screen-message shown when multiple game controllers
            disconnect at the same time (a single controller disconnecting shows
            a different message naming that controller).

            English: (one) "# controller disconnected." / (other) "# controllers
            disconnected."
            """

        #: Display name for the keyboard input device; shown in input-device
        #: lists, controls-configuration UI, and messages naming the device.
        #:
        #: English: "Keyboard"
        keyboard: LangStr

        #: Display name for the touch-screen input device; shown in input-device
        #: lists, controls-configuration UI, and messages naming the device.
        #:
        #: English: "TouchScreen"
        touch_screen: LangStr

        #: Warning screen-message shown when the touchscreen joins the game
        #: while physical controllers are already active (touch joins are often
        #: accidental then); tells the player how to back out. 'Menu' and 'Leave
        #: Game' refer to in-game menu items.
        #:
        #: English: "You have joined with the touchscreen. If this was a
        #: mistake, tap Menu -> Leave Game with it to back out."
        touch_screen_join_warning: LangStr

        #: Confirmation screen-message shown in VR mode when the player resets
        #: the headset's forward orientation via their controller.
        #:
        #: English: "VR orientation reset."
        vr_orientation_reset: LangStr

    class StringsNetGroup:
        """
        Networking error messages shown to the player.

        See source for the full asset list.
        """

        #: Error screen-message shown when the player enters a malformed network
        #: address trying to connect to a game party.
        #:
        #: English: "Error: invalid address."
        invalid_address: LangStr

    class StringsReplayGroup:
        """
        Game-replay playback error messages.

        See source for the full asset list.
        """

        #: Error screen-message shown when a game replay file can't be read
        #: (corrupt or truncated).
        #:
        #: English: "Error reading replay file."
        read_error: LangStr

        #: Error screen-message shown when a saved game replay was recorded by
        #: an incompatible game version and can't be played back.
        #:
        #: English: "Sorry, this replay was made in a different version of the
        #: game and can't be used."
        version_error: LangStr

    class StringsSessionGroup:
        """
        Gameplay-session messages shown by the host: idle-player kick notices
        and similar.

        See source for the full asset list.
        """

        def kick_idle_kicked(self, *, name: str | LangStr) -> LangStr:
            """
            Screen-message shown on the host when a player is removed from the
            game for being idle too long (the kick-idle-players option).

            English: "Kicking {name} for being idle."
            """

        def kick_idle_warning(
            self, *, seconds: int, name: str | LangStr
        ) -> LangStr:
            """
            Screen-message warning shown on the host shortly before an idle
            player gets kicked (the kick-idle-players option); followed by the
            kick_idle_warning_settings note.

            English: (one) "{name} will be kicked in # second if still idle." /
            (other) "{name} will be kicked in # seconds if still idle."
            """

        #: Parenthesized note shown right after the kick_idle_warning message,
        #: pointing at where the kick-idle-players behavior can be disabled.
        #: 'Settings' and 'Advanced' refer to the in-game settings menu
        #: sections.
        #:
        #: English: "(you can turn this off in Settings -> Advanced)"
        kick_idle_warning_settings: LangStr

    class StringsUiGroup:
        """
        General UI strings: menu-control ownership messages and list-navigation
        hints.

        See source for the full asset list.
        """

        def arrows_to_exit_list(
            self, *, left: str | LangStr, right: str | LangStr
        ) -> LangStr:
            """
            Lowercase hint shown (with an error sound) when the player hits the
            edge of a UI list; tells them how to move focus out of it. The two
            placeholders are substituted with left/right arrow glyph characters.

            English: "press {left} or {right} to exit list"
            """

        def has_menu_control(self, *, name: str | LangStr) -> LangStr:
            """
            Screen-message shown when an input device tries to use a menu
            another device currently controls; names the controlling device. A
            timeout suffix (menu_control_time_out or menu_control_will_time_out)
            is appended after it.

            English: "{name} has menu control."
            """

        def menu_control_time_out(self, *, seconds: int) -> LangStr:
            """
            Parenthesized suffix appended after the has_menu_control message
            once the controlling device's ownership is close to expiring; gives
            the remaining seconds.

            English: (one) "(times out in # second)" / (other) "(times out in #
            seconds)"
            """

        #: Parenthesized suffix appended after the has_menu_control message
        #: while the controlling device's ownership is not yet close to
        #: expiring.
        #:
        #: English: "(will time out if idle)"
        menu_control_will_time_out: LangStr

    class StringsGroup:
        """
        New-format engine strings needed early or accessed from the C++ layer
        via the builtin-strings API (see ballistica-internal
        strings-asset-migration decision D22).

        See source for the full asset list.
        """

        audio: StringsAudioGroup
        input: StringsInputGroup
        net: StringsNetGroup
        replay: StringsReplayGroup
        session: StringsSessionGroup
        ui: StringsUiGroup

    class TexturesGroup:
        """
        Textures needed during engine bootstrap and early UI, including the
        reflection cube-maps.

        See source for the full asset list.
        """

        action_buttons: TextureRef
        arrow: TextureRef
        back_icon: TextureRef
        black: TextureRef
        bomb_button: TextureRef
        boxing_gloves_color: TextureRef
        button_square: TextureRef
        button_square_wide: TextureRef
        character_icon_mask: TextureRef
        circle: TextureRef
        circle_no_alpha: TextureRef
        circle_outline: TextureRef
        circle_outline_no_alpha: TextureRef
        circle_shadow: TextureRef
        circle_soft: TextureRef
        cursor: TextureRef
        explosion: TextureRef
        eye_color: TextureRef
        eye_color_tint_mask: TextureRef
        flag_pole_color: TextureRef
        font_big: TextureRef
        font_extras: TextureRef
        font_extras2: TextureRef
        font_extras3: TextureRef
        font_extras4: TextureRef
        font_extras5: TextureRef
        font_small0: TextureRef
        font_small1: TextureRef
        font_small2: TextureRef
        font_small3: TextureRef
        font_small4: TextureRef
        font_small5: TextureRef
        font_small6: TextureRef
        font_small7: TextureRef
        fuse: TextureRef
        glow: TextureRef
        light: TextureRef
        light_sharp: TextureRef
        light_soft: TextureRef
        menu_button: TextureRef
        nub: TextureRef
        ouya_abutton: TextureRef
        page_left_right: TextureRef
        rgb_stripes: TextureRef
        scorch: TextureRef
        scorch_big: TextureRef
        scroll_widget: TextureRef
        scroll_widget_glow: TextureRef
        shadow: TextureRef
        shadow_sharp: TextureRef
        shadow_soft: TextureRef
        shield: TextureRef
        shrapnel1_color: TextureRef
        smoke: TextureRef
        soft_rect: TextureRef
        soft_rect2: TextureRef
        soft_rect_vertical: TextureRef
        sparks: TextureRef
        spinner: TextureRef
        spinner0: TextureRef
        spinner1: TextureRef
        spinner10: TextureRef
        spinner11: TextureRef
        spinner2: TextureRef
        spinner3: TextureRef
        spinner4: TextureRef
        spinner5: TextureRef
        spinner6: TextureRef
        spinner7: TextureRef
        spinner8: TextureRef
        spinner9: TextureRef
        start_button: TextureRef
        text_clear_button: TextureRef
        touch_arrows: TextureRef
        touch_arrows_actions: TextureRef
        ui_atlas: TextureRef
        ui_atlas2: TextureRef
        users_button: TextureRef
        white: TextureRef
        window_hsmall_vmed: TextureRef
        window_hsmall_vsmall: TextureRef
        wings: TextureRef

    #: The ``audio`` group - 20 assets (``blank``, ``blip``, ``cash_register``,
    #: ``click01``, ``cork_pop``, and 15 more). Full list in source.
    audio: AudioGroup

    #: The ``meshes`` group - 72 assets (``action_button_bottom``,
    #: ``action_button_left``, ``action_button_right``, ``action_button_top``,
    #: ``arrow_back``, and 67 more). Full list in source.
    meshes: MeshesGroup

    #: The ``strings`` group - 24 strings (``audio``, ``input``, ``net``,
    #: ``replay``, ``session``, and 19 more). Full list in source.
    strings: StringsGroup

    #: The ``textures`` group - 82 assets (``action_buttons``, ``arrow``,
    #: ``back_icon``, ``black``, ``bomb_button``, and 77 more). Full list in
    #: source.
    textures: TexturesGroup

_TREE = {
    'audio': {
        'blank': 's',
        'blip': 's',
        'cash_register': 's',
        'click01': 's',
        'cork_pop': 's',
        'deek': 's',
        'ding': 's',
        'error': 's',
        'gun_cocking': 's',
        'powerdown01': 's',
        'punch01': 's',
        'score_increase': 's',
        'sparkle01': 's',
        'sparkle02': 's',
        'sparkle03': 's',
        'swish': 's',
        'swish2': 's',
        'swish3': 's',
        'tap': 's',
        'ticking_crazy': 's',
    },
    'meshes': {
        'action_button_bottom': 'm',
        'action_button_left': 'm',
        'action_button_right': 'm',
        'action_button_top': 'm',
        'arrow_back': 'm',
        'arrow_front': 'm',
        'box': 'm',
        'boxing_glove': 'm',
        'button_back_opaque': 'm',
        'button_back_small_opaque': 'm',
        'button_back_small_transparent': 'm',
        'button_back_transparent': 'm',
        'button_large_opaque': 'm',
        'button_large_transparent': 'm',
        'button_larger_opaque': 'm',
        'button_larger_transparent': 'm',
        'button_medium_opaque': 'm',
        'button_medium_transparent': 'm',
        'button_small_opaque': 'm',
        'button_small_transparent': 'm',
        'button_square_opaque': 'm',
        'button_square_transparent': 'm',
        'button_tab_opaque': 'm',
        'button_tab_transparent': 'm',
        'check_transparent': 'm',
        'cross_out': 'm',
        'cylinder': 'm',
        'eye_ball': 'm',
        'eye_ball_iris': 'm',
        'eye_lid': 'm',
        'flag_pole': 'm',
        'flag_stand': 'm',
        'flash': 'm',
        'hair_tuft1': 'm',
        'hair_tuft1b': 'm',
        'hair_tuft2': 'm',
        'hair_tuft3': 'm',
        'hair_tuft4': 'm',
        'image16x1': 'm',
        'image1x1': 'm',
        'image1x1_full_screen': 'm',
        'image1x1_vrfull_screen': 'm',
        'image2x1': 'm',
        'image4x1': 'm',
        'locator': 'm',
        'locator_box': 'm',
        'locator_circle': 'm',
        'locator_circle_outline': 'm',
        'overlay_guide': 'm',
        'scorch': 'm',
        'scroll_bar_thumb_opaque': 'm',
        'scroll_bar_thumb_short_opaque': 'm',
        'scroll_bar_thumb_short_simple': 'm',
        'scroll_bar_thumb_short_transparent': 'm',
        'scroll_bar_thumb_simple': 'm',
        'scroll_bar_thumb_transparent': 'm',
        'scroll_bar_trough_transparent': 'm',
        'shield': 'm',
        'shock_wave': 'm',
        'shrapnel1': 'm',
        'shrapnel_board': 'm',
        'shrapnel_slime': 'm',
        'soft_edge_inside': 'm',
        'soft_edge_outside': 'm',
        'text_box_transparent': 'm',
        'vr_fade': 'm',
        'vr_overlay': 'm',
        'window_hsmall_vmed_opaque': 'm',
        'window_hsmall_vmed_transparent': 'm',
        'window_hsmall_vsmall_opaque': 'm',
        'window_hsmall_vsmall_transparent': 'm',
        'wing': 'm',
    },
    'strings': {
        'audio': {'music_play_error': ('music',)},
        'input': {
            'axis': ('number',),
            'button': ('number',),
            'controller_connected': ('controller',),
            'controller_detected': (),
            'controller_disconnected': ('controller',),
            'controller_reconnected': ('controller',),
            'controllers_connected': ('count',),
            'controllers_detected': ('count',),
            'controllers_disconnected': ('count',),
            'keyboard': (),
            'touch_screen': (),
            'touch_screen_join_warning': (),
            'vr_orientation_reset': (),
        },
        'net': {'invalid_address': ()},
        'replay': {'read_error': (), 'version_error': ()},
        'session': {
            'kick_idle_kicked': ('name',),
            'kick_idle_warning': ('seconds', 'name'),
            'kick_idle_warning_settings': (),
        },
        'ui': {
            'arrows_to_exit_list': ('left', 'right'),
            'has_menu_control': ('name',),
            'menu_control_time_out': ('seconds',),
            'menu_control_will_time_out': (),
        },
    },
    'textures': {
        'action_buttons': 't',
        'arrow': 't',
        'back_icon': 't',
        'black': 't',
        'bomb_button': 't',
        'boxing_gloves_color': 't',
        'button_square': 't',
        'button_square_wide': 't',
        'character_icon_mask': 't',
        'circle': 't',
        'circle_no_alpha': 't',
        'circle_outline': 't',
        'circle_outline_no_alpha': 't',
        'circle_shadow': 't',
        'circle_soft': 't',
        'cursor': 't',
        'explosion': 't',
        'eye_color': 't',
        'eye_color_tint_mask': 't',
        'flag_pole_color': 't',
        'font_big': 't',
        'font_extras': 't',
        'font_extras2': 't',
        'font_extras3': 't',
        'font_extras4': 't',
        'font_extras5': 't',
        'font_small0': 't',
        'font_small1': 't',
        'font_small2': 't',
        'font_small3': 't',
        'font_small4': 't',
        'font_small5': 't',
        'font_small6': 't',
        'font_small7': 't',
        'fuse': 't',
        'glow': 't',
        'light': 't',
        'light_sharp': 't',
        'light_soft': 't',
        'menu_button': 't',
        'nub': 't',
        'ouya_abutton': 't',
        'page_left_right': 't',
        'rgb_stripes': 't',
        'scorch': 't',
        'scorch_big': 't',
        'scroll_widget': 't',
        'scroll_widget_glow': 't',
        'shadow': 't',
        'shadow_sharp': 't',
        'shadow_soft': 't',
        'shield': 't',
        'shrapnel1_color': 't',
        'smoke': 't',
        'soft_rect': 't',
        'soft_rect2': 't',
        'soft_rect_vertical': 't',
        'sparks': 't',
        'spinner': 't',
        'spinner0': 't',
        'spinner1': 't',
        'spinner10': 't',
        'spinner11': 't',
        'spinner2': 't',
        'spinner3': 't',
        'spinner4': 't',
        'spinner5': 't',
        'spinner6': 't',
        'spinner7': 't',
        'spinner8': 't',
        'spinner9': 't',
        'start_button': 't',
        'text_clear_button': 't',
        'touch_arrows': 't',
        'touch_arrows_actions': 't',
        'ui_atlas': 't',
        'ui_atlas2': 't',
        'users_button': 't',
        'white': 't',
        'window_hsmall_vmed': 't',
        'window_hsmall_vsmall': 't',
        'wings': 't',
    },
}


if not TYPE_CHECKING:
    audio = AssetRefDir(__asset_package__, _TREE['audio'], 'audio')
    meshes = AssetRefDir(__asset_package__, _TREE['meshes'], 'meshes')
    strings = LangStrDir(__asset_package__, _TREE['strings'], 'strings')
    textures = AssetRefDir(__asset_package__, _TREE['textures'], 'textures')
