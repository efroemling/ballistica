# Released under the MIT License. See LICENSE for details.
#
# Auto-generated; do not edit by hand.
"""Asset-package wrapper for ``a-0.babuiltinassets.260831h`` (bauiv1).

Bare minimum assets always bundled with the engine.

These are loaded at launch and always available in the C++ layer.
"""

# ba_meta require api 9
# ba_meta require asset-package a-0.babuiltinassets.260831h

# pylint: disable=useless-suppression
# pylint: disable=too-many-lines
# pylint: disable=too-few-public-methods, disallowed-name

from typing import TYPE_CHECKING

from bauiv1._assetref import AssetGroup

from babase import LangStrDir

_ASSET_PACKAGE = 'a-0.babuiltinassets.260831h'

if TYPE_CHECKING:
    import datetime
    from bauiv1._assetref import MeshHandle, SoundHandle, TextureHandle
    from babase import LangStr

    class AudioGroup:
        """
        ::

            Sounds needed during engine bootstrap and early UI (clicks, errors,
            and other always-available effects).

            See source for the full asset list.
        """

        blank: SoundHandle
        blip: SoundHandle
        cash_register: SoundHandle
        click01: SoundHandle
        ding: SoundHandle
        error: SoundHandle
        gun_cocking: SoundHandle
        powerdown01: SoundHandle
        tap: SoundHandle

    class MeshesGroup:
        """
        ::

            Meshes needed during engine bootstrap and early UI.

            See source for the full asset list.
        """

        box: MeshHandle
        image1x1: MeshHandle
        overlay_guide: MeshHandle
        vr_fade: MeshHandle
        vr_overlay: MeshHandle

    class StringsAccountGroup:
        """
        ::

            Account and sign-in vocabulary: status, error, and requirement
            messages about the player account.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Error screen-message shown to a player who attempts to join a
        #:     party or server that requires account authentication while they
        #:     are not signed in to an account.
        #:
        #:     English: "You must sign in to do this."
        must_sign_in: LangStr

        def not_using_account(self, *, service: str | LangStr) -> LangStr:
            """
            ::

                Notice that a platform account is being ignored.

                English: "Note: Ignoring that {service} account. Go to 'Account
                -> Sign in' if you want to use it."
            """

        #: ::
        #:
        #:     Error message shown when signing in fails.
        #:
        #:     English: "Error signing in."
        sign_in_error: LangStr

        #: ::
        #:
        #:     Notice that the account is being updated.
        #:
        #:     English: "Updating your account..."
        updating_account: LangStr

        def you_got_item(self, *, item: str | LangStr) -> LangStr:
            """
            ::

                Screen-message acknowledging the player received a
                purchased/awarded item; the placeholder is the item name (may be
                raw text or a nested translated name).

                English: "You got a {item}!"
            """

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
        #:     Screen message shown when a resolve finally lands full asset
        #:     quality after previously showing reduced-quality versions. Paired
        #:     with requested_quality_assets_building.
        #:
        #:     English: "All assets are now full quality."
        all_assets_requested_quality: LangStr

        #: ::
        #:
        #:     Status line in the boot-time asset dialog while waiting for
        #:     account sign-in so restricted assets can load.
        #:
        #:     English: "Authenticating…"
        authenticating: LangStr

        def building_assets(self, *, count: int) -> LangStr:
            """
            ::

                Progress-dialog line shown while the server builds assets;
                updates live as the remaining count drops. Spans every package
                being built, so it names no package.

                English: (one) "Building assets (# remaining)…" / (other)
                "Building assets (# remaining)…"
            """

        #: ::
        #:
        #:     Progress-dialog line shown once asset builds have started but
        #:     before the total step count is known (some packages have not
        #:     reported yet). Replaced by the counted line once it is.
        #:
        #:     English: "Building assets…"
        building_assets_no_count: LangStr

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

                English: "{detail} Fix the file in the source Workspace and try
                again."
            """

        def corrupt_file(self, *, email: str | LangStr) -> LangStr:
            """
            ::

                Error screen-message shown when a corrupt game data file (e.g.
                an unreadable audio file) is detected; the placeholder is the
                support email address.

                English: "Corrupt file(s) detected. Please try re-installing, or
                email {email}"
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

        #: ::
        #:
        #:     Progress-dialog line shown while server-side asset builds are
        #:     being prepared, before per-step progress is known.
        #:
        #:     English: "Preparing to build assets…"
        preparing_build: LangStr

        #: ::
        #:
        #:     Screen message shown after a resolve that had to serve
        #:     lower-quality textures because the requested quality was still
        #:     being built. Paired with all_assets_requested_quality, which
        #:     announces the recovery.
        #:
        #:     English: "Assets are still building; some may appear with reduced
        #:     quality."
        requested_quality_assets_building: LangStr

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

        #: ::
        #:
        #:     Notice that a controller works only in menus.
        #:
        #:     English: "This controller can not be used to play; only to
        #:     navigate menus."
        controller_menus_only: LangStr

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

        def unsupported_controller(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Notice that a controller is not supported.

                English: "Sorry, the {name} controller is not supported."
            """

        #: ::
        #:
        #:     Confirmation screen-message shown in VR mode when the player
        #:     resets the headset's forward orientation via their controller.
        #:
        #:     English: "VR orientation reset."
        vr_orientation_reset: LangStr

        #: ::
        #:
        #:     Explanation of the VR orientation reset on Cardboard.
        #:
        #:     English: "Use this to reset the VR orientation. To play, you'll
        #:     need an external controller."
        vr_orientation_reset_cardboard: LangStr

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

        def connected_to_game(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Screen-message after successfully joining a named hosted game;
                the placeholder is the game/party name (already quoted in the
                English form).

                English: "Joined '{name}'"
            """

        def connected_to_party(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Screen-message after successfully joining another player's
                party; the placeholder is that player's display name.

                English: "Joined {name}'s party!"
            """

        #: ::
        #:
        #:     Progress screen-message shown while attempting to connect to a
        #:     multiplayer party.
        #:
        #:     English: "Connecting..."
        connecting: LangStr

        #: ::
        #:
        #:     Notice that connecting to a server failed.
        #:
        #:     English: "Connection failed."
        connection_failed: LangStr

        #: ::
        #:
        #:     Screen-message when connecting fails because the target host is
        #:     itself in another party.
        #:
        #:     English: "Connection failed; host is in another party."
        connection_failed_host_in_other_party: LangStr

        #: ::
        #:
        #:     Screen-message when connecting fails because the party has no
        #:     free slots.
        #:
        #:     English: "Connection failed; the party is full."
        connection_failed_party_full: LangStr

        #: ::
        #:
        #:     Screen-message when connecting fails because the host runs a
        #:     different game version.
        #:
        #:     English: "Connection failed; host is running a different version
        #:     of the game. Make sure you are both up-to-date and try again."
        connection_failed_version_mismatch: LangStr

        #: ::
        #:
        #:     Generic screen-message when a host refuses the connection for an
        #:     unspecified reason.
        #:
        #:     English: "Connection rejected."
        connection_rejected: LangStr

        def device_time_incorrect(self, *, hours: str | LangStr) -> LangStr:
            """
            ::

                Warning shown when the device clock differs substantially from
                real-world time; the placeholder is how many hours off it is.

                English: "Your device's time is incorrect by {hours} hours. This
                is likely to cause problems. Please check your time and
                time-zone settings."
            """

        #: ::
        #:
        #:     Screen-message when connecting fails because the host runs a
        #:     NEWER game version (so updating locally will fix it).
        #:
        #:     English: "Host is running a newer version. Update your game and
        #:     try again."
        incompatible_newer_version_host: LangStr

        #: ::
        #:
        #:     Screen-message when connecting fails because the host runs a
        #:     different game version (direction unknown).
        #:
        #:     English: "Host is running a different version of the game. Make
        #:     sure you are both up-to-date and try again."
        incompatible_version_host: LangStr

        def incompatible_version_player(
            self, *, name: str | LangStr
        ) -> LangStr:
            """
            ::

                Screen-message when a joining player is refused because their
                game version differs from the host; the placeholder is their
                display name.

                English: "{name} is running a different version of the game.
                Make sure you are both up-to-date and try again."
            """

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

        def left_game(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Screen-message after leaving a named hosted game; the
                placeholder is the game/party name (already quoted in the
                English form).

                English: "Left '{name}'."
            """

        def left_party(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Screen-message after leaving another player's party; the
                placeholder is that player's display name.

                English: "Left {name}'s party."
            """

        def player_joined_party(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Screen-message when another player joins the party you are in;
                the placeholder is their display name.

                English: "{name} joined the party!"
            """

        def player_left_party(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Screen-message when another player leaves the party you are in;
                the placeholder is their display name.

                English: "{name} left the party."
            """

        #: ::
        #:
        #:     Screen-message shown when the client cannot establish its secure
        #:     connection to the cloud.
        #:
        #:     English: "Unable to establish secure cloud connection; network
        #:     functionality may fail."
        secure_connection_failed: LangStr

        #: ::
        #:
        #:     Screen-message when connecting to game servers is refused because
        #:     this app version is too old for them.
        #:
        #:     English: "Server functionality is no longer supported in this
        #:     version of the game; Please update to a newer version."
        server_unsupported: LangStr

        #: ::
        #:
        #:     Error shown when something cannot be reached, most likely because
        #:     there is no internet connection (dialog messages and
        #:     screen-messages).
        #:
        #:     English: "This is currently unavailable (no internet
        #:     connection?)"
        unavailable_no_connection: LangStr

    class StringsPluginsGroup:
        """
        ::

            Messages about user-installed plugins being detected, removed, or
            failing to load.

            See source for the full asset list.
        """

        def class_load_error(
            self, *, plugin: str | LangStr, error: str | LangStr
        ) -> LangStr:
            """
            ::

                Error message for a plugin class that failed to load.

                English: "Error loading plugin class '{plugin}': {error}"
            """

        #: ::
        #:
        #:     Notice that new plugins were found.
        #:
        #:     English: "New plugin(s) detected. Restart to activate them, or
        #:     configure them in settings."
        detected: LangStr

        def init_error(
            self, *, plugin: str | LangStr, error: str | LangStr
        ) -> LangStr:
            """
            ::

                Error message for a plugin that failed to initialize.

                English: "Error initializing plugin {plugin}: {error}"
            """

        def removed(self, *, count: int) -> LangStr:
            """
            ::

                Notice that previously-present plugins are gone.

                English: (one) "# plugin no longer found." / (other) "# plugins
                no longer found."
            """

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

    class StringsScriptsGroup:
        """
        ::

            Messages about scanning user script modules and reporting ones that
            need updating for the current script API.

            See source for the full asset list.
        """

        def module_needs_update(
            self, *, path: str | LangStr, api: str | LangStr
        ) -> LangStr:
            """
            ::

                Notice that one script module is out of date.

                English: "The module at {path} must be updated for API version
                {api}."
            """

        def modules_need_update(
            self, *, path: str | LangStr, count: int, api: str | LangStr
        ) -> LangStr:
            """
            ::

                Notice that several script modules are out of date.

                English: (one) "{path} and # other module must be updated for
                API {api}" / (other) "{path} and # other modules must be updated
                for API {api}"
            """

        #: ::
        #:
        #:     Notice that errors occurred scanning scripts.
        #:
        #:     English: "Error(s) scanning scripts. See log for details."
        scan_error: LangStr

    class StringsSessionGroup:
        """
        ::

            Gameplay-session messages shown by the host: idle-player kick
            notices and similar.

            See source for the full asset list.
        """

        def chat_blocked(self, *, seconds: int, name: str | LangStr) -> LangStr:
            """
            ::

                Screen-message when a player is temporarily blocked from
                chatting; placeholders are their display name and the block
                duration in seconds.

                English: (one) "{name} is chat-blocked for # second." / (other)
                "{name} is chat-blocked for # seconds."
            """

        def join_cooldown(self, *, seconds: int) -> LangStr:
            """
            ::

                Screen-message telling a recently-departed player how long until
                they may rejoin the game session.

                English: (one) "You can join in # second." / (other) "You can
                join in # seconds."
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

        def kick_occurred(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Screen-message when a player is kicked from the party after a
                successful vote; the placeholder is their display name.

                English: "{name} was kicked."
            """

        def kick_question(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Prompt asking the party whether a player should be kicked; the
                placeholder is their display name.

                English: "Kick {name}?"
            """

        #: ::
        #:
        #:     Error screen-message when a player tries to start a kick vote
        #:     against a server admin.
        #:
        #:     English: "Admins can't be kicked."
        kick_vote_cant_kick_admins: LangStr

        #: ::
        #:
        #:     Error screen-message when a player tries to start a kick vote
        #:     against themselves.
        #:
        #:     English: "You can't kick yourself."
        kick_vote_cant_kick_self: LangStr

        #: ::
        #:
        #:     Screen-message when a kick vote ends without enough yes votes.
        #:
        #:     English: "Kick-vote failed."
        kick_vote_failed: LangStr

        #: ::
        #:
        #:     Error screen-message when there are too few players present for a
        #:     kick vote to be meaningful.
        #:
        #:     English: "Not enough players for a vote."
        kick_vote_not_enough_players: LangStr

        def kick_vote_started(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Screen-message announcing that a kick vote has begun against a
                player; the placeholder is their display name.

                English: "A kick vote has been started for {name}."
            """

        def kick_votes_needed(self, *, count: int) -> LangStr:
            """
            ::

                Screen-message showing how many more yes votes a kick vote needs
                to pass.

                English: (one) "# vote needed" / (other) "# votes needed"
            """

        #: ::
        #:
        #:     Error screen-message when kick voting is turned off on this
        #:     server.
        #:
        #:     English: "Kick voting is disabled."
        kick_voting_disabled: LangStr

        def kick_with_chat(
            self, *, yes: str | LangStr, no: str | LangStr
        ) -> LangStr:
            """
            ::

                Instructions for voting via chat; the placeholders are the exact
                text to type into chat for yes and for no (e.g. "1" and "2").

                English: "Type {yes} in chat for yes and {no} for no."
            """

        #: ::
        #:
        #:     Screen-message when a client tries to do something while the host
        #:     is still loading.
        #:
        #:     English: "Loading; try again in a moment..."
        loading_try_again: LangStr

        def vote_delay(self, *, seconds: int) -> LangStr:
            """
            ::

                Error screen-message telling a player how long until they may
                start another vote.

                English: (one) "You can't start another vote for # second." /
                (other) "You can't start another vote for # seconds."
            """

        #: ::
        #:
        #:     Error screen-message when a player tries to start a vote while
        #:     another vote is still running.
        #:
        #:     English: "A vote is already in progress."
        vote_in_progress: LangStr

        #: ::
        #:
        #:     Error screen-message when a player tries to vote twice in the
        #:     same vote.
        #:
        #:     English: "You already voted"
        voted_already: LangStr

    class StringsStoreGroup:
        """
        ::

            In-app-purchase and store transaction messages: purchase failures,
            restores, and availability notices.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Notice that Google Play purchases are unavailable.
        #:
        #:     English: "Google Play purchases are not available. You may need
        #:     to update your store app."
        google_play_purchases_unavailable: LangStr

        #: ::
        #:
        #:     Notice that Google Play Services is unavailable.
        #:
        #:     English: "Google Play Services is not available. Some app
        #:     functionality may be disabled."
        google_play_services_unavailable: LangStr

        #: ::
        #:
        #:     Notice that this item is already being purchased.
        #:
        #:     English: "A purchase of this item is already in progress."
        purchase_already_in_progress: LangStr

        def purchase_not_valid(self, *, email: str | LangStr) -> LangStr:
            """
            ::

                Error message that a purchase was not valid.

                English: "Purchase not valid. Contact {email} if this is an
                error."
            """

        #: ::
        #:
        #:     Confirmation that past purchases were restored.
        #:
        #:     English: "Purchases restored."
        purchases_restored: LangStr

        #: ::
        #:
        #:     Status shown while a purchase is being processed.
        #:
        #:     English: "Purchasing..."
        purchasing: LangStr

        #: ::
        #:
        #:     Limited-time offer to remove ads via a token pack.
        #:
        #:     English: "LIMITED TIME OFFER: PURCHASE ANY TOKEN PACK TO REMOVE
        #:     IN-GAME ADS."
        remove_ads_token_offer: LangStr

        #: ::
        #:
        #:     Status shown while a free (zero-price) item is being requested;
        #:     the counterpart of the purchasing message.
        #:
        #:     English: "Requesting..."
        requesting: LangStr

        #: ::
        #:
        #:     Notice that a transaction is already underway.
        #:
        #:     English: "A transaction is in progress; please try again in a
        #:     moment."
        transaction_in_progress: LangStr

        #: ::
        #:
        #:     Notice that a store item is not available.
        #:
        #:     English: "Sorry, this is not available."
        unavailable: LangStr

        #: ::
        #:
        #:     Notice that something is unavailable for now.
        #:
        #:     English: "This is currently unavailable; please try again later."
        unavailable_temporarily: LangStr

    class StringsTimeGroup:
        """
        ::

            Compact unit suffixes and glue for formatted time values (the
            hours/minutes/seconds pieces babase.timestring assembles).

            See source for the full asset list.
        """

        def duration_value(
            self,
            *,
            t: datetime.timedelta | datetime.datetime,
            now: datetime.datetime | None = None,
        ) -> LangStr:
            """
            ::

                A bare length of time such as "1h 23m", shown by itself as a
                plain value. Doubles as the string that keeps the duration
                formatter components embedded in this package: engine-level
                displays (the timedisplay node, the toolbar chest countdowns)
                read their unit words from those embedded components, so this
                entry must always exist here.

                English: "{t}"
            """

        def suffix_hours(self, *, count: str | LangStr) -> LangStr:
            """
            ::

                Compact hours suffix used in formatted time values.

                English: "{count}h"
            """

        def suffix_minutes(self, *, count: str | LangStr) -> LangStr:
            """
            ::

                Compact minutes suffix used in formatted time values.

                English: "{count}m"
            """

        def suffix_seconds(self, *, count: str | LangStr) -> LangStr:
            """
            ::

                Compact seconds suffix used in formatted time values.

                English: "{count}s"
            """

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
        #:     Notice that the clipboard is unavailable in this build.
        #:
        #:     English: "Clipboard not supported on this build."
        clipboard_not_supported: LangStr

        #: ::
        #:
        #:     Confirmation that text was copied to the clipboard.
        #:
        #:     English: "Copied to clipboard."
        copied_to_clipboard: LangStr

        #: ::
        #:
        #:     Generic Error title used on error dialogs (e.g. the boot-time
        #:     asset-update dialog when a load fails).
        #:
        #:     English: "Error"
        error: LangStr

        #: ::
        #:
        #:     Name label for the Apple Game Center service.
        #:
        #:     English: "Game Center"
        game_center: LangStr

        #: ::
        #:
        #:     Name label for the Google Play service.
        #:
        #:     English: "Google Play"
        google_play: LangStr

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
        #:     Label on an unopenable-yet treasure chest slot in the root UI
        #:     inviting the player to open it once its timer completes. Replaces
        #:     the legacy openMeText resource.
        #:
        #:     English: "Open Me!"
        open_me: LangStr

        #: ::
        #:
        #:     Name label for the remote-control companion app.
        #:
        #:     English: "BombSquad Remote"
        remote_app_name: LangStr

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

        def spaced_pair(
            self, *, first: str | LangStr, second: str | LangStr
        ) -> LangStr:
            """
            ::

                Pure-formatting template joining two labels with a space;
                substitution-only.

                English: "{first} {second}"
            """

        #: ::
        #:
        #:     Notice that storage access permission is required.
        #:
        #:     English: "This requires storage access"
        storage_permission_needed: LangStr

        #: ::
        #:
        #:     Confirmation label that an operation succeeded.
        #:
        #:     English: "Success!"
        success: LangStr

        #: ::
        #:
        #:     Generic screen-message for a failure with no more specific
        #:     explanation available.
        #:
        #:     English: "Unknown error"
        unknown_error: LangStr

        #: ::
        #:
        #:     Gentle non-urgent screen-message notice, shown once shortly after
        #:     connectivity comes up, telling the player that a newer version of
        #:     the app is available to download.
        #:
        #:     English: "A newer version of this app is available."
        update_available: LangStr

        #: ::
        #:
        #:     Generic title for progress dialogs applying updates: asset
        #:     downloads/builds at boot, locale switches, pre-game package
        #:     fetches.
        #:
        #:     English: "Updating…"
        updating: LangStr

    class StringsWorkspaceGroup:
        """
        ::

            Messages about syncing and activating account workspaces.

            See source for the full asset list.
        """

        def activated(self, *, thing: str | LangStr) -> LangStr:
            """
            ::

                Confirmation that a workspace was activated.

                English: "Workspace {thing} activated."
            """

        def sync_error(self, *, workspace: str | LangStr) -> LangStr:
            """
            ::

                Error message that a workspace failed to sync.

                English: "Error syncing Workspace {workspace}. See log for
                details."
            """

        def sync_reuse(self, *, workspace: str | LangStr) -> LangStr:
            """
            ::

                Notice that a previously synced workspace is being reused.

                English: "Can't sync Workspace '{workspace}'. Reusing previously
                synced version."
            """

    class StringsGroup:
        """
        ::

            New-format engine strings needed early or accessed from the C++
            layer via the builtin-strings API (see ballistica-internal
            strings-asset-migration decision D22).

            See source for the full asset list.
        """

        account: StringsAccountGroup
        assets: StringsAssetsGroup
        audio: StringsAudioGroup
        input: StringsInputGroup
        net: StringsNetGroup
        plugins: StringsPluginsGroup
        replay: StringsReplayGroup
        scripts: StringsScriptsGroup
        session: StringsSessionGroup
        store: StringsStoreGroup
        time: StringsTimeGroup
        ui: StringsUiGroup
        workspace: StringsWorkspaceGroup

    class TexturesGroup:
        """
        ::

            Textures needed during engine bootstrap and early UI, including the
            reflection cube-maps.

            See source for the full asset list.
        """

        black: TextureHandle
        circle: TextureHandle
        circle_shadow: TextureHandle
        cursor: TextureHandle
        font_big: TextureHandle
        font_extras: TextureHandle
        font_extras2: TextureHandle
        font_extras3: TextureHandle
        font_extras4: TextureHandle
        font_extras5: TextureHandle
        font_small0: TextureHandle
        font_small1: TextureHandle
        font_small2: TextureHandle
        font_small3: TextureHandle
        font_small4: TextureHandle
        font_small5: TextureHandle
        font_small6: TextureHandle
        font_small7: TextureHandle
        shadow: TextureHandle
        shadow_sharp: TextureHandle
        soft_rect: TextureHandle
        soft_rect2: TextureHandle
        soft_rect_vertical: TextureHandle
        white: TextureHandle

    #: The ``audio`` group - 9 assets (``blank``, ``blip``, ``cash_register``,
    #: ``click01``, ``ding``, and 4 more). Full list in source.
    audio: AudioGroup

    #: The ``meshes`` group - 5 assets (``box``, ``image1x1``,
    #: ``overlay_guide``, ``vr_fade``, ``vr_overlay``). Full list in source.
    meshes: MeshesGroup

    #: The ``strings`` group - 128 strings (``account``, ``assets``, ``audio``,
    #: ``input``, ``net``, and 123 more). Full list in source.
    strings: StringsGroup

    #: The ``textures`` group - 24 assets (``black``, ``circle``,
    #: ``circle_shadow``, ``cursor``, ``font_big``, and 19 more). Full list in
    #: source.
    textures: TexturesGroup

_TREE = {
    'audio': {
        'blank': 's',
        'blip': 's',
        'cash_register': 's',
        'click01': 's',
        'ding': 's',
        'error': 's',
        'gun_cocking': 's',
        'powerdown01': 's',
        'tap': 's',
    },
    'meshes': {
        'box': 'm',
        'image1x1': 'm',
        'overlay_guide': 'm',
        'vr_fade': 'm',
        'vr_overlay': 'm',
    },
    'strings': {
        'account': {
            'must_sign_in': (),
            'not_using_account': ('service',),
            'sign_in_error': (),
            'updating_account': (),
            'you_got_item': ('item',),
        },
        'assets': {
            'access_denied_guidance': ('detail',),
            'all_assets_requested_quality': (),
            'authenticating': (),
            'building_assets': ('count',),
            'building_assets_no_count': (),
            'client_too_old': (),
            'content_error_guidance': ('detail',),
            'corrupt_file': ('email',),
            'downloading_assets': ('count',),
            'load_error': (),
            'preparing_build': (),
            'requested_quality_assets_building': (),
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
            'controller_menus_only': (),
            'controller_reconnected': ('controller',),
            'controllers_connected': ('count',),
            'controllers_detected': ('count',),
            'controllers_disconnected': ('count',),
            'keyboard': (),
            'touch_screen': (),
            'touch_screen_join_warning': (),
            'unsupported_controller': ('name',),
            'vr_orientation_reset': (),
            'vr_orientation_reset_cardboard': (),
        },
        'net': {
            'account_rejected': (),
            'auth_error': (),
            'connected_to_game': ('name',),
            'connected_to_party': ('name',),
            'connecting': (),
            'connection_failed': (),
            'connection_failed_host_in_other_party': (),
            'connection_failed_party_full': (),
            'connection_failed_version_mismatch': (),
            'connection_rejected': (),
            'device_time_incorrect': ('hours',),
            'incompatible_newer_version_host': (),
            'incompatible_version_host': (),
            'incompatible_version_player': ('name',),
            'incorrect_password': (),
            'invalid_address': (),
            'left_game': ('name',),
            'left_party': ('name',),
            'player_joined_party': ('name',),
            'player_left_party': ('name',),
            'secure_connection_failed': (),
            'server_unsupported': (),
            'unavailable_no_connection': (),
        },
        'plugins': {
            'class_load_error': ('plugin', 'error'),
            'detected': (),
            'init_error': ('plugin', 'error'),
            'removed': ('count',),
        },
        'replay': {'read_error': (), 'version_error': ()},
        'scripts': {
            'module_needs_update': ('path', 'api'),
            'modules_need_update': ('path', 'count', 'api'),
            'scan_error': (),
        },
        'session': {
            'chat_blocked': ('seconds', 'name'),
            'join_cooldown': ('seconds',),
            'kick_idle_kicked': ('name',),
            'kick_idle_warning': ('seconds', 'name'),
            'kick_idle_warning_settings': (),
            'kick_occurred': ('name',),
            'kick_question': ('name',),
            'kick_vote_cant_kick_admins': (),
            'kick_vote_cant_kick_self': (),
            'kick_vote_failed': (),
            'kick_vote_not_enough_players': (),
            'kick_vote_started': ('name',),
            'kick_votes_needed': ('count',),
            'kick_voting_disabled': (),
            'kick_with_chat': ('yes', 'no'),
            'loading_try_again': (),
            'vote_delay': ('seconds',),
            'vote_in_progress': (),
            'voted_already': (),
        },
        'store': {
            'google_play_purchases_unavailable': (),
            'google_play_services_unavailable': (),
            'purchase_already_in_progress': (),
            'purchase_not_valid': ('email',),
            'purchases_restored': (),
            'purchasing': (),
            'remove_ads_token_offer': (),
            'requesting': (),
            'transaction_in_progress': (),
            'unavailable': (),
            'unavailable_temporarily': (),
        },
        'time': {
            'duration_value': ('t',),
            'suffix_hours': ('count',),
            'suffix_minutes': ('count',),
            'suffix_seconds': ('count',),
        },
        'ui': {
            'arrows_to_exit_list': ('left', 'right'),
            'cancel': (),
            'clipboard_not_supported': (),
            'copied_to_clipboard': (),
            'error': (),
            'game_center': (),
            'google_play': (),
            'has_menu_control': ('name',),
            'menu_control_time_out': ('seconds',),
            'menu_control_will_time_out': (),
            'ok': (),
            'open_me': (),
            'remote_app_name': (),
            'retry': (),
            'sign_in': (),
            'spaced_pair': ('first', 'second'),
            'storage_permission_needed': (),
            'success': (),
            'unknown_error': (),
            'update_available': (),
            'updating': (),
        },
        'workspace': {
            'activated': ('thing',),
            'sync_error': ('workspace',),
            'sync_reuse': ('workspace',),
        },
    },
    'textures': {
        'black': 't',
        'circle': 't',
        'circle_shadow': 't',
        'cursor': 't',
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
        'shadow': 't',
        'shadow_sharp': 't',
        'soft_rect': 't',
        'soft_rect2': 't',
        'soft_rect_vertical': 't',
        'white': 't',
    },
}
_DISPLAY_KINDS = {'strings/time/duration_value': {'t': 'millis'}}


if not TYPE_CHECKING:
    audio = AssetGroup(_ASSET_PACKAGE, _TREE['audio'], 'audio')
    meshes = AssetGroup(_ASSET_PACKAGE, _TREE['meshes'], 'meshes')
    strings = LangStrDir(
        _ASSET_PACKAGE,
        _TREE['strings'],
        'strings',
        display_kinds=_DISPLAY_KINDS,
    )
    textures = AssetGroup(_ASSET_PACKAGE, _TREE['textures'], 'textures')
