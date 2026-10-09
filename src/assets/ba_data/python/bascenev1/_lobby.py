# Released under the MIT License. See LICENSE for details.
#
"""Implements lobby system for gathering before games, char select, etc."""

# pylint: disable=too-many-lines

import json
import logging
import weakref
from dataclasses import dataclass
from typing import TYPE_CHECKING

from efro.dataclassio import dataclass_to_json, dataclass_from_json
import bacommon.depiction as bdep
import babase
import _bascenev1
from bascenev1 import _assetref
from bascenev1._character import name_text, split_character
from bascenev1._profile import get_player_profile_colors
from bascenev1._gameutils import animate, animate_array

if TYPE_CHECKING:
    from typing import Any, Sequence

    import bascenev1

MAX_QUICK_CHANGE_COUNT = 30
QUICK_CHANGE_INTERVAL = 0.05
QUICK_CHANGE_RESET_INTERVAL = 1.0

# A chooser's name box (its left edge sits just right of its icon): room
# for the name and its '(ready)' together, which shrink as one to fit
# (each viewer measures them in its own fonts). 40 tall draws a basic
# name's text at the size the old name text node used; 180 wide stays
# clear of the next team's column (350 over).
_NAME_BOX_WIDTH = 180.0
_NAME_BOX_HEIGHT = 40.0
_NAME_BOX_LEFT = -100.0


# Hmm should we move this to actors?..
class JoinInfo:
    """Display useful info for joiners."""

    def __init__(self, lobby: bascenev1.Lobby):
        # Safe up-call: bascenev1 is fully imported by the time
        # this runs; the cycle pylint sees is structural only.
        # pylint: disable-next=cyclic-import
        from bascenev1 import _commonassets, _classicassets
        from bascenev1._nodeactor import NodeActor

        self._state = 0
        self._press_to_punch: str | babase.LangStr = babase.charstr(
            babase.SpecialChar.LEFT_BUTTON
        )
        self._press_to_bomb: str | babase.LangStr = babase.charstr(
            babase.SpecialChar.RIGHT_BUTTON
        )
        self._joinmsg: babase.LangStr = (
            _classicassets.strings.lobby.press_any_button_to_join
        )
        can_switch_teams = len(lobby.sessionteams) > 1

        # If we have a keyboard, grab keys for punch and pickup.
        # FIXME: This of course is only correct on the local device;
        #  Should change this for net games.
        keyboard = _bascenev1.getinputdevice('Keyboard', '#1', doraise=False)
        if keyboard is not None:
            self._update_for_keyboard(keyboard)

        flatness = 1.0 if babase.app.env.vr else 0.0
        self._text = NodeActor(
            _bascenev1.newnode(
                'text',
                attrs={
                    'position': (0, -40),
                    'h_attach': 'center',
                    'v_attach': 'top',
                    'h_align': 'center',
                    'color': (0.7, 0.7, 0.95, 1.0),
                    'flatness': flatness,
                    'text': self._joinmsg,
                },
            )
        )

        variant = babase.app.env.variant
        vart = type(variant)

        if variant is vart.DEMO or variant is vart.ARCADE:
            self._messages = [self._joinmsg]
        else:
            msg1 = _classicassets.strings.lobby.press_to_select_profile(
                buttons=(
                    babase.charstr(babase.SpecialChar.UP_ARROW)
                    + ' '
                    + babase.charstr(babase.SpecialChar.DOWN_ARROW)
                )
            )
            msg2 = _classicassets.strings.lobby.press_to_override_character(
                buttons=_classicassets.strings.lobby.bomb
            )
            msg3 = _commonassets.strings.compose.angle_button_suffix(
                main=msg2, button=self._press_to_bomb
            )
            self._messages = (
                (
                    [
                        _classicassets.strings.lobby.press_to_select_team(
                            buttons=(
                                babase.charstr(babase.SpecialChar.LEFT_ARROW)
                                + ' '
                                + babase.charstr(babase.SpecialChar.RIGHT_ARROW)
                            )
                        )
                    ]
                    if can_switch_teams
                    else []
                )
                + [msg1]
                + [msg3]
                + [self._joinmsg]
            )

        self._timer = _bascenev1.Timer(
            4.0, babase.WeakCallStrict(self._update), repeat=True
        )

    def _update_for_keyboard(self, keyboard: bascenev1.InputDevice) -> None:
        # Safe up-call: bascenev1 is fully imported by the time
        # this runs; the cycle pylint sees is structural only.
        # pylint: disable-next=cyclic-import
        from bascenev1 import _commonassets, _classicassets

        classic = babase.app.classic
        assert classic is not None

        compose = _commonassets.strings.compose
        punch_key = keyboard.get_button_name(
            classic.get_input_device_mapped_value(keyboard, 'buttonPunch')
        )
        self._press_to_punch = compose.or_join(
            a=compose.quoted(text=punch_key), b=self._press_to_punch
        )
        bomb_key = keyboard.get_button_name(
            classic.get_input_device_mapped_value(keyboard, 'buttonBomb')
        )
        self._press_to_bomb = compose.or_join(
            a=compose.quoted(text=bomb_key), b=self._press_to_bomb
        )
        self._joinmsg = _commonassets.strings.compose.angle_button_suffix(
            main=_classicassets.strings.lobby.press_punch_to_join,
            button=self._press_to_punch,
        )

    def _update(self) -> None:
        assert self._text.node
        self._text.node.text = self._messages[self._state]
        self._state = (self._state + 1) % len(self._messages)


@dataclass
class PlayerReadyMessage:
    """Tells an object a player has been selected from the given chooser."""

    chooser: bascenev1.Chooser


@dataclass
class ChangeMessage:
    """Tells an object that a selection is being changed."""

    what: str
    value: int


