# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Implements lobby system for gathering before games, char select, etc."""

from __future__ import annotations

import weakref
from dataclasses import dataclass
from typing import TYPE_CHECKING

import _ba
from ba._error import print_exception, print_error, NotFoundError
from ba._gameutils import animate, animate_array
from ba._lang import Lstr
from ba._enums import SpecialChar, InputType
from ba._profile import get_player_profile_colors

if TYPE_CHECKING:
    from typing import Optional, List, Dict, Any, Sequence, Union
    import ba

MAX_QUICK_CHANGE_COUNT = 30
QUICK_CHANGE_INTERVAL = 0.05
QUICK_CHANGE_RESET_INTERVAL = 1.0


# Hmm should we move this to actors?..
class JoinInfo:
    """Display useful info for joiners."""

    def __init__(self, lobby: ba.Lobby):
        from ba._nodeactor import NodeActor
        from ba._general import WeakCall
        self._state = 0
        self._press_to_punch: Union[str, ba.Lstr] = _ba.charstr(
            SpecialChar.LEFT_BUTTON)
        self._press_to_bomb: Union[str, ba.Lstr] = _ba.charstr(
            SpecialChar.RIGHT_BUTTON)
        self._joinmsg = Lstr(resource='pressAnyButtonToJoinText')
        can_switch_teams = (len(lobby.sessionteams) > 1)

        # If we have a keyboard, grab keys for punch and pickup.
        # FIXME: This of course is only correct on the local device;
        #  Should change this for net games.
        keyboard = _ba.getinputdevice('Keyboard', '#1', doraise=False)
        if keyboard is not None:
            self._update_for_keyboard(keyboard)

        flatness = 1.0 if _ba.app.vr_mode else 0.0
        self._text = NodeActor(
            _ba.newnode('text',
                        attrs={
                            'position': (0, -40),
                            'h_attach': 'center',
                            'v_attach': 'top',
                            'h_align': 'center',
                            'color': (0.7, 0.7, 0.95, 1.0),
                            'flatness': flatness,
                            'text': self._joinmsg
                        }))

        if _ba.app.kiosk_mode:
            self._messages = [self._joinmsg]
        else:
            msg1 = Lstr(resource='pressToSelectProfileText',
                        subs=[
                            ('${BUTTONS}', _ba.charstr(SpecialChar.UP_ARROW) +
                             ' ' + _ba.charstr(SpecialChar.DOWN_ARROW))
                        ])
            msg2 = Lstr(resource='pressToOverrideCharacterText',
                        subs=[('${BUTTONS}', Lstr(resource='bombBoldText'))])
            msg3 = Lstr(value='${A} < ${B} >',
                        subs=[('${A}', msg2), ('${B}', self._press_to_bomb)])
            self._messages = (([
                Lstr(
                    resource='pressToSelectTeamText',
                    subs=[('${BUTTONS}', _ba.charstr(SpecialChar.LEFT_ARROW) +
                           ' ' + _ba.charstr(SpecialChar.RIGHT_ARROW))],
                )
            ] if can_switch_teams else []) + [msg1] + [msg3] + [self._joinmsg])

        self._timer = _ba.Timer(4.0, WeakCall(self._update), repeat=True)

    def _update_for_keyboard(self, keyboard: ba.InputDevice) -> None:
        from ba import _input
        punch_key = keyboard.get_button_name(
            _input.get_device_value(keyboard, 'buttonPunch'))
        self._press_to_punch = Lstr(resource='orText',
                                    subs=[('${A}',
                                           Lstr(value='\'${K}\'',
                                                subs=[('${K}', punch_key)])),
                                          ('${B}', self._press_to_punch)])
        bomb_key = keyboard.get_button_name(
            _input.get_device_value(keyboard, 'buttonBomb'))
        self._press_to_bomb = Lstr(resource='orText',
                                   subs=[('${A}',
                                          Lstr(value='\'${K}\'',
                                               subs=[('${K}', bomb_key)])),
                                         ('${B}', self._press_to_bomb)])
        self._joinmsg = Lstr(value='${A} < ${B} >',
                             subs=[('${A}',
                                    Lstr(resource='pressPunchToJoinText')),
                                   ('${B}', self._press_to_punch)])

    def _update(self) -> None:
        assert self._text.node
        self._text.node.text = self._messages[self._state]
        self._state = (self._state + 1) % len(self._messages)


