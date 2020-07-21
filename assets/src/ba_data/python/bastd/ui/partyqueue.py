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
"""UI related to waiting in line for a party."""

from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Any, Optional, Sequence, List, Dict


class PartyQueueWindow(ba.Window):
    """Window showing players waiting to join a server."""

    # ewww this needs quite a bit of de-linting if/when i revisit it..
    # pylint: disable=invalid-name
    # pylint: disable=consider-using-dict-comprehension
    class Dude:
        """Represents a single dude waiting in a server line."""

        def __init__(self, parent: PartyQueueWindow, distance: float,
                     initial_offset: float, is_player: bool, account_id: str,
                     name: str):
            self.claimed = False
            self._line_left = parent.get_line_left()
            self._line_width = parent.get_line_width()
            self._line_bottom = parent.get_line_bottom()
            self._target_distance = distance
            self._distance = distance + initial_offset
            self._boost_brightness = 0.0
            self._debug = False
            self._sc = sc = 1.1 if is_player else 0.6 + random.random() * 0.2
            self._y_offs = -30.0 if is_player else -47.0 * sc
            self._last_boost_time = 0.0
            self._color = (0.2, 1.0,
                           0.2) if is_player else (0.5 + 0.3 * random.random(),
                                                   0.4 + 0.2 * random.random(),
                                                   0.5 + 0.3 * random.random())
            self._eye_color = (0.7 * 1.0 + 0.3 * self._color[0],
                               0.7 * 1.0 + 0.3 * self._color[1],
                               0.7 * 1.0 + 0.3 * self._color[2])
            self._body_image = ba.buttonwidget(
                parent=parent.get_root_widget(),
                selectable=True,
                label='',
                size=(sc * 60, sc * 80),
                color=self._color,
                texture=parent.lineup_tex,
                model_transparent=parent.lineup_1_transparent_model)
            ba.buttonwidget(edit=self._body_image,
                            on_activate_call=ba.WeakCall(
                                parent.on_account_press, account_id,
                                self._body_image))
            ba.widget(edit=self._body_image, autoselect=True)
            self._eyes_image = ba.imagewidget(
                parent=parent.get_root_widget(),
                size=(sc * 36, sc * 18),
                texture=parent.lineup_tex,
                color=self._eye_color,
                model_transparent=parent.eyes_model)
            self._name_text = ba.textwidget(parent=parent.get_root_widget(),
                                            size=(0, 0),
                                            shadow=0,
                                            flatness=1.0,
                                            text=name,
                                            maxwidth=100,
                                            h_align='center',
                                            v_align='center',
                                            scale=0.75,
                                            color=(1, 1, 1, 0.6))
            self._update_image()

            # DEBUG: vis target pos..
            self._body_image_target: Optional[ba.Widget]
            self._eyes_image_target: Optional[ba.Widget]
            if self._debug:
                self._body_image_target = ba.imagewidget(
                    parent=parent.get_root_widget(),
                    size=(sc * 60, sc * 80),
                    color=self._color,
                    texture=parent.lineup_tex,
                    model_transparent=parent.lineup_1_transparent_model)
                self._eyes_image_target = ba.imagewidget(
                    parent=parent.get_root_widget(),
                    size=(sc * 36, sc * 18),
                    texture=parent.lineup_tex,
                    color=self._eye_color,
                    model_transparent=parent.eyes_model)
                # (updates our image positions)
                self.set_target_distance(self._target_distance)
            else:
                self._body_image_target = self._eyes_image_target = None

        def __del__(self) -> None:

            # ew.  our destructor here may get called as part of an internal
            # widget tear-down.
            # running further widget calls here can quietly break stuff, so we
            # need to push a deferred call to kill these as necessary instead.
            # (should bulletproof internal widget code to give a clean error
            # in this case)
            def kill_widgets(widgets: Sequence[Optional[ba.Widget]]) -> None:
                for widget in widgets:
                    if widget:
                        widget.delete()

            ba.pushcall(
                ba.Call(kill_widgets, [
                    self._body_image, self._eyes_image,
                    self._body_image_target, self._eyes_image_target,
                    self._name_text
                ]))

        def set_target_distance(self, dist: float) -> None:
            """Set distance for a dude."""
            self._target_distance = dist
            if self._debug:
                sc = self._sc
                position = (self._line_left + self._line_width *
                            (1.0 - self._target_distance),
                            self._line_bottom - 30)
                ba.imagewidget(edit=self._body_image_target,
                               position=(position[0] - sc * 30,
                                         position[1] - sc * 25 - 70))
                ba.imagewidget(edit=self._eyes_image_target,
                               position=(position[0] - sc * 18,
                                         position[1] + sc * 31 - 70))

        def step(self, smoothing: float) -> None:
            """Step this dude."""
            self._distance = (smoothing * self._distance +
                              (1.0 - smoothing) * self._target_distance)
            self._update_image()
            self._boost_brightness *= 0.9

        def _update_image(self) -> None:
            sc = self._sc
            position = (self._line_left + self._line_width *
                        (1.0 - self._distance), self._line_bottom + 40)
            brightness = 1.0 + self._boost_brightness
            ba.buttonwidget(edit=self._body_image,
                            position=(position[0] - sc * 30,
                                      position[1] - sc * 25 + self._y_offs),
                            color=(self._color[0] * brightness,
                                   self._color[1] * brightness,
                                   self._color[2] * brightness))
            ba.imagewidget(edit=self._eyes_image,
                           position=(position[0] - sc * 18,
                                     position[1] + sc * 31 + self._y_offs),
                           color=(self._eye_color[0] * brightness,
                                  self._eye_color[1] * brightness,
                                  self._eye_color[2] * brightness))
            ba.textwidget(edit=self._name_text,
                          position=(position[0] - sc * 0,
                                    position[1] + sc * 40.0))

        def boost(self, amount: float, smoothing: float) -> None:
            """Boost this dude."""
            del smoothing  # unused arg
            self._distance = max(0.0, self._distance - amount)
            self._update_image()
            self._last_boost_time = time.time()
            self._boost_brightness += 0.6

    def __init__(self, queue_id: str, address: str, port: int):
        ba.app.ui.have_party_queue_window = True
        self._address = address
        self._port = port
        self._queue_id = queue_id
        self._width = 800
        self._height = 400
        self._last_connect_attempt_time: Optional[float] = None
        self._last_transaction_time: Optional[float] = None
        self._boost_button: Optional[ba.Widget] = None
        self._boost_price: Optional[ba.Widget] = None
        self._boost_label: Optional[ba.Widget] = None
        self._field_shown = False
        self._dudes: List[PartyQueueWindow.Dude] = []
        self._dudes_by_id: Dict[int, PartyQueueWindow.Dude] = {}
        self._line_left = 40.0
        self._line_width = self._width - 190
        self._line_bottom = self._height * 0.4
        self.lineup_tex = ba.gettexture('playerLineup')
        self._smoothing = 0.0
        self._initial_offset = 0.0
        self._boost_tickets = 0
        self._boost_strength = 0.0
        self._angry_computer_transparent_model = ba.getmodel(
            'angryComputerTransparent')
        self._angry_computer_image: Optional[ba.Widget] = None
        self.lineup_1_transparent_model = ba.getmodel(
            'playerLineup1Transparent')
        self._lineup_2_transparent_model = ba.getmodel(
            'playerLineup2Transparent')
        self._lineup_3_transparent_model = ba.getmodel(
            'playerLineup3Transparent')
        self._lineup_4_transparent_model = ba.getmodel(
            'playerLineup4Transparent')
        self._line_image: Optional[ba.Widget] = None
        self.eyes_model = ba.getmodel('plasticEyesTransparent')
        self._white_tex = ba.gettexture('white')
        uiscale = ba.app.ui.uiscale
        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height),
            color=(0.45, 0.63, 0.15),
            transition='in_scale',
            scale=(1.4 if uiscale is ba.UIScale.SMALL else
                   1.2 if uiscale is ba.UIScale.MEDIUM else 1.0)))

        self._cancel_button = ba.buttonwidget(parent=self._root_widget,
                                              scale=1.0,
                                              position=(60, self._height - 80),
                                              size=(50, 50),
                                              label='',
                                              on_activate_call=self.close,
                                              autoselect=True,
                                              color=(0.45, 0.63, 0.15),
                                              icon=ba.gettexture('crossOut'),
                                              iconscale=1.2)
        ba.containerwidget(edit=self._root_widget,
                           cancel_button=self._cancel_button)

        self._title_text = ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.55),
            size=(0, 0),
            color=(1.0, 3.0, 1.0),
            scale=1.3,
            h_align='center',
            v_align='center',
            text=ba.Lstr(resource='internal.connectingToPartyText'),
            maxwidth=self._width * 0.65)

        self._tickets_text = ba.textwidget(parent=self._root_widget,
                                           position=(self._width - 180,
                                                     self._height - 20),
                                           size=(0, 0),
                                           color=(0.2, 1.0, 0.2),
                                           scale=0.7,
                                           h_align='center',
                                           v_align='center',
                                           text='')

        # update at roughly 30fps
        self._update_timer = ba.Timer(0.033,
                                      ba.WeakCall(self.update),
                                      repeat=True,
                                      timetype=ba.TimeType.REAL)
        self.update()

    def __del__(self) -> None:
        try:
            ba.app.ui.have_party_queue_window = False
            _ba.add_transaction({
                'type': 'PARTY_QUEUE_REMOVE',
                'q': self._queue_id
            })
            _ba.run_transactions()
        except Exception:
            ba.print_exception('Error removing self from party queue.')

    def get_line_left(self) -> float:
        """(internal)"""
        return self._line_left

    def get_line_width(self) -> float:
        """(internal)"""
        return self._line_width

    def get_line_bottom(self) -> float:
        """(internal)"""
        return self._line_bottom

    def on_account_press(self, account_id: Optional[str],
                         origin_widget: ba.Widget) -> None:
        """A dude was clicked so we should show his account info."""
        from bastd.ui.account import viewer
        if account_id is None:
            ba.playsound(ba.getsound('error'))
            return
        viewer.AccountViewerWindow(
            account_id=account_id,
            position=origin_widget.get_screen_space_center())

    def close(self) -> None:
        """Close the ui."""
        ba.containerwidget(edit=self._root_widget, transition='out_scale')

    def _update_field(self, response: Dict[str, Any]) -> None:
        if self._angry_computer_image is None:
            self._angry_computer_image = ba.imagewidget(
                parent=self._root_widget,
                position=(self._width - 180, self._height * 0.5 - 65),
                size=(150, 150),
                texture=self.lineup_tex,
                model_transparent=self._angry_computer_transparent_model)
        if self._line_image is None:
            self._line_image = ba.imagewidget(
                parent=self._root_widget,
                color=(0.0, 0.0, 0.0),
                opacity=0.2,
                position=(self._line_left, self._line_bottom - 2.0),
                size=(self._line_width, 4.0),
                texture=self._white_tex)

        # now go through the data they sent, creating dudes for us and our
        # enemies as needed and updating target positions on all of them..

        # mark all as unclaimed so we know which ones to kill off..
        for dude in self._dudes:
            dude.claimed = False

        # always have a dude for ourself..
        if -1 not in self._dudes_by_id:
            dude = self.Dude(
                self, response['d'], self._initial_offset, True,
                _ba.get_account_misc_read_val_2('resolvedAccountID', None),
                _ba.get_account_display_string())
            self._dudes_by_id[-1] = dude
            self._dudes.append(dude)
        else:
            self._dudes_by_id[-1].set_target_distance(response['d'])
        self._dudes_by_id[-1].claimed = True

        # now create/destroy enemies
        for (enemy_id, enemy_distance, enemy_account_id,
             enemy_name) in response['e']:
            if enemy_id not in self._dudes_by_id:
                dude = self.Dude(self, enemy_distance, self._initial_offset,
                                 False, enemy_account_id, enemy_name)
                self._dudes_by_id[enemy_id] = dude
                self._dudes.append(dude)
            else:
                self._dudes_by_id[enemy_id].set_target_distance(enemy_distance)
            self._dudes_by_id[enemy_id].claimed = True

        # remove unclaimed dudes from both of our lists
        self._dudes_by_id = dict([
            item for item in list(self._dudes_by_id.items()) if item[1].claimed
        ])
        self._dudes = [dude for dude in self._dudes if dude.claimed]

    def _hide_field(self) -> None:
        if self._angry_computer_image:
            self._angry_computer_image.delete()
        self._angry_computer_image = None
        if self._line_image:
            self._line_image.delete()
        self._line_image = None
        self._dudes = []
        self._dudes_by_id = {}

    def on_update_response(self, response: Optional[Dict[str, Any]]) -> None:
        """We've received a response from an update to the server."""
        # pylint: disable=too-many-branches
        if not self._root_widget:
            return

        # Seeing this in logs; debugging...
        if not self._title_text:
            print('PartyQueueWindows update: Have root but no title_text.')
            return

        if response is not None:
            should_show_field = (response.get('d') is not None)
            self._smoothing = response['s']
            self._initial_offset = response['o']

            # If they gave us a position, show the field.
            if should_show_field:
                ba.textwidget(edit=self._title_text,
                              text=ba.Lstr(resource='waitingInLineText'),
                              position=(self._width * 0.5,
                                        self._height * 0.85))
                self._update_field(response)
                self._field_shown = True
            if not should_show_field and self._field_shown:
                ba.textwidget(
                    edit=self._title_text,
                    text=ba.Lstr(resource='internal.connectingToPartyText'),
                    position=(self._width * 0.5, self._height * 0.55))
                self._hide_field()
                self._field_shown = False

            # if they told us there's a boost button, update..
            if response.get('bt') is not None:
                self._boost_tickets = response['bt']
                self._boost_strength = response['ba']
                if self._boost_button is None:
                    self._boost_button = ba.buttonwidget(
                        parent=self._root_widget,
                        scale=1.0,
                        position=(self._width * 0.5 - 75, 20),
                        size=(150, 100),
                        button_type='square',
                        label='',
                        on_activate_call=self.on_boost_press,
                        enable_sound=False,
                        color=(0, 1, 0),
                        autoselect=True)
                    self._boost_label = ba.textwidget(
                        parent=self._root_widget,
                        draw_controller=self._boost_button,
                        position=(self._width * 0.5, 88),
                        size=(0, 0),
                        color=(0.8, 1.0, 0.8),
                        scale=1.5,
                        h_align='center',
                        v_align='center',
                        text=ba.Lstr(resource='boostText'),
                        maxwidth=150)
                    self._boost_price = ba.textwidget(
                        parent=self._root_widget,
                        draw_controller=self._boost_button,
                        position=(self._width * 0.5, 50),
                        size=(0, 0),
                        color=(0, 1, 0),
                        scale=0.9,
                        h_align='center',
                        v_align='center',
                        text=ba.charstr(ba.SpecialChar.TICKET) +
                        str(self._boost_tickets),
                        maxwidth=150)
            else:
                if self._boost_button is not None:
                    self._boost_button.delete()
                    self._boost_button = None
                if self._boost_price is not None:
                    self._boost_price.delete()
                    self._boost_price = None
                if self._boost_label is not None:
                    self._boost_label.delete()
                    self._boost_label = None

            # if they told us to go ahead and try and connect, do so..
            # (note: servers will disconnect us if we try to connect before
            # getting this go-ahead, so don't get any bright ideas...)
            if response.get('c', False):
                # enforce a delay between connection attempts
                # (in case they're jamming on the boost button)
                now = time.time()
                if (self._last_connect_attempt_time is None
                        or now - self._last_connect_attempt_time > 10.0):
                    _ba.connect_to_party(address=self._address,
                                         port=self._port,
                                         print_progress=False)
                    self._last_connect_attempt_time = now

    def on_boost_press(self) -> None:
        """Boost was pressed."""
        from bastd.ui import account
        from bastd.ui import getcurrency
        if _ba.get_account_state() != 'signed_in':
            account.show_sign_in_prompt()
            return

        if _ba.get_account_ticket_count() < self._boost_tickets:
            ba.playsound(ba.getsound('error'))
            getcurrency.show_get_tickets_prompt()
            return

        ba.playsound(ba.getsound('laserReverse'))
        _ba.add_transaction(
            {
                'type': 'PARTY_QUEUE_BOOST',
                't': self._boost_tickets,
                'q': self._queue_id
            },
            callback=ba.WeakCall(self.on_update_response))
        # lets not run these immediately (since they may be rapid-fire,
        # just bucket them until the next tick)

        # the transaction handles the local ticket change, but we apply our
        # local boost vis manually here..
        # (our visualization isn't really wired up to be transaction-based)
        our_dude = self._dudes_by_id.get(-1)
        if our_dude is not None:
            our_dude.boost(self._boost_strength, self._smoothing)

    def update(self) -> None:
        """Update!"""
        if not self._root_widget:
            return

        # Update boost-price.
        if self._boost_price is not None:
            ba.textwidget(edit=self._boost_price,
                          text=ba.charstr(ba.SpecialChar.TICKET) +
                          str(self._boost_tickets))

        # Update boost button color based on if we have enough moola.
        if self._boost_button is not None:
            can_boost = (
                (_ba.get_account_state() == 'signed_in'
                 and _ba.get_account_ticket_count() >= self._boost_tickets))
            ba.buttonwidget(edit=self._boost_button,
                            color=(0, 1, 0) if can_boost else (0.7, 0.7, 0.7))

        # Update ticket-count.
        if self._tickets_text is not None:
            if self._boost_button is not None:
                if _ba.get_account_state() == 'signed_in':
                    val = ba.charstr(ba.SpecialChar.TICKET) + str(
                        _ba.get_account_ticket_count())
                else:
                    val = ba.charstr(ba.SpecialChar.TICKET) + '???'
                ba.textwidget(edit=self._tickets_text, text=val)
            else:
                ba.textwidget(edit=self._tickets_text, text='')

        current_time = ba.time(ba.TimeType.REAL)
        if (self._last_transaction_time is None
                or current_time - self._last_transaction_time >
                0.001 * _ba.get_account_misc_read_val('pqInt', 5000)):
            self._last_transaction_time = current_time
            _ba.add_transaction(
                {
                    'type': 'PARTY_QUEUE_QUERY',
                    'q': self._queue_id
                },
                callback=ba.WeakCall(self.on_update_response))
            _ba.run_transactions()

        # step our dudes
        for dude in self._dudes:
            dude.step(self._smoothing)
