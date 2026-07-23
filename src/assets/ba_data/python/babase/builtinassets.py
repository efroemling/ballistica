# Released under the MIT License. See LICENSE for details.
#
# Auto-generated; do not edit by hand.
"""Asset-package wrapper for ``a-0.babuiltinassets.260723a`` (babase).

Bare minimum assets always bundled with the engine.

These are loaded at launch and always available in the C++ layer.
"""

# ba_meta require api 9
# ba_meta require asset-package a-0.babuiltinassets.260723a

# pylint: disable=useless-suppression
# pylint: disable=too-many-lines
# pylint: disable=too-few-public-methods, disallowed-name

__asset_package__ = 'a-0.babuiltinassets.260723a'

from typing import TYPE_CHECKING

from babase._language import LangStrDir

if TYPE_CHECKING:
    from babase import LangStr

    class StringsAssetsGroup:
        """
        ::

            Asset-system progress and error strings: boot-time (construct-mode)
            bring-up, package download/build progress dialogs, and the
            pre-main-menu sign-in gate.

            See source for the full asset list.
        """

        def access_denied_guidance(self, *, detail: str | LangStr) -> LangStr:
            """
            ::

                Wraps a server-supplied asset access-denial explanation with
                guidance for the user; shown on the boot-time asset dialog.

                English: "{detail} Remove these mods/changes and try again."
            """

        #: ::
        #:
        #:     Status line in the boot-time asset dialog while waiting for
        #:     account sign-in so restricted assets can load.
        #:
        #:     English: "Authenticating…"
        authenticating: LangStr

        def building_assets(
            self, *, count: int, package: str | LangStr
        ) -> LangStr:
            """
            ::

                Progress-dialog line shown while the server builds assets for a
                package; updates live as the remaining count drops.

                English: (one) "Building {package} assets (# step remaining)…" /
                (other) "Building {package} assets (# steps remaining)…"
            """

        #: ::
        #:
        #:     Error on the boot-time asset dialog when this app build is too
        #:     old to load current assets (fallback wording when the server
        #:     didn't supply its own).
        #:
        #:     English: "This app version is too old to load current assets.
        #:     Please update to continue."
        client_too_old: LangStr

        def content_error_guidance(self, *, detail: str | LangStr) -> LangStr:
            """
            ::

                Wraps a server-supplied asset build-failure explanation with
                guidance for the package author; shown on the boot-time asset
                dialog (this state is nearly always seen by the author, since
                dev/test versions only resolve for them).

                English: "{detail} Fix the file in the source workspace and try
                again."
            """

        def downloading_assets(self, *, count: int) -> LangStr:
            """
            ::

                Progress-dialog line shown while asset files download; updates
                live as the remaining count drops.

                English: (one) "Downloading assets (# remaining)…" / (other)
                "Downloading assets (# remaining)…"
            """

        #: ::
        #:
        #:     Generic error on the boot-time asset dialog when asset loading
        #:     fails unexpectedly.
        #:
        #:     English: "An error occurred loading assets; see log for details."
        load_error: LangStr

        def preparing_build(self, *, package: str | LangStr) -> LangStr:
            """
            ::

                Progress-dialog line shown while a server-side asset build is
                being prepared, before per-step progress is known.

                English: "Preparing to build {package}…"
            """

        #: ::
        #:
        #:     Error on the boot-time asset dialog when a required sign-in was
        #:     not completed (attempted and failed, or timed out); a Retry
        #:     button sits below it.
        #:
        #:     English: "You must sign in to an account with access to these
        #:     assets to continue. Retry to sign in, or remove these
        #:     mods/changes."
        sign_in_failed: LangStr

        def sign_in_needed_browser(self, *, address: str | LangStr) -> LangStr:
            """
            ::

                Message on the boot-time sign-in dialog when required assets
                need a signed-in account and a web browser is available; a Sign
                In button sits below it.

                English: "Sign-in is required to load these assets. Press the
                button below, or visit {address}"
            """

        def sign_in_needed_other_device(
            self, *, address: str | LangStr
        ) -> LangStr:
            """
            ::

                Message on the boot-time sign-in dialog when required assets
                need a signed-in account and this device has no web browser.

                English: "Sign-in is required to load these assets. On another
                device, visit {address}"
            """

        #: ::
        #:
        #:     Status line in the boot-time asset dialog after a browser sign-in
        #:     completes, while the account finishes validating.
        #:
        #:     English: "Signing in…"
        signing_in: LangStr

    class StringsAudioGroup:
        """
        ::

            Audio-related messages: music/custom-soundtrack playback errors.

            See source for the full asset list.
        """

        def music_play_error(self, *, music: str | LangStr) -> LangStr:
            """
            ::

                Error screen-message shown when a custom-soundtrack music file
                fails to play; the placeholder is the quoted filename.

                English: "Error playing music: {music}"
            """

    class StringsInputGroup:
        """
        ::

            Input-device strings: device display names and connect/disconnect
            notices.

            See source for the full asset list.
        """

        def axis(self, *, number: str | LangStr) -> LangStr:
            """
            ::

                Short lowercase label identifying a numbered joystick axis by
                index; used inline in axis-name displays such as the
                controls-configuration UI. The {number} placeholder is the axis
                index.

                English: "axis {number}"
            """

        def button(self, *, number: str | LangStr) -> LangStr:
            """
            ::

                Short lowercase label identifying a numbered controller button
                by index; used inline in button-name displays such as the
                controls-configuration UI. The {number} placeholder is the
                button index.

                English: "button {number}"
            """

        def controller_connected(self, *, controller: str | LangStr) -> LangStr:
            """
            ::

                Transient screen-message shown when a single game controller
                connects, naming the device (several connecting at once use a
                separate counted message).

                English: "{controller} connected."
            """

        #: ::
        #:
        #:     Transient screen-message shown at app startup when exactly one
        #:     game controller is detected (multiple controllers at startup use
        #:     a separate counted message).
        #:
        #:     English: "1 controller detected."
        controller_detected: LangStr

        def controller_disconnected(
            self, *, controller: str | LangStr
        ) -> LangStr:
            """
            ::

                Transient screen-message shown when a single game controller
                disconnects, naming the device (several disconnecting at once
                use a separate counted message).

                English: "{controller} disconnected."
            """

        def controller_reconnected(
            self, *, controller: str | LangStr
        ) -> LangStr:
            """
            ::

                Transient screen-message shown when a previously-connected game
                controller (e.g. a BombSquad Remote phone client) reconnects,
                naming the device.

                English: "{controller} reconnected."
            """

        def controllers_connected(self, *, count: int) -> LangStr:
            """
            ::

                Transient screen-message shown when multiple game controllers
                connect at the same time (a single controller connecting shows a
                different message naming that controller).

                English: (one) "# controller connected." / (other) "#
                controllers connected."
            """

        def controllers_detected(self, *, count: int) -> LangStr:
            """
            ::

                Transient screen-message shown at app startup when more than one
                game controller is detected at once (a single controller at
                startup uses a separate message).

                English: (one) "# controller detected." / (other) "# controllers
                detected."
            """

        def controllers_disconnected(self, *, count: int) -> LangStr:
            """
            ::

                Transient screen-message shown when multiple game controllers
                disconnect at the same time (a single controller disconnecting
                shows a different message naming that controller).

                English: (one) "# controller disconnected." / (other) "#
                controllers disconnected."
            """

        #: ::
        #:
        #:     Display name for the keyboard input device; shown in input-device
        #:     lists, controls-configuration UI, and messages naming the device.
        #:
        #:     English: "Keyboard"
        keyboard: LangStr

        #: ::
        #:
        #:     Display name for the touch-screen input device; shown in
        #:     input-device lists, controls-configuration UI, and messages
        #:     naming the device.
        #:
        #:     English: "TouchScreen"
        touch_screen: LangStr

        #: ::
        #:
        #:     Warning screen-message shown when the touchscreen joins the game
        #:     while physical controllers are already active (touch joins are
        #:     often accidental then); tells the player how to back out. 'Menu'
        #:     and 'Leave Game' refer to in-game menu items.
        #:
        #:     English: "You have joined with the touchscreen. If this was a
        #:     mistake, tap Menu -> Leave Game with it to back out."
        touch_screen_join_warning: LangStr

        #: ::
        #:
        #:     Confirmation screen-message shown in VR mode when the player
        #:     resets the headset's forward orientation via their controller.
        #:
        #:     English: "VR orientation reset."
        vr_orientation_reset: LangStr

    class StringsNetGroup:
        """
        ::

            Networking error messages shown to the player.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Error screen-message shown to a player whose attempt to join a
        #:     party or server was rejected because the host could not validate
        #:     their account.
        #:
        #:     English: "Your account was rejected. Are you signed in?"
        account_rejected: LangStr

        #: ::
        #:
        #:     Generic error screen-message shown to a player whose attempt to
        #:     join a party or server failed due to an authentication or server
        #:     error (with no more-specific cause available).
        #:
        #:     English: "An error has occurred."
        auth_error: LangStr

        #: ::
        #:
        #:     Error screen-message shown to a player whose attempt to join a
        #:     password-protected party or server was rejected for entering the
        #:     wrong party password.
        #:
        #:     English: "Incorrect password."
        incorrect_password: LangStr

        #: ::
        #:
        #:     Error screen-message shown when the player enters a malformed
        #:     network address trying to connect to a game party.
        #:
        #:     English: "Error: invalid address."
        invalid_address: LangStr

        #: ::
        #:
        #:     Error screen-message shown to a player who attempts to join a
        #:     party or server that requires account authentication while they
        #:     are not signed in to an account.
        #:
        #:     English: "You must sign in to do this."
        must_sign_in: LangStr

        #: ::
        #:
        #:     Error shown when something cannot be reached, most likely because
        #:     there is no internet connection (dialog messages and
        #:     screen-messages).
        #:
        #:     English: "This is currently unavailable (no internet
        #:     connection?)"
        unavailable_no_connection: LangStr

    class StringsReplayGroup:
        """
        ::

            Game-replay playback error messages.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Error screen-message shown when a game replay file can't be read
        #:     (corrupt or truncated).
        #:
        #:     English: "Error reading replay file."
        read_error: LangStr

        #: ::
        #:
        #:     Error screen-message shown when a saved game replay was recorded
        #:     by an incompatible game version and can't be played back.
        #:
        #:     English: "Sorry, this replay was made in a different version of
        #:     the game and can't be used."
        version_error: LangStr

    class StringsSessionGroup:
        """
        ::

            Gameplay-session messages shown by the host: idle-player kick
            notices and similar.

            See source for the full asset list.
        """

        def kick_idle_kicked(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Screen-message shown on the host when a player is removed from
                the game for being idle too long (the kick-idle-players option).

                English: "Kicking {name} for being idle."
            """

        def kick_idle_warning(
            self, *, seconds: int, name: str | LangStr
        ) -> LangStr:
            """
            ::

                Screen-message warning shown on the host shortly before an idle
                player gets kicked (the kick-idle-players option); followed by
                the kick_idle_warning_settings note.

                English: (one) "{name} will be kicked in # second if still
                idle." / (other) "{name} will be kicked in # seconds if still
                idle."
            """

        #: ::
        #:
        #:     Parenthesized note shown right after the kick_idle_warning
        #:     message, pointing at where the kick-idle-players behavior can be
        #:     disabled. 'Settings' and 'Advanced' refer to the in-game settings
        #:     menu sections.
        #:
        #:     English: "(you can turn this off in Settings -> Advanced)"
        kick_idle_warning_settings: LangStr

    class StringsUiGroup:
        """
        ::

            General UI strings: menu-control ownership messages and
            list-navigation hints.

            See source for the full asset list.
        """

        def arrows_to_exit_list(
            self, *, left: str | LangStr, right: str | LangStr
        ) -> LangStr:
            """
            ::

                Lowercase hint shown (with an error sound) when the player hits
                the edge of a UI list; tells them how to move focus out of it.
                The two placeholders are substituted with left/right arrow glyph
                characters.

                English: "press {left} or {right} to exit list"
            """

        #: ::
        #:
        #:     Generic Cancel button label (used by e.g. asset-download progress
        #:     dialogs).
        #:
        #:     English: "Cancel"
        cancel: LangStr

        #: ::
        #:
        #:     Generic Error title used on error dialogs (e.g. the boot-time
        #:     asset-update dialog when a load fails).
        #:
        #:     English: "Error"
        error: LangStr

        def has_menu_control(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Screen-message shown when an input device tries to use a menu
                another device currently controls; names the controlling device.
                A timeout suffix (menu_control_time_out or
                menu_control_will_time_out) is appended after it.

                English: "{name} has menu control."
            """

        def menu_control_time_out(self, *, seconds: int) -> LangStr:
            """
            ::

                Parenthesized suffix appended after the has_menu_control message
                once the controlling device's ownership is close to expiring;
                gives the remaining seconds.

                English: (one) "(times out in # second)" / (other) "(times out
                in # seconds)"
            """

        #: ::
        #:
        #:     Parenthesized suffix appended after the has_menu_control message
        #:     while the controlling device's ownership is not yet close to
        #:     expiring.
        #:
        #:     English: "(will time out if idle)"
        menu_control_will_time_out: LangStr

        #: ::
        #:
        #:     Generic label for a button acknowledging/dismissing a message
        #:     (used by e.g. asset-update error dialogs).
        #:
        #:     English: "OK"
        ok: LangStr

        #: ::
        #:
        #:     Generic label for a button that retries a failed operation (used
        #:     by e.g. the boot-time asset-update dialog).
        #:
        #:     English: "Retry"
        retry: LangStr

        #: ::
        #:
        #:     Generic Sign In label used for dialog titles and buttons (e.g.
        #:     the boot-time asset gate's browser sign-in dialog).
        #:
        #:     English: "Sign In"
        sign_in: LangStr

        #: ::
        #:
        #:     Generic title for progress dialogs applying updates: asset
        #:     downloads/builds at boot, locale switches, pre-game package
        #:     fetches.
        #:
        #:     English: "Updating…"
        updating: LangStr

    class StringsGroup:
        """
        ::

            New-format engine strings needed early or accessed from the C++
            layer via the builtin-strings API (see ballistica-internal
            strings-asset-migration decision D22).

            See source for the full asset list.
        """

        assets: StringsAssetsGroup
        audio: StringsAudioGroup
        input: StringsInputGroup
        net: StringsNetGroup
        replay: StringsReplayGroup
        session: StringsSessionGroup
        ui: StringsUiGroup

    #: The ``strings`` group - 47 strings (``assets``, ``audio``, ``input``,
    #: ``net``, ``replay``, and 42 more). Full list in source.
    strings: StringsGroup

_TREE = {
    'strings': {
        'assets': {
            'access_denied_guidance': ('detail',),
            'authenticating': (),
            'building_assets': ('count', 'package'),
            'client_too_old': (),
            'content_error_guidance': ('detail',),
            'downloading_assets': ('count',),
            'load_error': (),
            'preparing_build': ('package',),
            'sign_in_failed': (),
            'sign_in_needed_browser': ('address',),
            'sign_in_needed_other_device': ('address',),
            'signing_in': (),
        },
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
        'net': {
            'account_rejected': (),
            'auth_error': (),
            'incorrect_password': (),
            'invalid_address': (),
            'must_sign_in': (),
            'unavailable_no_connection': (),
        },
        'replay': {'read_error': (), 'version_error': ()},
        'session': {
            'kick_idle_kicked': ('name',),
            'kick_idle_warning': ('seconds', 'name'),
            'kick_idle_warning_settings': (),
        },
        'ui': {
            'arrows_to_exit_list': ('left', 'right'),
            'cancel': (),
            'error': (),
            'has_menu_control': ('name',),
            'menu_control_time_out': ('seconds',),
            'menu_control_will_time_out': (),
            'ok': (),
            'retry': (),
            'sign_in': (),
            'updating': (),
        },
    }
}


if not TYPE_CHECKING:
    strings = LangStrDir(__asset_package__, _TREE['strings'], 'strings')