@dataclass
class PlayerReadyMessage:
    """Tells an object a player has been selected from the given chooser."""
    chooser: ba.Chooser


@dataclass
class ChangeMessage:
    """Tells an object that a selection is being changed."""
    what: str
    value: int


class Chooser:
    """A character/team selector for a ba.Player.

    Category: Gameplay Classes
    """

    def __del__(self) -> None:

        # Just kill off our base node; the rest should go down with it.
        if self._text_node:
            self._text_node.delete()

    def __init__(self, vpos: float, sessionplayer: _ba.SessionPlayer,
                 lobby: 'Lobby') -> None:
        self._deek_sound = _ba.getsound('deek')
        self._click_sound = _ba.getsound('click01')
        self._punchsound = _ba.getsound('punch01')
        self._swish_sound = _ba.getsound('punchSwish')
        self._errorsound = _ba.getsound('error')
        self._mask_texture = _ba.gettexture('characterIconMask')
        self._vpos = vpos
        self._lobby = weakref.ref(lobby)
        self._sessionplayer = sessionplayer
        self._inited = False
        self._dead = False
        self._text_node: Optional[ba.Node] = None
        self._profilename = ''
        self._profilenames: List[str] = []
        self._ready: bool = False
        self._character_names: List[str] = []
        self._last_change: Sequence[Union[float, int]] = (0, 0)
        self._profiles: Dict[str, Dict[str, Any]] = {}

        app = _ba.app

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
        self._random_color, self._random_highlight = (
            get_player_profile_colors(None))

        # To calc our random character we pick a random one out of our
        # unlocked list and then locate that character's index in the full
        # list.
        char_index_offset = app.lobby_random_char_index_offset
        self._random_character_index = (
            (sessionplayer.inputdevice.id + char_index_offset) %
            len(self._character_names))

        # Attempt to set an initial profile based on what was used previously
        # for this input-device, etc.
        self._profileindex = self._select_initial_profile()
        self._profilename = self._profilenames[self._profileindex]

        self._text_node = _ba.newnode('text',
                                      delegate=self,
                                      attrs={
                                          'position': (-100, self._vpos),
                                          'maxwidth': 160,
                                          'shadow': 0.5,
                                          'vr_depth': -20,
                                          'h_align': 'left',
                                          'v_align': 'center',
                                          'v_attach': 'top'
                                      })
        animate(self._text_node, 'scale', {0: 0, 0.1: 1.0})
        self.icon = _ba.newnode('image',
                                owner=self._text_node,
                                attrs={
                                    'position': (-130, self._vpos + 20),
                                    'mask_texture': self._mask_texture,
                                    'vr_depth': -10,
                                    'attach': 'topCenter'
                                })

        animate_array(self.icon, 'scale', 2, {0: (0, 0), 0.1: (45, 45)})

        # Set our initial name to '<choosing player>' in case anyone asks.
        self._sessionplayer.setname(
            Lstr(resource='choosingPlayerText').evaluate(), real=False)

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
        app = _ba.app
        profilenames = self._profilenames
        inputdevice = self._sessionplayer.inputdevice

        # If we've got a set profile name for this device, work backwards
        # from that to get our index.
        dprofilename = (app.config.get('Default Player Profiles',
                                       {}).get(inputdevice.name + ' ' +
                                               inputdevice.unique_identifier))
        if dprofilename is not None and dprofilename in profilenames:
            # If we got '__account__' and its local and we haven't marked
            # anyone as the 'account profile' device yet, mark this guy as
            # it. (prevents the next joiner from getting the account
            # profile too).
            if (dprofilename == '__account__'
                    and not inputdevice.is_remote_client
                    and app.lobby_account_profile_device_id is None):
                app.lobby_account_profile_device_id = inputdevice.id
            return profilenames.index(dprofilename)

        # We want to mark the first local input-device in the game
        # as the 'account profile' device.
        if (not inputdevice.is_remote_client
                and not inputdevice.is_controller_app):
            if (app.lobby_account_profile_device_id is None
                    and '__account__' in profilenames):
                app.lobby_account_profile_device_id = inputdevice.id

        # If this is the designated account-profile-device, try to default
        # to the account profile.
        if (inputdevice.id == app.lobby_account_profile_device_id
                and '__account__' in profilenames):
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
        while (app.lobby_random_profile_index < len(profilenames)
               and profilenames[app.lobby_random_profile_index]
               in ('_random', '__account__', '_edit')):
            app.lobby_random_profile_index += 1
        if app.lobby_random_profile_index < len(profilenames):
            profileindex = app.lobby_random_profile_index
            app.lobby_random_profile_index += 1
            return profileindex
        assert '_random' in profilenames
        return profilenames.index('_random')

    @property
    def sessionplayer(self) -> ba.SessionPlayer:
        """The ba.SessionPlayer associated with this chooser."""
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
    def sessionteam(self) -> ba.SessionTeam:
        """Return this chooser's currently selected ba.SessionTeam."""
        return self.lobby.sessionteams[self._selected_team_index]

    @property
    def lobby(self) -> ba.Lobby:
        """The chooser's ba.Lobby."""
        lobby = self._lobby()
        if lobby is None:
            raise NotFoundError('Lobby does not exist.')
        return lobby

    def get_lobby(self) -> Optional[ba.Lobby]:
        """Return this chooser's lobby if it still exists; otherwise None."""
        return self._lobby()

    def update_from_profile(self) -> None:
        """Set character/colors based on the current profile."""
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
            if (character not in self._character_names
                    and character in _ba.app.spaz_appearances):
                self._character_names.append(character)
            self._character_index = self._character_names.index(character)
            self._color, self._highlight = (get_player_profile_colors(
                self._profilename, profiles=self._profiles))
        self._update_icon()
        self._update_text()

    def reload_profiles(self) -> None:
        """Reload all player profiles."""
        from ba._general import json_prep
        app = _ba.app

        # Re-construct our profile index and other stuff since the profile
        # list might have changed.
        input_device = self._sessionplayer.inputdevice
        is_remote = input_device.is_remote_client
        is_test_input = input_device.name.startswith('TestInput')

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
        self._profiles = json_prep(self._profiles)

        # Filter out any characters we're unaware of.
        for profile in list(self._profiles.items()):
            if profile[1].get('character', '') not in app.spaz_appearances:
                profile[1]['character'] = 'Spaz'

        # Add in a random one so we're ok even if there's no user profiles.
        self._profiles['_random'] = {}

        # In kiosk mode we disable account profiles to force random.
        if app.kiosk_mode:
            if '__account__' in self._profiles:
                del self._profiles['__account__']

        # For local devices, add it an 'edit' option which will pop up
        # the profile window.
        if not is_remote and not is_test_input and not app.kiosk_mode:
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
        offs = (spacing * -0.5 * len(sessionteams) +
                spacing * self._selected_team_index + 250)
        if len(sessionteams) > 1:
            offs -= 35
        animate_array(self._text_node, 'position', 2, {
            0: self._text_node.position,
            0.1: (-100 + offs, self._vpos + 23)
        })
        animate_array(self.icon, 'position', 2, {
            0: self.icon.position,
            0.1: (-130 + offs, self._vpos + 22)
        })

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
                name = (
                    self._sessionplayer.inputdevice.get_default_player_name())
            except Exception:
                print_exception('Error getting _random chooser name.')
                name = 'Invalid'
            clamp = not full
        elif name == '__account__':
            try:
                name = self._sessionplayer.inputdevice.get_account_name(full)
            except Exception:
                print_exception('Error getting account name for chooser.')
                name = 'Invalid'
            clamp = not full
        elif name == '_edit':
            # Explicitly flattening this to a str; it's only relevant on
            # the host so that's ok.
            name = (Lstr(
                resource='createEditPlayerText',
                fallback_resource='editProfileWindow.titleNewText').evaluate())
        else:
            # If we have a regular profile marked as global with an icon,
            # use it (for full only).
            if full:
                try:
                    if self._profiles[name_raw].get('global', False):
                        icon = (self._profiles[name_raw]['icon']
                                if 'icon' in self._profiles[name_raw] else
                                _ba.charstr(SpecialChar.LOGO))
                        name = icon + name
                except Exception:
                    print_exception('Error applying global icon.')
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
        from bastd.ui.profile import browser as pbrowser
        from ba._general import Call
        profilename = self._profilenames[self._profileindex]

        # Handle '_edit' as a special case.
        if profilename == '_edit' and ready:
            with _ba.Context('ui'):
                pbrowser.ProfileBrowserWindow(in_main_menu=False)

                # Give their input-device UI ownership too
                # (prevent someone else from snatching it in crowded games)
                _ba.set_ui_input_device(self._sessionplayer.inputdevice)
            return

        if not ready:
            self._sessionplayer.assigninput(
                InputType.LEFT_PRESS,
                Call(self.handlemessage, ChangeMessage('team', -1)))
            self._sessionplayer.assigninput(
                InputType.RIGHT_PRESS,
                Call(self.handlemessage, ChangeMessage('team', 1)))
            self._sessionplayer.assigninput(
                InputType.BOMB_PRESS,
                Call(self.handlemessage, ChangeMessage('character', 1)))
            self._sessionplayer.assigninput(
                InputType.UP_PRESS,
                Call(self.handlemessage, ChangeMessage('profileindex', -1)))
            self._sessionplayer.assigninput(
                InputType.DOWN_PRESS,
                Call(self.handlemessage, ChangeMessage('profileindex', 1)))
            self._sessionplayer.assigninput(
                (InputType.JUMP_PRESS, InputType.PICK_UP_PRESS,
                 InputType.PUNCH_PRESS),
                Call(self.handlemessage, ChangeMessage('ready', 1)))
            self._ready = False
            self._update_text()
            self._sessionplayer.setname('untitled', real=False)
        else:
            self._sessionplayer.assigninput(
                (InputType.LEFT_PRESS, InputType.RIGHT_PRESS,
                 InputType.UP_PRESS, InputType.DOWN_PRESS,
                 InputType.JUMP_PRESS, InputType.BOMB_PRESS,
                 InputType.PICK_UP_PRESS), self._do_nothing)
            self._sessionplayer.assigninput(
                (InputType.JUMP_PRESS, InputType.BOMB_PRESS,
                 InputType.PICK_UP_PRESS, InputType.PUNCH_PRESS),
                Call(self.handlemessage, ChangeMessage('ready', 0)))

            # Store the last profile picked by this input for reuse.
            input_device = self._sessionplayer.inputdevice
            name = input_device.name
            unique_id = input_device.unique_identifier
            device_profiles = _ba.app.config.setdefault(
                'Default Player Profiles', {})

            # Make an exception if we have no custom profiles and are set
            # to random; in that case we'll want to start picking up custom
            # profiles if/when one is made so keep our setting cleared.
            special = ('_random', '_edit', '__account__')
            have_custom_profiles = any(p not in special
                                       for p in self._profiles)

            profilekey = name + ' ' + unique_id
            if profilename == '_random' and not have_custom_profiles:
                if profilekey in device_profiles:
                    del device_profiles[profilekey]
            else:
                device_profiles[profilekey] = profilename
            _ba.app.config.commit()

            # Set this player's short and full name.
            self._sessionplayer.setname(self._getname(),
                                        self._getname(full=True),
                                        real=True)
            self._ready = True
            self._update_text()

            # Inform the session that this player is ready.
            _ba.getsession().handlemessage(PlayerReadyMessage(self))

    def _handle_ready_msg(self, ready: bool) -> None:
        force_team_switch = False

        # Team auto-balance kicks us to another team if we try to
        # join the team with the most players.
        if not self._ready:
            if _ba.app.config.get('Auto Balance Teams', False):
                lobby = self.lobby
                sessionteams = lobby.sessionteams
                if len(sessionteams) > 1:

                    # First, calc how many players are on each team
                    # ..we need to count both active players and
                    # choosers that have been marked as ready.
                    team_player_counts = {}
                    for sessionteam in sessionteams:
                        team_player_counts[sessionteam.id] = len(
                            sessionteam.players)
                    for chooser in lobby.choosers:
                        if chooser.ready:
                            team_player_counts[chooser.sessionteam.id] += 1
                    largest_team_size = max(team_player_counts.values())
                    smallest_team_size = (min(team_player_counts.values()))

                    # Force switch if we're on the biggest sessionteam
                    # and there's a smaller one available.
                    if (largest_team_size != smallest_team_size
                            and team_player_counts[self.sessionteam.id] >=
                            largest_team_size):
                        force_team_switch = True

        # Either force switch teams, or actually for realsies do the set-ready.
        if force_team_switch:
            _ba.playsound(self._errorsound)
            self.handlemessage(ChangeMessage('team', 1))
        else:
            _ba.playsound(self._punchsound)
            self._set_ready(ready)

    # TODO: should handle this at the engine layer so this is unnecessary.
    def _handle_repeat_message_attack(self) -> None:
        now = _ba.time()
        count = self._last_change[1]
        if now - self._last_change[0] < QUICK_CHANGE_INTERVAL:
            count += 1
            if count > MAX_QUICK_CHANGE_COUNT:
                _ba.disconnect_client(
                    self._sessionplayer.inputdevice.client_id)
        elif now - self._last_change[0] > QUICK_CHANGE_RESET_INTERVAL:
            count = 0
        self._last_change = (now, count)

    def handlemessage(self, msg: Any) -> Any:
        """Standard generic message handler."""

        if isinstance(msg, ChangeMessage):
            self._handle_repeat_message_attack()

            # If we've been removed from the lobby, ignore this stuff.
            if self._dead:
                print_error('chooser got ChangeMessage after dying')
                return

            if not self._text_node:
                print_error('got ChangeMessage after nodes died')
                return

            if msg.what == 'team':
                sessionteams = self.lobby.sessionteams
                if len(sessionteams) > 1:
                    _ba.playsound(self._swish_sound)
                self._selected_team_index = (
                    (self._selected_team_index + msg.value) %
                    len(sessionteams))
                self._update_text()
                self.update_position()
                self._update_icon()

            elif msg.what == 'profileindex':
                if len(self._profilenames) == 1:

                    # This should be pretty hard to hit now with
                    # automatic local accounts.
                    _ba.playsound(_ba.getsound('error'))
                else:

                    # Pick the next player profile and assign our name
                    # and character based on that.
                    _ba.playsound(self._deek_sound)
                    self._profileindex = ((self._profileindex + msg.value) %
                                          len(self._profilenames))
                    self.update_from_profile()

            elif msg.what == 'character':
                _ba.playsound(self._click_sound)
                # update our index in our local list of characters
                self._character_index = ((self._character_index + msg.value) %
                                         len(self._character_names))
                self._update_text()
                self._update_icon()

            elif msg.what == 'ready':
                self._handle_ready_msg(bool(msg.value))

    def _update_text(self) -> None:
        assert self._text_node is not None
        if self._ready:

            # Once we're ready, we've saved the name, so lets ask the system
            # for it so we get appended numbers and stuff.
            text = Lstr(value=self._sessionplayer.getname(full=True))
            text = Lstr(value='${A} (${B})',
                        subs=[('${A}', text),
                              ('${B}', Lstr(resource='readyText'))])
        else:
            text = Lstr(value=self._getname(full=True))

        can_switch_teams = len(self.lobby.sessionteams) > 1

        # Flash as we're coming in.
        fin_color = _ba.safecolor(self.get_color()) + (1, )
        if not self._inited:
            animate_array(self._text_node, 'color', 4, {
                0.15: fin_color,
                0.25: (2, 2, 2, 1),
                0.35: fin_color
            })
        else:

            # Blend if we're in teams mode; switch instantly otherwise.
            if can_switch_teams:
                animate_array(self._text_node, 'color', 4, {
                    0: self._text_node.color,
                    0.1: fin_color
                })
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
                    our_second_biggest = max(highlight[(max_index + 1) % 3],
                                             highlight[(max_index + 2) % 3])
                    diff = (that_color_for_us - our_second_biggest)
                    if diff > 0:
                        highlight[max_index] -= diff * 0.6
                        highlight[(max_index + 1) % 3] += diff * 0.3
                        highlight[(max_index + 2) % 3] += diff * 0.2
        return highlight

    def getplayer(self) -> ba.SessionPlayer:
        """Return the player associated with this chooser."""
        return self._sessionplayer

    def _update_icon(self) -> None:
        if self._profilenames[self._profileindex] == '_edit':
            tex = _ba.gettexture('black')
            tint_tex = _ba.gettexture('black')
            self.icon.color = (1, 1, 1)
            self.icon.texture = tex
            self.icon.tint_texture = tint_tex
            self.icon.tint_color = (0, 1, 0)
            return

        try:
            tex_name = (_ba.app.spaz_appearances[self._character_names[
                self._character_index]].icon_texture)
            tint_tex_name = (_ba.app.spaz_appearances[self._character_names[
                self._character_index]].icon_mask_texture)
        except Exception:
            print_exception('Error updating char icon list')
            tex_name = 'neoSpazIcon'
            tint_tex_name = 'neoSpazIconColorMask'

        tex = _ba.gettexture(tex_name)
        tint_tex = _ba.gettexture(tint_tex_name)

        self.icon.color = (1, 1, 1)
        self.icon.texture = tex
        self.icon.tint_texture = tint_tex
        clr = self.get_color()
        clr2 = self.get_highlight()

        can_switch_teams = len(self.lobby.sessionteams) > 1

        # If we're initing, flash.
        if not self._inited:
            animate_array(self.icon, 'color', 3, {
                0.15: (1, 1, 1),
                0.25: (2, 2, 2),
                0.35: (1, 1, 1)
            })

        # Blend in teams mode; switch instantly in ffa-mode.
        if can_switch_teams:
            animate_array(self.icon, 'tint_color', 3, {
                0: self.icon.tint_color,
                0.1: clr
            })
        else:
            self.icon.tint_color = clr
        self.icon.tint2_color = clr2

        # Store the icon info the the player.
        self._sessionplayer.set_icon_info(tex_name, tint_tex_name, clr, clr2)