class Chooser:
    """A character/team selector for a player."""

    # Class-level default so choosers built by older user mods (a
    # subclass or copy with its own __init__ that predates this
    # attribute) still work with our methods instead of failing every
    # join with an AttributeError.
    _cloud_look_name: str | None = None

    def __del__(self) -> None:
        # Just kill off our base node; the rest should go down with it.
        if self._text_node:
            self._text_node.delete()

    def __init__(
        self,
        vpos: float,
        sessionplayer: bascenev1.SessionPlayer,
        lobby: 'Lobby',
    ) -> None:
        # Safe up-call: bascenev1 is fully imported by the time
        # this runs; the cycle pylint sees is structural only.
        # pylint: disable-next=cyclic-import
        from bascenev1 import (
            _commonassets,
            _builtinassets,
            _classicassets,
            _uiv1assets,
            _classiccatalogassets,
        )

        self._deek_sound = _classicassets.audio.deek.get()
        self._click_sound = _builtinassets.audio.click01.get()
        self._punchsound = _classicassets.audio.punch01.get()
        self._swish_sound = _classicassets.audio.punch_swish.get()
        self._errorsound = _builtinassets.audio.error.get()
        self._mask_texture = (
            _classiccatalogassets.textures.character_icon_mask.get()
        )
        self._vpos = vpos
        self._lobby = weakref.ref(lobby)
        self._sessionplayer = sessionplayer
        self._inited = False
        self._dead = False
        self._text_node: bascenev1.Node | None = None
        self._profilename = ''
        self._profilenames: list[str] = []
        self._ready: bool = False
        self._character_names: list[str] = []
        self._last_change: Sequence[float | int] = (0, 0)
        self._profiles: dict[str, dict[str, Any]] = {}
        # Cloud profiles, when this player's source supplies them (the
        # joiner's v2-auth data for remote players, our own synced cache
        # for local ones): each one's (spaz json, icon block json) keyed
        # by profile name -- also what a player carries out of the lobby
        # is built from these (see get_cloud_look_json()). Empty in
        # legacy mode. Kept as json: every live spaz def and depiction
        # rides the session stream (to every client), so we only make
        # objects for the selected look, not for each of the player's
        # profiles (accounts can have ~100).
        self._cloud_json_by_name: dict[str, tuple[str, str]] = {}
        # The selected look's spaz def and icon depiction, and the
        # look they were made for (remade only when that changes).
        self._cloud_spaz_def: bascenev1.SpazDef | None = None
        self._cloud_icon: bascenev1.Depiction | None = None
        self._cloud_made_look: str | None = None
        # Each cloud profile's name as the cloud composed it (a name
        # block's json): how it shows, which may differ from the
        # profile name it's keyed by (an __account__ profile shows the
        # account's).
        self._cloud_name_by_name: dict[str, str] = {}
        # The name depiction our name node shows, with its json (kept
        # while the name stays the same; replaced when it changes).
        self._name_depiction: tuple[str, bascenev1.Depiction] | None = None
        # The cloud profile whose look (spaz, icon, colors) we're
        # borrowing via the character-override button while keeping
        # the selected profile's name; None for the profile's own look.
        # Lasts until the profile selection changes.
        self._cloud_look_name = None

        app = babase.app
        assert app.classic is not None

        # Load available player profiles either from the local config or
        # from the remote device.
        self.reload_profiles()

        # Note: this is just our local index out of available teams; *not*
        # the team-id!
        self._selected_team_index: int = self.lobby.next_add_team

        # Store a persistent random character index and colors; we'll use this
        # for the '_random' profile. Let's use their input_device id to seed
        # it. This will give a persistent character for them between games
        # and will distribute characters nicely if everyone is random.
        self._random_color, self._random_highlight = get_player_profile_colors(
            None
        )

        # To calc our random character we pick a random one out of our
        # unlocked list and then locate that character's index in the full
        # list.
        char_index_offset: int = app.classic.lobby_random_char_index_offset
        self._random_character_index = (
            sessionplayer.inputdevice.id + char_index_offset
        ) % len(self._character_names)

        # Attempt to set an initial profile based on what was used previously
        # for this input-device, etc.
        self._profileindex = self._select_initial_profile()
        self._profilename = self._profilenames[self._profileindex]

        # Our name (and '(ready)' after it) as a name depiction, in our
        # color; see _update_text().
        self._text_node = _bascenev1.newnode(
            'depictiondisplay',
            delegate=self,
            attrs={
                'position': (
                    _NAME_BOX_LEFT + _NAME_BOX_WIDTH * 0.5,
                    self._vpos,
                ),
                'vr_depth': -20,
                'h_align': 'left',
                'v_align': 'center',
                'attach': 'topCenter',
                'use_color_override': True,
                # A team's color stays dominant over a capsule's own.
                'team_coloring': self.lobby.use_team_colors,
            },
        )
        animate_array(
            self._text_node,
            'scale',
            2,
            {0: (0, 0), 0.1: (_NAME_BOX_WIDTH, _NAME_BOX_HEIGHT)},
        )
        self.icon = _bascenev1.newnode(
            'image',
            owner=self._text_node,
            attrs={
                'position': (-130, self._vpos + 20),
                'mask_texture': self._mask_texture,
                'vr_depth': -10,
                'attach': 'topCenter',
            },
        )

        animate_array(self.icon, 'scale', 2, {0: (0, 0), 0.1: (45, 45)})

        # Set our initial name to '<choosing player>' in case anyone asks.
        self._sessionplayer.setname(
            _classicassets.strings.lobby.choosing_player.evaluate(), real=False
        )

        # Init these to our rando but they should get switched to the
        # selected profile (if any) right after.
        self._character_index = self._random_character_index
        self._color = self._random_color
        self._highlight = self._random_highlight

        self.update_from_profile()
        self.update_position()
        self._inited = True

        self._set_ready(False)

        # Confirm the join physically. This is the moment someone pressed
        # a button and got in, so it is exactly the kind of
        # tied-to-your-own-action event haptics read well for. Fired once
        # per session join (Session.on_player_request), so unlike the
        # in-game events it needs no rate limiting.
        self._sessionplayer.send_feedback(event='join')

    def _select_initial_profile(self) -> int:
        # pylint: disable=too-many-return-statements
        app = babase.app
        assert app.classic is not None
        profilenames = self._profilenames
        inputdevice = self._sessionplayer.inputdevice

        # A session that fixes its profiles: everyone starts on the
        # first of them. (Nothing remembered or account-related comes
        # into it, and there may be no random one to fall back to.)
        if self.lobby.fixed_profiles is not None and '_random' not in (
            profilenames
        ):
            return 0

        # If we've got a set profile name for this device, work backwards
        # from that to get our index.
        dprofilename = app.config.get('Default Player Profiles', {}).get(
            inputdevice.name + ' ' + inputdevice.unique_identifier
        )
        if dprofilename is not None and dprofilename in profilenames:
            # If we got '__account__' and its local and we haven't marked
            # anyone as the 'account profile' device yet, mark this guy as
            # it. (prevents the next joiner from getting the account
            # profile too).
            if (
                dprofilename == '__account__'
                and not inputdevice.is_remote_client
                and app.classic.lobby_account_profile_device_id is None
            ):
                app.classic.lobby_account_profile_device_id = inputdevice.id
            return profilenames.index(dprofilename)

        # We want to mark the first local input-device in the game
        # as the 'account profile' device.
        if (
            not inputdevice.is_remote_client
            and not inputdevice.is_controller_app
        ):
            if (
                app.classic.lobby_account_profile_device_id is None
                and '__account__' in profilenames
            ):
                app.classic.lobby_account_profile_device_id = inputdevice.id

        # If this is the designated account-profile-device, try to default
        # to the account profile.
        if (
            inputdevice.id == app.classic.lobby_account_profile_device_id
            and '__account__' in profilenames
        ):
            return profilenames.index('__account__')

        # If this is the controller app, it defaults to using a random
        # profile (since we can pull the random name from the app).
        if inputdevice.is_controller_app and '_random' in profilenames:
            return profilenames.index('_random')

        # If its a client connection, for now just force the account
        # profile if possible. (need to provide a way for clients to
        # specify/remember their default profile on remote servers that
        # do not already know them).
        if inputdevice.is_remote_client and '__account__' in profilenames:
            return profilenames.index('__account__')

        # Cycle through our non-random profiles once; after
        # that, everyone gets random.
        while app.classic.lobby_random_profile_index < len(
            profilenames
        ) and profilenames[app.classic.lobby_random_profile_index] in (
            '_random',
            '__account__',
            '_edit',
        ):
            app.classic.lobby_random_profile_index += 1
        if app.classic.lobby_random_profile_index < len(profilenames):
            profileindex: int = app.classic.lobby_random_profile_index
            app.classic.lobby_random_profile_index += 1
            return profileindex
        assert '_random' in profilenames
        return profilenames.index('_random')

    @property
    def sessionplayer(self) -> bascenev1.SessionPlayer:
        """The session-player associated with this chooser."""
        return self._sessionplayer

    @property
    def ready(self) -> bool:
        """Whether this chooser is checked in as ready."""
        return self._ready

    def set_vpos(self, vpos: float) -> None:
        """(internal)

        :meta private:
        """
        self._vpos = vpos

    def set_dead(self, val: bool) -> None:
        """(internal)

        :meta private:
        """
        self._dead = val

    @property
    def sessionteam(self) -> bascenev1.SessionTeam:
        """Return this chooser's currently selected bascenev1.SessionTeam."""
        return self.lobby.sessionteams[self._selected_team_index]

    @property
    def lobby(self) -> bascenev1.Lobby:
        """The chooser's lobby."""
        lobby = self._lobby()
        if lobby is None:
            raise babase.NotFoundError('Lobby does not exist.')
        return lobby

    def get_lobby(self) -> bascenev1.Lobby | None:
        """Return this chooser's lobby if it still exists; otherwise None."""
        return self._lobby()

    def update_from_profile(self) -> None:
        """Set character/colors based on the current profile."""
        assert babase.app.classic is not None
        self._profilename = self._profilenames[self._profileindex]
        # A cloud profile carries its whole look as a composed spaz def;
        # everything else (legacy profiles, random, edit) is legacy-form.
        # The look may be borrowed from another of our cloud profiles
        # (see _cycle_cloud_look()); drop a borrow whose source is gone.
        if (
            self._profilename not in self._cloud_json_by_name
            or self._cloud_look_name not in self._cloud_json_by_name
        ):
            self._cloud_look_name = None
        look = self._cloud_look_name or self._profilename
        self._make_cloud_look(look)
        if self._profilename == '_edit':
            pass
        elif self._profilename == '_random':
            self._character_index = self._random_character_index
            self._color = self._random_color
            self._highlight = self._random_highlight
        else:
            character = self._profiles[self._profilename]['character']

            # At the moment we're not properly pulling the list
            # of available characters from clients, so profiles might use a
            # character not in their list. For now, just go ahead and add
            # a character name to their list as long as we're aware of it.
            # This just means they won't always be able to override their
            # character to others they own, but profile characters
            # should work (and we validate profiles on the master server
            # so no exploit opportunities)
            if (
                character not in self._character_names
                and character in babase.app.classic.spaz_appearances
            ):
                self._character_names.append(character)
            self._character_index = self._character_names.index(character)
            # Colors are part of the look, so a borrowed look brings
            # its own.
            if self._cloud_spaz_def is not None:
                self._color = self._cloud_spaz_def.color or (0.5, 0.5, 0.5)
                self._highlight = self._cloud_spaz_def.highlight or (
                    0.5,
                    0.5,
                    0.5,
                )
            else:
                self._color, self._highlight = get_player_profile_colors(
                    look, profiles=self._profiles
                )
        self._update_icon()
        self._update_text()

    def reload_profiles(self) -> None:
        """Reload all player profiles."""

        app = babase.app
        assert app.classic is not None

        # Re-construct our profile index and other stuff since the profile
        # list might have changed.
        input_device = self._sessionplayer.inputdevice
        is_remote = input_device.is_remote_client
        is_test_input = input_device.is_test_input

        # Pull this player's list of unlocked characters.
        if is_remote:
            # v2-auth hosts can get an authoritative purchases list
            # from the master server — see
            # ``input_device.get_classic_purchases()``. When that
            # returns ``None`` (non-v2-auth connection, older
            # master, etc.) fall back to the legacy behavior: start
            # with just 'Spaz' and let ``update_from_profile()``
            # lazily append characters referenced in the remote
            # player's (master-server-validated) profiles. The
            # purchases snapshot is captured at handshake time, so
            # characters unlocked mid-match won't appear until
            # rejoin — mirrors local-player behavior
            # (``character_names_local_unlocked`` is only refreshed
            # at lobby reload).
            classic_purchases: list[str] | None = (
                input_device.get_classic_purchases()
            )
            if classic_purchases is None:
                self._character_names = ['Spaz']
            else:
                # Run through the same mapper local players use so
                # the legacy-id → in-game-name translation lives in
                # one place.
                # pylint: disable=cyclic-import
                from bascenev1lib.actor.spazappearance import (
                    get_appearances,
                )

                self._character_names = get_appearances(
                    purchases=classic_purchases
                )
                self._character_names.sort(key=lambda x: x.lower())
                if not self._character_names:
                    self._character_names = ['Spaz']
        else:
            self._character_names = self.lobby.character_names_local_unlocked

        # If we're a local player, pull our local profiles from the config.
        # Otherwise ask the remote-input-device for its profile list.
        if is_remote:
            self._profiles = input_device.get_player_profiles()
        else:
            self._profiles = app.config.get('Player Profiles', {})

        # Cloud profiles (cloud-profiles D11): when the master server has
        # composed a character list for this player -- delivered with
        # the v2-auth handshake for remote players, synced into our own
        # cache for local ones -- that list is the authoritative set and
        # replaces the legacy profiles outright. None means no cloud
        # data (old host, v2-auth off, offline, not fetched yet): fall
        # back to legacy profiles.
        self._apply_cloud_profiles(
            input_device, is_remote=is_remote, is_test_input=is_test_input
        )

        # Filter out any characters we're unaware of. These profiles can
        # arrive over the wire from clients, so a malformed 'character'
        # value (e.g. an unhashable list) must not be allowed to reach
        # the membership check below; that would raise and abort the
        # join partway through, leaving the session corrupted.
        for profile in list(self._profiles.items()):
            character = profile[1].get('character', '')
            if (
                not isinstance(character, str)
                or character not in app.classic.spaz_appearances
            ):
                profile[1]['character'] = 'Spaz'

        # A session that fixes its profiles offers those and nothing
        # more: no random one, and no editing. (Unless none of them
        # was usable, which leaves the random one as the only way in.)
        fixed = self.lobby.fixed_profiles is not None and bool(self._profiles)

        # Add in a random one so we're ok even if there's no user profiles.
        if not fixed:
            self._profiles['_random'] = {}

        # In kiosk mode we disable account profiles to force random.
        variant = babase.app.env.variant
        vart = type(variant)
        arcade_or_demo = variant is vart.ARCADE or variant is vart.DEMO

        if arcade_or_demo and not fixed:
            if '__account__' in self._profiles:
                del self._profiles['__account__']

        # For local devices, add it an 'edit' option which will pop up
        # the profile window.
        if (
            not is_remote
            and not is_test_input
            and not arcade_or_demo
            and not fixed
        ):
            self._profiles['_edit'] = {}

        # Build a sorted name list we can iterate through.
        self._profilenames = list(self._profiles.keys())
        self._profilenames.sort(key=lambda x: x.lower())

        if self._profilename in self._profilenames:
            self._profileindex = self._profilenames.index(self._profilename)
        else:
            self._profileindex = 0
            self._profilename = self._profilenames[self._profileindex]

    def update_position(self) -> None:
        """Update this chooser's position."""

        assert self._text_node
        spacing = 350
        sessionteams = self.lobby.sessionteams
        offs = (
            spacing * -0.5 * len(sessionteams)
            + spacing * self._selected_team_index
            + 250
        )
        if len(sessionteams) > 1:
            offs -= 35
        animate_array(
            self._text_node,
            'position',
            2,
            {
                0: self._text_node.position,
                0.1: (
                    _NAME_BOX_LEFT + _NAME_BOX_WIDTH * 0.5 + offs,
                    self._vpos + 23,
                ),
            },
        )
        animate_array(
            self.icon,
            'position',
            2,
            {0: self.icon.position, 0.1: (-130 + offs, self._vpos + 22)},
        )

    def get_character_name(self) -> str:
        """Return the selected character name.

        For a cloud profile this is the legacy standin appearance; the
        real look is :meth:`get_cloud_spaz_def`.
        """
        return self._character_names[self._character_index]

    def get_cloud_spaz_def(self) -> bascenev1.SpazDef | None:
        """Return the selected cloud profile's composed look.

        That is the profile's own look, or another of the player's
        cloud profiles' if they've borrowed one with the
        character-override button. None when the selection is a legacy
        profile or the random look.
        """
        return self._cloud_spaz_def

    def _cycle_cloud_look(self, step: int) -> None:
        """Step the look of our cloud profile through our other ones.

        The character-override button for cloud profiles: a cloud look
        is a sealed, server-composed whole, so rather than swapping a
        character inside it we borrow another of the player's profiles'
        look (spaz, icon, colors) while keeping the selected profile's
        name. The cycle runs in profile order and comes back around to
        the profile's own look.
        """
        names = [n for n in self._profilenames if n in self._cloud_json_by_name]
        if len(names) < 2:
            # No other looks to borrow.
            self._errorsound.play()
            return
        current = self._cloud_look_name or self._profilename
        index = names.index(current) if current in names else 0
        look = names[(index + step) % len(names)]
        self._cloud_look_name = None if look == self._profilename else look
        self._click_sound.play()
        self.update_from_profile()

    def get_cloud_icon(self) -> bascenev1.Depiction | None:
        """Return the selected cloud profile's icon depiction.

        None exactly when :meth:`get_cloud_spaz_def` is None.
        """
        return self._cloud_icon

    def get_cloud_look_json(self) -> tuple[str, str] | None:
        """Return the selected cloud look as json, for the player.

        (spaz json, icon depiction json), or None exactly when
        :meth:`get_cloud_spaz_def` is None. Our own spaz def and icon
        live in the session scene with the lobby; a player carries the
        json instead and gets objects made in each activity's own scene
        (scene objects never cross scenes).
        """
        look = self._cloud_look_name or self._profilename
        if self._cloud_spaz_def is None:
            return None
        blocks = self._cloud_json_by_name.get(look)
        if blocks is None:
            return None
        spaz_json, icon_block = blocks
        # In a teams game the icon takes the team's color in place of
        # its own main one, as the spaz does; baked into the depiction
        # as its color override so everything showing the player's
        # icon follows.
        color: tuple[float, float, float] | None = None
        if self.lobby.use_team_colors:
            red, green, blue = self.get_color()
            color = (red, green, blue)
        return spaz_json, dataclass_to_json(
            bdep.CharacterIconDepiction(
                icon_block,
                color_override=color,
                team_coloring=color is not None,
            )
        )

    def _apply_cloud_profiles(
        self,
        input_device: bascenev1.InputDevice,
        *,
        is_remote: bool,
        is_test_input: bool,
    ) -> None:
        """Replace our profile table with the player's cloud profiles.

        Sources: the joiner's v2-auth data for remote players, our own
        synced cache for local ones. When either yields a list it fills
        ``_cloud_json_by_name`` and rewrites ``_profiles`` in the legacy
        shape the rest of the chooser reads (name and the standin
        appearance name for anything still reading ``character``).
        None from the source leaves the legacy profiles in place.
        """
        classic = babase.app.classic
        assert classic is not None
        # (A session that fixes its profiles overrides everyone's own,
        # in the same form.)
        cloud_json: list[str] | None = self.lobby.fixed_profiles
        if cloud_json is not None:
            pass
        elif is_remote:
            cloud_json = input_device.get_cloud_characters()
        elif not is_test_input:
            cloud_json = classic.cloud_profiles.get_usable_profiles()
            plus = babase.app.plus
            if (
                cloud_json is None
                and plus is not None
                and plus.accounts.have_primary_credentials()
            ):
                # Legacy profiles must be obvious (D11); the lobby
                # says so once -- but only for someone signed in
                # (offline, or the cloud data not here yet). Signed
                # out, having no cloud profiles is stating the
                # obvious. (Remote players hear it from their own
                # client when they join an old or v2-auth-off host.)
                self.lobby.warn_legacy_profiles_once()
        self._cloud_name_by_name = {}
        self._cloud_json_by_name = {}
        # A look's json can change under the same name; remake on the
        # next update_from_profile().
        self._cloud_made_look = None
        if cloud_json is None:
            return
        profiles: dict[str, dict[str, Any]] = {}
        for cjson in cloud_json:
            # A profile arrives as a whole character; we use its parts
            # (look, name, icon) independently.
            parts = split_character(cjson)
            # Keyed by the profile's own name (an __account__ profile
            # shows the account's name; that's display only). Older
            # cached data had no key; its shown name was the key.
            cname = parts.profile or name_text(parts.name)
            if (
                cname is None
                or cname in profiles
                or parts.spaz is None
                or parts.icon is None
            ):
                # Unusable or duplicate composition; the server
                # shouldn't produce these.
                continue
            # (Colors come from the look's spaz def once it's made;
            # see update_from_profile().)
            profiles[cname] = {'character': 'Spaz'}
            self._cloud_json_by_name[cname] = (parts.spaz, parts.icon)
            if parts.name is not None:
                self._cloud_name_by_name[cname] = parts.name
        self._profiles = profiles

    def _make_cloud_look(self, look: str) -> None:
        """Make the spaz def and icon for a cloud look (None: legacy).

        Reuses the current ones while the look is unchanged; otherwise
        the old ones are dropped, so a chooser holds at most one of
        each however far the player browses.
        """
        if look == self._cloud_made_look:
            return
        jsons = self._cloud_json_by_name.get(look)
        if jsons is None:
            self._cloud_spaz_def = None
            self._cloud_icon = None
            self._cloud_made_look = None
            return
        spaz_json, icon_block = jsons
        self._cloud_spaz_def = _bascenev1.SpazDef(spaz_json)
        self._cloud_icon = _bascenev1.Depiction(
            dataclass_to_json(bdep.CharacterIconDepiction(icon_block))
        )
        self._cloud_made_look = look

    def _ensure_icon_node(self, *, cloud: bool) -> bool:
        """Make our icon node the right kind for the current selection.

        Cloud profiles draw via a 'depictiondisplay' node (a character
        icon depiction), legacy profiles via an 'image' node; switching
        between them swaps the node in place (same position/size/attach).
        Returns whether a new node was made.
        """
        want = 'depictiondisplay' if cloud else 'image'
        if self.icon and self.icon.getnodetype() == want:
            return False
        position = self.icon.position if self.icon else (-130, self._vpos + 20)
        if self.icon:
            self.icon.delete()
        if cloud:
            self.icon = _bascenev1.newnode(
                'depictiondisplay',
                owner=self._text_node,
                attrs={
                    'position': position,
                    'scale': (45, 45),
                    'vr_depth': -10,
                    'attach': 'topCenter',
                    # A team's color replaces the icon's own main one
                    # (see _update_icon()).
                    'use_color_override': self.lobby.use_team_colors,
                    'team_coloring': self.lobby.use_team_colors,
                },
            )
        else:
            self.icon = _bascenev1.newnode(
                'image',
                owner=self._text_node,
                attrs={
                    'position': position,
                    'scale': (45, 45),
                    'mask_texture': self._mask_texture,
                    'vr_depth': -10,
                    'attach': 'topCenter',
                },
            )
        return True

    def _do_nothing(self) -> None:
        """Does nothing! (hacky way to disable callbacks)"""

    def _getname(self, full: bool = False) -> str:
        # Safe up-call: bascenev1 is fully imported by the time
        # this runs; the cycle pylint sees is structural only.
        # pylint: disable-next=cyclic-import
        from bascenev1 import _commonassets, _classicassets

        name_raw = name = self._profilenames[self._profileindex]
        clamp = False
        if name == '_random':
            try:
                name = self._sessionplayer.inputdevice.get_default_player_name()
            except Exception:
                logging.exception('Error getting _random chooser name.')
                name = 'Invalid'
            clamp = not full
        elif name == '__account__':
            try:
                name = self._sessionplayer.inputdevice.get_v1_account_name(full)
            except Exception:
                logging.exception('Error getting account name for chooser.')
                name = 'Invalid'
            clamp = not full
        elif name == '_edit':
            # Explicitly flattening this to a str; it's only relevant on
            # the host so that's ok.
            name = _classicassets.strings.lobby.create_edit_player.evaluate()
        else:
            # If we have a regular profile marked as global with an icon,
            # use it (for full only).
            if full:
                try:
                    if self._profiles[name_raw].get('global', False):
                        icon = (
                            self._profiles[name_raw]['icon']
                            if 'icon' in self._profiles[name_raw]
                            else babase.charstr(babase.SpecialChar.LOGO)
                        )
                        name = icon + name
                except Exception:
                    logging.exception('Error applying global icon.')
            else:
                # We now clamp non-full versions of names so there's at
                # least some hope of reading them in-game.
                clamp = True

        if clamp:
            if len(name) > 10:
                name = name[:10] + '...'
        return name

    def _set_ready(self, ready: bool) -> None:
        # pylint: disable=cyclic-import

        classic = babase.app.classic
        assert classic is not None

        profilename = self._profilenames[self._profileindex]

        # Handle '_edit' as a special case.
        if profilename == '_edit' and ready:
            with babase.ContextRef.empty():

                classic.profile_browser_window()

                # Give their input-device main-UI ownership too (prevent
                # someone else from snatching it in crowded games).
                babase.set_main_ui_input_device(
                    self._sessionplayer.inputdevice.id
                )
            return

        if not ready:
            self._sessionplayer.assigninput(
                babase.InputType.LEFT_PRESS,
                babase.CallStrict(
                    self.handlemessage, ChangeMessage('team', -1)
                ),
            )
            self._sessionplayer.assigninput(
                babase.InputType.RIGHT_PRESS,
                babase.CallStrict(self.handlemessage, ChangeMessage('team', 1)),
            )
            self._sessionplayer.assigninput(
                babase.InputType.BOMB_PRESS,
                babase.CallStrict(
                    self.handlemessage, ChangeMessage('character', 1)
                ),
            )
            self._sessionplayer.assigninput(
                babase.InputType.UP_PRESS,
                babase.CallStrict(
                    self.handlemessage, ChangeMessage('profileindex', -1)
                ),
            )
            self._sessionplayer.assigninput(
                babase.InputType.DOWN_PRESS,
                babase.CallStrict(
                    self.handlemessage, ChangeMessage('profileindex', 1)
                ),
            )
            self._sessionplayer.assigninput(
                (
                    babase.InputType.JUMP_PRESS,
                    babase.InputType.PICK_UP_PRESS,
                    babase.InputType.PUNCH_PRESS,
                ),
                babase.CallStrict(
                    self.handlemessage, ChangeMessage('ready', 1)
                ),
            )
            self._ready = False
            self._update_text()
            self._sessionplayer.setname('untitled', real=False)
        else:
            self._sessionplayer.assigninput(
                (
                    babase.InputType.LEFT_PRESS,
                    babase.InputType.RIGHT_PRESS,
                    babase.InputType.UP_PRESS,
                    babase.InputType.DOWN_PRESS,
                    babase.InputType.JUMP_PRESS,
                    babase.InputType.BOMB_PRESS,
                    babase.InputType.PICK_UP_PRESS,
                ),
                self._do_nothing,
            )
            self._sessionplayer.assigninput(
                (
                    babase.InputType.JUMP_PRESS,
                    babase.InputType.BOMB_PRESS,
                    babase.InputType.PICK_UP_PRESS,
                    babase.InputType.PUNCH_PRESS,
                ),
                babase.CallStrict(
                    self.handlemessage, ChangeMessage('ready', 0)
                ),
            )

            # Store the last profile picked by this input for reuse.
            input_device = self._sessionplayer.inputdevice
            name = input_device.name
            unique_id = input_device.unique_identifier
            device_profiles = babase.app.config.setdefault(
                'Default Player Profiles', {}
            )

            # Make an exception if we have no custom profiles and are set
            # to random; in that case we'll want to start picking up custom
            # profiles if/when one is made so keep our setting cleared.
            special = ('_random', '_edit', '__account__')
            have_custom_profiles = any(p not in special for p in self._profiles)

            profilekey = name + ' ' + unique_id
            if self.lobby.fixed_profiles is not None:
                # (Not this player's pick among their own profiles;
                # nothing to remember.)
                pass
            elif profilename == '_random' and not have_custom_profiles:
                if profilekey in device_profiles:
                    del device_profiles[profilekey]
                babase.app.config.commit()
            else:
                device_profiles[profilekey] = profilename
                babase.app.config.commit()

            # Set this player's short and full name.
            self._sessionplayer.setname(
                self._getname(), self._getname(full=True), real=True
            )
            self._ready = True
            self._update_text()

            # Inform the session that this player is ready.
            _bascenev1.getsession().handlemessage(PlayerReadyMessage(self))

    def _handle_ready_msg(self, ready: bool) -> None:
        # Stress-test input devices mash random buttons; if they could
        # un-ready, a lobby of them would churn forever without ever
        # reaching all-ready. Their ready state only moves forward, and
        # they never land on the profile-editor entry (which would pop
        # a window instead of readying).
        if self._sessionplayer.inputdevice.is_test_input:
            if not ready:
                return
            if self._profilenames[self._profileindex] == '_edit':
                self.handlemessage(ChangeMessage('profileindex', 1))

        force_team_switch = False

        # Team auto-balance kicks us to another team if we try to
        # join the team with the most players.
        if not self._ready:
            if babase.app.config.get('Auto Balance Teams', False):
                lobby = self.lobby
                sessionteams = lobby.sessionteams
                if len(sessionteams) > 1:
                    # First, calc how many players are on each team
                    # ..we need to count both active players and
                    # choosers that have been marked as ready.
                    team_player_counts = {}
                    for sessionteam in sessionteams:
                        team_player_counts[sessionteam.id] = len(
                            sessionteam.players
                        )
                    for chooser in lobby.choosers:
                        if chooser.ready:
                            team_player_counts[chooser.sessionteam.id] += 1
                    largest_team_size = max(team_player_counts.values())
                    smallest_team_size = min(team_player_counts.values())

                    # Force switch if we're on the biggest sessionteam
                    # and there's a smaller one available.
                    if (
                        largest_team_size != smallest_team_size
                        and team_player_counts[self.sessionteam.id]
                        >= largest_team_size
                    ):
                        force_team_switch = True

        # Either force switch teams, or actually for realsies do the set-ready.
        if force_team_switch:
            self._errorsound.play()
            self.handlemessage(ChangeMessage('team', 1))
        else:
            self._punchsound.play()
            self._set_ready(ready)

    # TODO: should handle this at the engine layer so this is unnecessary.
    def _handle_repeat_message_attack(self) -> None:
        now = babase.apptime()
        count = self._last_change[1]
        if now - self._last_change[0] < QUICK_CHANGE_INTERVAL:
            count += 1
            if count > MAX_QUICK_CHANGE_COUNT:
                _bascenev1.disconnect_client(
                    self._sessionplayer.inputdevice.client_id
                )
        elif now - self._last_change[0] > QUICK_CHANGE_RESET_INTERVAL:
            count = 0
        self._last_change = (now, count)

    def handlemessage(self, msg: Any) -> Any:
        """Standard generic message handler."""
        # Safe up-call: bascenev1 is fully imported by the time
        # this runs; the cycle pylint sees is structural only.
        # pylint: disable-next=cyclic-import
        from bascenev1 import _builtinassets

        if isinstance(msg, ChangeMessage):
            self._handle_repeat_message_attack()

            # If we've been removed from the lobby, ignore this stuff.
            if self._dead:
                logging.error('chooser got ChangeMessage after dying')
                return

            if not self._text_node:
                logging.error('got ChangeMessage after nodes died')
                return

            if msg.what == 'team':
                sessionteams = self.lobby.sessionteams
                if len(sessionteams) > 1:
                    self._swish_sound.play()
                self._selected_team_index = (
                    self._selected_team_index + msg.value
                ) % len(sessionteams)
                self._update_text()
                self.update_position()
                self._update_icon()

            elif msg.what == 'profileindex':
                if len(self._profilenames) == 1:
                    # This should be pretty hard to hit now with
                    # automatic local accounts.
                    _builtinassets.audio.error.get().play()
                else:
                    # Pick the next player profile and assign our name
                    # and character based on that.
                    self._deek_sound.play()
                    self._profileindex = (self._profileindex + msg.value) % len(
                        self._profilenames
                    )
                    # A new profile starts out in its own look (as a
                    # legacy character override resets here too).
                    self._cloud_look_name = None
                    self.update_from_profile()

            elif msg.what == 'character':
                if self._profilename in self._cloud_json_by_name:
                    self._cycle_cloud_look(msg.value)
                    return
                self._click_sound.play()
                # update our index in our local list of characters
                self._character_index = (
                    self._character_index + msg.value
                ) % len(self._character_names)
                self._update_text()
                self._update_icon()

            elif msg.what == 'ready':
                self._handle_ready_msg(bool(msg.value))

    def _update_text(self) -> None:
        # Safe up-call: bascenev1 is fully imported by the time
        # this runs; the cycle pylint sees is structural only.
        # pylint: disable-next=cyclic-import
        from bascenev1 import _commonassets, _classicassets

        assert self._text_node is not None
        self._text_node.depiction = self._get_name_depiction()
        self._text_node.suffix = (
            _commonassets.strings.compose.parenthesized(
                note=_classicassets.strings.lobby.ready
            )
            if self._ready
            else ''
        )

        can_switch_teams = len(self.lobby.sessionteams) > 1

        # Our color is imposed on the name (as legacy's name text always
        # showed in it; a capsule routes it where it wants it).
        fin_color = babase.safecolor(self.get_color())
        if not self._inited:
            self._text_node.color_override = fin_color
            # Flash as we're coming in.
            animate(
                self._text_node,
                'brightness',
                {0.15: 1.0, 0.25: 2.0, 0.35: 1.0},
            )
        else:
            # Blend if we're in teams mode; switch instantly otherwise.
            if can_switch_teams:
                animate_array(
                    self._text_node,
                    'color_override',
                    3,
                    {0: self._text_node.color_override, 0.1: fin_color},
                )
            else:
                self._text_node.color_override = fin_color

    def _get_name_depiction(self) -> bascenev1.Depiction:
        """Our current selection's full name, as a session depiction.

        A cloud profile shows the name the cloud composed for it (with
        its glyph if global). An __account__ profile shows the
        account's name: our own live one for a local player (the cloud
        doesn't send it to us; it can change at any time), the one the
        cloud sent with a remote player's profiles otherwise. Anything
        else -- legacy profiles, random, edit -- shows its plain name.
        """
        depiction_json = self._get_name_depiction_json()
        if (
            self._name_depiction is None
            or self._name_depiction[0] != depiction_json
        ):
            self._name_depiction = (
                depiction_json,
                _bascenev1.Depiction(depiction_json),
            )
        return self._name_depiction[1]

    def get_name_depiction_json(self) -> str:
        """Return our name as depiction json, for the player.

        The name our own display shows (see
        ``_get_name_depiction()``) with our color baked in as its
        color override (and team coloring in a teams game), so
        everything showing the player's name by itself follows, as with
        the icon from :meth:`get_cloud_look_json`.
        """
        depiction = dataclass_from_json(
            bdep.Depiction, self._get_name_depiction_json()
        )
        assert isinstance(depiction, bdep.NameDepiction)
        red, green, blue = babase.safecolor(self.get_color())[:3]
        depiction.color_override = (red, green, blue)
        depiction.team_coloring = self.lobby.use_team_colors
        return dataclass_to_json(depiction)

    def _get_name_depiction_json(self) -> str:
        assert babase.app.classic is not None
        name = self._profilename
        depiction_json: str | None = None
        if name == '__account__' and not (
            self._sessionplayer.inputdevice.is_remote_client
        ):
            if name in self._cloud_json_by_name:
                depiction_json = (
                    babase.app.classic.account_name_depiction or None
                )
        else:
            name_json = self._cloud_name_by_name.get(name)
            # (A plain '__account__' name only stands in for the
            # account's for older builds; ours draws it as legacy does.)
            if name_json is not None and name_text(name_json) != '__account__':
                depiction_json = dataclass_to_json(
                    bdep.NameDepiction(name_json)
                )
        if depiction_json is None:
            depiction_json = dataclass_to_json(
                bdep.NameDepiction(
                    json.dumps(
                        {'b': {'t': self._getname(full=True)}},
                        separators=(',', ':'),
                    )
                )
            )
        return depiction_json

    def get_color(self) -> Sequence[float]:
        """Return the currently selected color."""
        val: Sequence[float]
        if self.lobby.use_team_colors:
            val = self.lobby.sessionteams[self._selected_team_index].color
        else:
            val = self._color
        if len(val) != 3:
            print('get_color: ignoring invalid color of len', len(val))
            val = (0, 1, 0)
        return val

    def get_highlight(self) -> Sequence[float]:
        """Return the currently selected highlight."""
        if self._profilenames[self._profileindex] == '_edit':
            return 0, 1, 0

        # If we're using team colors we wanna make sure our highlight color
        # isn't too close to any other team's color.
        highlight = list(self._highlight)
        if self.lobby.use_team_colors:
            for i, sessionteam in enumerate(self.lobby.sessionteams):
                if i != self._selected_team_index:
                    # Find the dominant component of this sessionteam's color
                    # and adjust ours so that the component is
                    # not super-dominant.
                    max_val = 0.0
                    max_index = 0
                    for j in range(3):
                        if sessionteam.color[j] > max_val:
                            max_val = sessionteam.color[j]
                            max_index = j
                    that_color_for_us = highlight[max_index]
                    our_second_biggest = max(
                        highlight[(max_index + 1) % 3],
                        highlight[(max_index + 2) % 3],
                    )
                    diff = that_color_for_us - our_second_biggest
                    if diff > 0:
                        highlight[max_index] -= diff * 0.6
                        highlight[(max_index + 1) % 3] += diff * 0.3
                        highlight[(max_index + 2) % 3] += diff * 0.2
        return highlight

    def getplayer(self) -> bascenev1.SessionPlayer:
        """Return the player associated with this chooser."""
        return self._sessionplayer

    def _update_icon(self) -> None:
        # Safe up-call: bascenev1 is fully imported by the time
        # this runs; the cycle pylint sees is structural only.
        # pylint: disable-next=cyclic-import
        from bascenev1 import (
            _commonassets,
            _builtinassets,
            _classicassets,
            _uiv1assets,
            _classiccatalogassets,
        )

        assert babase.app.classic is not None

        # Cloud profiles draw through a depiction display node (the
        # composed definition's own icon and colors, the standin while
        # its art loads); everything else keeps the legacy image node.
        fresh = self._ensure_icon_node(cloud=self._cloud_icon is not None)

        if self._cloud_icon is not None:
            # Safe up-call; see below.
            # pylint: disable-next=cyclic-import
            from bascenev1lib.actor import spazappearance

            self.icon.depiction = self._cloud_icon
            # In teams mode our team's color goes on the icon (in place
            # of its own main one), blending with the name's as we
            # switch teams.
            if self.lobby.use_team_colors:
                team_color = self.get_color()
                if fresh:
                    self.icon.color_override = team_color
                else:
                    animate_array(
                        self.icon,
                        'color_override',
                        3,
                        {0: self.icon.color_override, 0.1: team_color},
                    )
            # In-game icon sites draw the player's icon depiction
            # (SessionPlayer.get_icon_depiction()); the legacy icon
            # info stays for anything still reading get_icon() (mods,
            # mostly), so it gets the standin icon in this profile's
            # colors.
            self._sessionplayer.set_icon_info(
                _assetref.qualified_ref(
                    spazappearance.texture_spec(
                        _classiccatalogassets.textures.neo_spaz_icon
                    )
                ),
                _assetref.qualified_ref(
                    spazappearance.texture_spec(
                        _classiccatalogassets.textures.neo_spaz_icon_color_mask
                    )
                ),
                self.get_color(),
                self.get_highlight(),
            )
            return

        if self._profilenames[self._profileindex] == '_edit':
            tex = _builtinassets.textures.black.get()
            tint_tex = _builtinassets.textures.black_data.get()
            self.icon.color = (1, 1, 1)
            self.icon.texture = tex
            self.icon.tint_texture = tint_tex
            self.icon.tint_color = (0, 1, 0)
            return

        # Safe up-call: bascenev1lib is fully imported by the time a
        # lobby exists; the cycle pylint sees is structural only.
        # pylint: disable-next=cyclic-import
        from bascenev1lib.actor import spazappearance

        texval: spazappearance.TexVal
        tintval: spazappearance.TexVal
        try:
            appearance = babase.app.classic.spaz_appearances[
                self._character_names[self._character_index]
            ]
            texval = appearance.icon_texture
            tintval = appearance.icon_mask_texture
        except Exception:
            logging.exception('Error updating char icon list')
            texval = _classiccatalogassets.textures.neo_spaz_icon
            tintval = _classiccatalogassets.textures.neo_spaz_icon_color_mask

        tex = spazappearance.scene_texture(texval)
        tint_tex = spazappearance.scene_texture(tintval)

        self.icon.color = (1, 1, 1)
        self.icon.texture = tex
        self.icon.tint_texture = tint_tex
        clr = self.get_color()
        clr2 = self.get_highlight()

        can_switch_teams = len(self.lobby.sessionteams) > 1

        # If we're initing, flash.
        if not self._inited:
            animate_array(
                self.icon,
                'color',
                3,
                {0.15: (1, 1, 1), 0.25: (2, 2, 2), 0.35: (1, 1, 1)},
            )

        # Blend in teams mode; switch instantly in ffa-mode.
        if can_switch_teams:
            animate_array(
                self.icon, 'tint_color', 3, {0: self.icon.tint_color, 0.1: clr}
            )
        else:
            self.icon.tint_color = clr
        self.icon.tint2_color = clr2

        # Store the icon info the the player.
        # set_icon_info is a native call taking qualified engine
        # names (they ride the wire to other clients).
        texspec = spazappearance.texture_spec(texval)
        tintspec = spazappearance.texture_spec(tintval)
        self._sessionplayer.set_icon_info(
            _assetref.qualified_ref(texspec),
            _assetref.qualified_ref(tintspec),
            clr,
            clr2,
        )


