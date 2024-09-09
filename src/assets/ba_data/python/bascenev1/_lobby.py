# Released under the MIT License. See LICENSE for details.
#
"""Implements lobby system for gathering before games, char select, etc."""
# pylint: disable=too-many-lines

from __future__ import annotations

import logging
import weakref
from dataclasses import dataclass
from typing import TYPE_CHECKING

import babase
import _bascenev1
from bascenev1._profile import get_player_profile_colors
from bascenev1._gameutils import animate, animate_array

if TYPE_CHECKING:
    from typing import Any, Sequence

    import bascenev1

MAX_QUICK_CHANGE_COUNT = 30
QUICK_CHANGE_INTERVAL = 0.05
QUICK_CHANGE_RESET_INTERVAL = 1.0


# Hmm should we move this to actors?..
class JoinInfo:
    """Display useful info for joiners."""

    def __init__(self, lobby: bascenev1.Lobby):
        from bascenev1._nodeactor import NodeActor

        self._state = 0
        self._press_to_punch: str | bascenev1.Lstr = babase.charstr(
            babase.SpecialChar.LEFT_BUTTON
        )
        self._press_to_bomb: str | bascenev1.Lstr = babase.charstr(
            babase.SpecialChar.RIGHT_BUTTON
        )
        self._joinmsg = babase.Lstr(resource='pressAnyButtonToJoinText')
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

        if babase.app.env.demo or babase.app.env.arcade:
            self._messages = [self._joinmsg]
        else:
            msg1 = babase.Lstr(
                resource='pressToSelectProfileText',
                subs=[
                    (
                        '${BUTTONS}',
                        babase.charstr(babase.SpecialChar.UP_ARROW)
                        + ' '
                        + babase.charstr(babase.SpecialChar.DOWN_ARROW),
                    )
                ],
            )
            msg2 = babase.Lstr(
                resource='pressToOverrideCharacterText',
                subs=[('${BUTTONS}', babase.Lstr(resource='bombBoldText'))],
            )
            msg3 = babase.Lstr(
                value='${A} < ${B} >',
                subs=[('${A}', msg2), ('${B}', self._press_to_bomb)],
            )
            self._messages = (
                (
                    [
                        babase.Lstr(
                            resource='pressToSelectTeamText',
                            subs=[
                                (
                                    '${BUTTONS}',
                                    babase.charstr(
                                        babase.SpecialChar.LEFT_ARROW
                                    )
                                    + ' '
                                    + babase.charstr(
                                        babase.SpecialChar.RIGHT_ARROW
                                    ),
                                )
                            ],
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
            4.0, babase.WeakCall(self._update), repeat=True
        )

    def _update_for_keyboard(self, keyboard: bascenev1.InputDevice) -> None:
        classic = babase.app.classic
        assert classic is not None

        punch_key = keyboard.get_button_name(
            classic.get_input_device_mapped_value(keyboard, 'buttonPunch')
        )
        self._press_to_punch = babase.Lstr(
            resource='orText',
            subs=[
                (
                    '${A}',
                    babase.Lstr(value='\'${K}\'', subs=[('${K}', punch_key)]),
                ),
                ('${B}', self._press_to_punch),
            ],
        )
        bomb_key = keyboard.get_button_name(
            classic.get_input_device_mapped_value(keyboard, 'buttonBomb')
        )
        self._press_to_bomb = babase.Lstr(
            resource='orText',
            subs=[
                (
                    '${A}',
                    babase.Lstr(value='\'${K}\'', subs=[('${K}', bomb_key)]),
                ),
                ('${B}', self._press_to_bomb),
            ],
        )
        self._joinmsg = babase.Lstr(
            value='${A} < ${B} >',
            subs=[
                ('${A}', babase.Lstr(resource='pressPunchToJoinText')),
                ('${B}', self._press_to_punch),
            ],
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
    """A character/team selector for a bascenev1.Player.

    Category: Gameplay Classes
    """

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
        self._deek_sound = _bascenev1.getsound('deek')
        self._click_sound = _bascenev1.getsound('click01')
        self._punchsound = _bascenev1.getsound('punch01')
        self._swish_sound = _bascenev1.getsound('punchSwish')
        self._errorsound = _bascenev1.getsound('error')
        self._mask_texture = _bascenev1.gettexture('characterIconMask')
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

        self._text_node = _bascenev1.newnode(
            'text',
            delegate=self,
            attrs={
                'position': (-100, self._vpos),
                'maxwidth': 160,
                'shadow': 0.5,
                'vr_depth': -20,
                'h_align': 'left',
                'v_align': 'center',
                'v_attach': 'top',
            },
        )
        animate(self._text_node, 'scale', {0: 0, 0.1: 1.0})
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
            babase.Lstr(resource='choosingPlayerText').evaluate(), real=False
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

    def _select_initial_profile(self) -> int:
        app = babase.app
        assert app.classic is not None
        profilenames = self._profilenames
        inputdevice = self._sessionplayer.inputdevice

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

        # If its a client connection, for now just force
        # the account profile if possible.. (need to provide a
        # way for clients to specify/remember their default
        # profile on remote servers that do not already know them).
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
        """The bascenev1.SessionPlayer associated with this chooser."""
        return self._sessionplayer

    @property
    def ready(self) -> bool:
        """Whether this chooser is checked in as ready."""
        return self._ready

    def set_vpos(self, vpos: float) -> None:
        """(internal)"""
        self._vpos = vpos

    def set_dead(self, val: bool) -> None:
        """(internal)"""
        self._dead = val

    @property
    def sessionteam(self) -> bascenev1.SessionTeam:
        """Return this chooser's currently selected bascenev1.SessionTeam."""
        return self.lobby.sessionteams[self._selected_team_index]

    @property
    def lobby(self) -> bascenev1.Lobby:
        """The chooser's baclassic.Lobby."""
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
            self._color, self._highlight = get_player_profile_colors(
                self._profilename, profiles=self._profiles
            )
        self._update_icon()
        self._update_text()

    def reload_profiles(self) -> None:
        """Reload all player profiles."""

        app = babase.app
        env = app.env
        assert app.classic is not None

        # Re-construct our profile index and other stuff since the profile
        # list might have changed.
        input_device = self._sessionplayer.inputdevice
        is_remote = input_device.is_remote_client
        is_test_input = input_device.is_test_input

        # Pull this player's list of unlocked characters.
        if is_remote:
            # TODO: Pull this from the remote player.
            # (but make sure to filter it to the ones we've got).
            self._character_names = ['Spaz']
        else:
            self._character_names = self.lobby.character_names_local_unlocked

        # If we're a local player, pull our local profiles from the config.
        # Otherwise ask the remote-input-device for its profile list.
        if is_remote:
            self._profiles = input_device.get_player_profiles()
        else:
            self._profiles = app.config.get('Player Profiles', {})

        # These may have come over the wire from an older
        # (non-unicode/non-json) version.
        # Make sure they conform to our standards
        # (unicode strings, no tuples, etc)
        self._profiles = app.classic.json_prep(self._profiles)

        # Filter out any characters we're unaware of.
        for profile in list(self._profiles.items()):
            if (
                profile[1].get('character', '')
                not in app.classic.spaz_appearances
            ):
                profile[1]['character'] = 'Spaz'

        # Add in a random one so we're ok even if there's no user profiles.
        self._profiles['_random'] = {}

        # In kiosk mode we disable account profiles to force random.
        if env.demo or env.arcade:
            if '__account__' in self._profiles:
                del self._profiles['__account__']

        # For local devices, add it an 'edit' option which will pop up
        # the profile window.
        if not is_remote and not is_test_input and not (env.demo or env.arcade):
            self._profiles['_edit'] = {}

        # Build a sorted name list we can iterate through.
        self._profilenames = list(self._profiles.keys())
        self._profilenames.sort(key=lambda x: x.lower())

        if self._profilename in self._profilenames:
            self._profileindex = self._profilenames.index(self._profilename)
        else:
            self._profileindex = 0
            # noinspection PyUnresolvedReferences
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
            {0: self._text_node.position, 0.1: (-100 + offs, self._vpos + 23)},
        )
        animate_array(
            self.icon,
            'position',
            2,
            {0: self.icon.position, 0.1: (-130 + offs, self._vpos + 22)},
        )

    def get_character_name(self) -> str:
        """Return the selected character name."""
        return self._character_names[self._character_index]

    def _do_nothing(self) -> None:
        """Does nothing! (hacky way to disable callbacks)"""

    def _getname(self, full: bool = False) -> str:
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
            name = babase.Lstr(
                resource='createEditPlayerText',
                fallback_resource='editProfileWindow.titleNewText',
            ).evaluate()
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
                # if bool(True):
                #     babase.screenmessage('UNDER CONSTRUCTION')
                #     return

                classic.profile_browser_window(
                    # in_main_menu=False
                )

                # Give their input-device UI ownership too (prevent
                # someone else from snatching it in crowded games).
                babase.set_ui_input_device(self._sessionplayer.inputdevice.id)
            return

        if not ready:
            self._sessionplayer.assigninput(
                babase.InputType.LEFT_PRESS,
                babase.Call(self.handlemessage, ChangeMessage('team', -1)),
            )
            self._sessionplayer.assigninput(
                babase.InputType.RIGHT_PRESS,
                babase.Call(self.handlemessage, ChangeMessage('team', 1)),
            )
            self._sessionplayer.assigninput(
                babase.InputType.BOMB_PRESS,
                babase.Call(self.handlemessage, ChangeMessage('character', 1)),
            )
            self._sessionplayer.assigninput(
                babase.InputType.UP_PRESS,
                babase.Call(
                    self.handlemessage, ChangeMessage('profileindex', -1)
                ),
            )
            self._sessionplayer.assigninput(
                babase.InputType.DOWN_PRESS,
                babase.Call(
                    self.handlemessage, ChangeMessage('profileindex', 1)
                ),
            )
            self._sessionplayer.assigninput(
                (
                    babase.InputType.JUMP_PRESS,
                    babase.InputType.PICK_UP_PRESS,
                    babase.InputType.PUNCH_PRESS,
                ),
                babase.Call(self.handlemessage, ChangeMessage('ready', 1)),
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
                babase.Call(self.handlemessage, ChangeMessage('ready', 0)),
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
            if profilename == '_random' and not have_custom_profiles:
                if profilekey in device_profiles:
                    del device_profiles[profilekey]
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
                    _bascenev1.getsound('error').play()
                else:
                    # Pick the next player profile and assign our name
                    # and character based on that.
                    self._deek_sound.play()
                    self._profileindex = (self._profileindex + msg.value) % len(
                        self._profilenames
                    )
                    self.update_from_profile()

            elif msg.what == 'character':
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
        assert self._text_node is not None
        if self._ready:
            # Once we're ready, we've saved the name, so lets ask the system
            # for it so we get appended numbers and stuff.
            text = babase.Lstr(value=self._sessionplayer.getname(full=True))
            text = babase.Lstr(
                value='${A} (${B})',
                subs=[
                    ('${A}', text),
                    ('${B}', babase.Lstr(resource='readyText')),
                ],
            )
        else:
            text = babase.Lstr(value=self._getname(full=True))

        can_switch_teams = len(self.lobby.sessionteams) > 1

        # Flash as we're coming in.
        fin_color = babase.safecolor(self.get_color()) + (1,)
        if not self._inited:
            animate_array(
                self._text_node,
                'color',
                4,
                {0.15: fin_color, 0.25: (2, 2, 2, 1), 0.35: fin_color},
            )
        else:
            # Blend if we're in teams mode; switch instantly otherwise.
            if can_switch_teams:
                animate_array(
                    self._text_node,
                    'color',
                    4,
                    {0: self._text_node.color, 0.1: fin_color},
                )
            else:
                self._text_node.color = fin_color

        self._text_node.text = text

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
        assert babase.app.classic is not None
        if self._profilenames[self._profileindex] == '_edit':
            tex = _bascenev1.gettexture('black')
            tint_tex = _bascenev1.gettexture('black')
            self.icon.color = (1, 1, 1)
            self.icon.texture = tex
            self.icon.tint_texture = tint_tex
            self.icon.tint_color = (0, 1, 0)
            return

        try:
            tex_name = babase.app.classic.spaz_appearances[
                self._character_names[self._character_index]
            ].icon_texture
            tint_tex_name = babase.app.classic.spaz_appearances[
                self._character_names[self._character_index]
            ].icon_mask_texture
        except Exception:
            logging.exception('Error updating char icon list')
            tex_name = 'neoSpazIcon'
            tint_tex_name = 'neoSpazIconColorMask'

        tex = _bascenev1.gettexture(tex_name)
        tint_tex = _bascenev1.gettexture(tint_tex_name)

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
        self._sessionplayer.set_icon_info(tex_name, tint_tex_name, clr, clr2)


class Lobby:
    """Container for baclassic.Choosers.

    Category: Gameplay Classes
    """

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

        # Grab available profiles.
        self.reload_profiles()

        self._join_info_text = None

    @property
    def next_add_team(self) -> int:
        """(internal)"""
        return self._next_add_team

    @property
    def use_team_colors(self) -> bool:
        """A bool for whether this lobby is using team colors.

        If False, inidividual player colors are used instead.
        """
        return self._use_team_colors

    @property
    def sessionteams(self) -> list[bascenev1.SessionTeam]:
        """bascenev1.SessionTeams available in this lobby."""
        allteams = []
        for tref in self._sessionteams:
            team = tref()
            assert team is not None
            allteams.append(team)
        return allteams

    def get_choosers(self) -> list[Chooser]:
        """Return the lobby's current choosers."""
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
                # change-commands/etc coming in still for it;
                # want to avoid duplicate player-adds/etc.
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