class Lobby:
    """Container for ba.Choosers.

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
        from ba._team import SessionTeam
        from ba._coopsession import CoopSession
        session = _ba.getsession()
        self._use_team_colors = session.use_team_colors
        if session.use_teams:
            self._sessionteams = [
                weakref.ref(team) for team in session.sessionteams
            ]
        else:
            self._dummy_teams = SessionTeam()
            self._sessionteams = [weakref.ref(self._dummy_teams)]
        v_offset = (-150 if isinstance(session, CoopSession) else -50)
        self.choosers: List[Chooser] = []
        self.base_v_offset = v_offset
        self.update_positions()
        self._next_add_team = 0
        self.character_names_local_unlocked: List[str] = []
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
    def sessionteams(self) -> List[ba.SessionTeam]:
        """ba.SessionTeams available in this lobby."""
        allteams = []
        for tref in self._sessionteams:
            team = tref()
            assert team is not None
            allteams.append(team)
        return allteams

    def get_choosers(self) -> List[Chooser]:
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
        from ba._account import ensure_have_account_player_profile
        from bastd.actor.spazappearance import get_appearances

        # We may have gained or lost character names if the user
        # bought something; reload these too.
        self.character_names_local_unlocked = get_appearances()
        self.character_names_local_unlocked.sort(key=lambda x: x.lower())

        # Do any overall prep we need to such as creating account profile.
        ensure_have_account_player_profile()
        for chooser in self.choosers:
            try:
                chooser.reload_profiles()
                chooser.update_from_profile()
            except Exception:
                print_exception('Error reloading profiles.')

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

    def add_chooser(self, sessionplayer: ba.SessionPlayer) -> None:
        """Add a chooser to the lobby for the provided player."""
        self.choosers.append(
            Chooser(vpos=self._vpos, sessionplayer=sessionplayer, lobby=self))
        self._next_add_team = (self._next_add_team + 1) % len(
            self._sessionteams)
        self._vpos -= 48

    def remove_chooser(self, player: ba.SessionPlayer) -> None:
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
            print_error(f'remove_chooser did not find player {player}')
        elif chooser in self.choosers:
            print_error(f'chooser remains after removal for {player}')
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