class Lobby:
    """Environment where players can selecting characters, etc."""

    def __del__(self) -> None:
        # Reset any players that still have a chooser in us.
        # (should allow the choosers to die).
        sessionplayers = [
            c.sessionplayer for c in self.choosers if c.sessionplayer
        ]
        for sessionplayer in sessionplayers:
            sessionplayer.resetinput()

    def __init__(self) -> None:
        from bascenev1._team import SessionTeam
        from bascenev1._coopsession import CoopSession

        session = _bascenev1.getsession()
        self._use_team_colors = session.use_team_colors
        if session.use_teams:
            self._sessionteams = [
                weakref.ref(team) for team in session.sessionteams
            ]
        else:
            self._dummy_teams = SessionTeam()
            self._sessionteams = [weakref.ref(self._dummy_teams)]
        v_offset = -150 if isinstance(session, CoopSession) else -50
        self.choosers: list[Chooser] = []
        self.base_v_offset = v_offset
        self.update_positions()
        self._next_add_team = 0
        self.character_names_local_unlocked: list[str] = []
        self._vpos = 0
        self._warned_legacy_profiles = False

        #: The only profiles choosers here offer, when the session
        #: fixes them (see :meth:`Session.get_fixed_profiles`).
        self.fixed_profiles: list[str] | None = session.get_fixed_profiles()

        # Grab available profiles.
        self.reload_profiles()

        self._join_info_text = None

    def warn_legacy_profiles_once(self) -> None:
        """Tell the local player their cloud profiles are unavailable.

        Shown once per lobby, when a signed-in local player's chooser
        falls back to legacy profiles (offline, or not yet fetched).
        """
        # Safe up-call: bascenev1 is fully imported by the time this
        # runs; the cycle pylint sees is structural only.
        # pylint: disable-next=cyclic-import
        from bascenev1 import _classicassets

        if self._warned_legacy_profiles:
            return
        self._warned_legacy_profiles = True
        babase.screenmessage(
            _classicassets.strings.lobby.legacy_profiles_only,
            color=(1.0, 1.0, 0.0),
        )

    @property
    def next_add_team(self) -> int:
        """(internal)"""
        return self._next_add_team

    @property
    def use_team_colors(self) -> bool:
        """Whether this lobby is using team colors.

        If False, inidividual player colors are used instead.
        """
        return self._use_team_colors

    @property
    def sessionteams(self) -> list[bascenev1.SessionTeam]:
        """The teams available in this lobby."""
        allteams = []
        for tref in self._sessionteams:
            team = tref()
            assert team is not None
            allteams.append(team)
        return allteams

    def get_choosers(self) -> list[Chooser]:
        """The current choosers present."""
        return self.choosers

    def create_join_info(self) -> JoinInfo:
        """Create a display of on-screen information for joiners.

        (how to switch teams, players, etc.)
        Intended for use in initial joining-screens.
        """
        return JoinInfo(self)

    def reload_profiles(self) -> None:
        """Reload available player profiles."""
        # pylint: disable=cyclic-import
        from bascenev1lib.actor.spazappearance import get_appearances

        assert babase.app.classic is not None

        # We may have gained or lost character names if the user
        # bought something; reload these too.
        self.character_names_local_unlocked = get_appearances()
        self.character_names_local_unlocked.sort(key=lambda x: x.lower())

        # Do any overall prep we need to such as creating account profile.
        babase.app.classic.accounts.ensure_have_account_player_profile()
        for chooser in self.choosers:
            try:
                chooser.reload_profiles()
                chooser.update_from_profile()
            except Exception:
                logging.exception('Error reloading profiles.')

    def update_positions(self) -> None:
        """Update positions for all choosers."""
        self._vpos = -100 + self.base_v_offset
        for chooser in self.choosers:
            chooser.set_vpos(self._vpos)
            chooser.update_position()
            self._vpos -= 48

    def check_all_ready(self) -> bool:
        """Return whether all choosers are marked ready."""
        return all(chooser.ready for chooser in self.choosers)

    def add_chooser(self, sessionplayer: bascenev1.SessionPlayer) -> None:
        """Add a chooser to the lobby for the provided player."""
        self.choosers.append(
            Chooser(vpos=self._vpos, sessionplayer=sessionplayer, lobby=self)
        )
        self._next_add_team = (self._next_add_team + 1) % len(
            self._sessionteams
        )
        self._vpos -= 48

    def remove_chooser(self, player: bascenev1.SessionPlayer) -> None:
        """Remove a single player's chooser; does not kick them.

        This is used when a player enters the game and no longer
        needs a chooser."""
        found = False
        chooser = None
        for chooser in self.choosers:
            if chooser.getplayer() is player:
                found = True

                # Mark it as dead since there could be more
                # change-commands/etc coming in still for it; want to
                # avoid duplicate player-adds/etc.
                chooser.set_dead(True)
                self.choosers.remove(chooser)
                break
        if not found:
            logging.exception('remove_chooser did not find player %s.', player)
        elif chooser in self.choosers:
            logging.exception('chooser remains after removal for %s.', player)
        self.update_positions()

    def remove_all_choosers(self) -> None:
        """Remove all choosers without kicking players.

        This is called after all players check in and enter a game.
        """
        self.choosers = []
        self.update_positions()

    def remove_all_choosers_and_kick_players(self) -> None:
        """Remove all player choosers and kick attached players."""

        # Copy the list; it can change under us otherwise.
        for chooser in list(self.choosers):
            if chooser.sessionplayer:
                chooser.sessionplayer.remove_from_game()
        self.remove_all_choosers()
