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
"""UI for player profile upgrades."""

from __future__ import annotations

import time
import weakref
from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Any, Optional, Dict
    from bastd.ui.profile.edit import EditProfileWindow


class ProfileUpgradeWindow(ba.Window):
    """Window for player profile upgrades to global."""

    def __init__(self,
                 edit_profile_window: EditProfileWindow,
                 transition: str = 'in_right'):
        from ba.internal import master_server_get
        self._r = 'editProfileWindow'

        self._width = 680
        self._height = 350
        uiscale = ba.app.ui.uiscale
        self._base_scale = (2.05 if uiscale is ba.UIScale.SMALL else
                            1.5 if uiscale is ba.UIScale.MEDIUM else 1.2)
        self._upgrade_start_time: Optional[float] = None
        self._name = edit_profile_window.getname()
        self._edit_profile_window = weakref.ref(edit_profile_window)

        top_extra = 15 if uiscale is ba.UIScale.SMALL else 15
        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height + top_extra),
            toolbar_visibility='menu_currency',
            transition=transition,
            scale=self._base_scale,
            stack_offset=(0, 15) if uiscale is ba.UIScale.SMALL else (0, 0)))
        cancel_button = ba.buttonwidget(parent=self._root_widget,
                                        position=(52, 30),
                                        size=(155, 60),
                                        scale=0.8,
                                        autoselect=True,
                                        label=ba.Lstr(resource='cancelText'),
                                        on_activate_call=self._cancel)
        self._upgrade_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(self._width - 190, 30),
            size=(155, 60),
            scale=0.8,
            autoselect=True,
            label=ba.Lstr(resource='upgradeText'),
            on_activate_call=self._on_upgrade_press)
        ba.containerwidget(edit=self._root_widget,
                           cancel_button=cancel_button,
                           start_button=self._upgrade_button,
                           selected_child=self._upgrade_button)

        ba.textwidget(parent=self._root_widget,
                      position=(self._width * 0.5, self._height - 38),
                      size=(0, 0),
                      text=ba.Lstr(resource=self._r +
                                   '.upgradeToGlobalProfileText'),
                      color=ba.app.ui.title_color,
                      maxwidth=self._width * 0.45,
                      scale=1.0,
                      h_align='center',
                      v_align='center')

        ba.textwidget(parent=self._root_widget,
                      position=(self._width * 0.5, self._height - 100),
                      size=(0, 0),
                      text=ba.Lstr(resource=self._r +
                                   '.upgradeProfileInfoText'),
                      color=ba.app.ui.infotextcolor,
                      maxwidth=self._width * 0.8,
                      scale=0.7,
                      h_align='center',
                      v_align='center')

        self._status_text = ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 160),
            size=(0, 0),
            text=ba.Lstr(resource=self._r + '.checkingAvailabilityText',
                         subs=[('${NAME}', self._name)]),
            color=(0.8, 0.4, 0.0),
            maxwidth=self._width * 0.8,
            scale=0.65,
            h_align='center',
            v_align='center')

        self._price_text = ba.textwidget(parent=self._root_widget,
                                         position=(self._width * 0.5,
                                                   self._height - 230),
                                         size=(0, 0),
                                         text='',
                                         color=(0.2, 1, 0.2),
                                         maxwidth=self._width * 0.8,
                                         scale=1.5,
                                         h_align='center',
                                         v_align='center')

        self._tickets_text: Optional[ba.Widget]
        if not ba.app.ui.use_toolbars:
            self._tickets_text = ba.textwidget(
                parent=self._root_widget,
                position=(self._width * 0.9 - 5, self._height - 30),
                size=(0, 0),
                text=ba.charstr(ba.SpecialChar.TICKET) + '123',
                color=(0.2, 1, 0.2),
                maxwidth=100,
                scale=0.5,
                h_align='right',
                v_align='center')
        else:
            self._tickets_text = None

        master_server_get('bsGlobalProfileCheck', {
            'name': self._name,
            'b': ba.app.build_number
        },
                          callback=ba.WeakCall(self._profile_check_result))
        self._cost = _ba.get_account_misc_read_val('price.global_profile', 500)
        self._status: Optional[str] = 'waiting'
        self._update_timer = ba.Timer(1.0,
                                      ba.WeakCall(self._update),
                                      timetype=ba.TimeType.REAL,
                                      repeat=True)
        self._update()

    def _profile_check_result(self, result: Optional[Dict[str, Any]]) -> None:
        if result is None:
            ba.textwidget(
                edit=self._status_text,
                text=ba.Lstr(resource='internal.unavailableNoConnectionText'),
                color=(1, 0, 0))
            self._status = 'error'
            ba.buttonwidget(edit=self._upgrade_button,
                            color=(0.4, 0.4, 0.4),
                            textcolor=(0.5, 0.5, 0.5))
        else:
            if result['available']:
                ba.textwidget(edit=self._status_text,
                              text=ba.Lstr(resource=self._r + '.availableText',
                                           subs=[('${NAME}', self._name)]),
                              color=(0, 1, 0))
                ba.textwidget(edit=self._price_text,
                              text=ba.charstr(ba.SpecialChar.TICKET) +
                              str(self._cost))
                self._status = None
            else:
                ba.textwidget(edit=self._status_text,
                              text=ba.Lstr(resource=self._r +
                                           '.unavailableText',
                                           subs=[('${NAME}', self._name)]),
                              color=(1, 0, 0))
                self._status = 'unavailable'
                ba.buttonwidget(edit=self._upgrade_button,
                                color=(0.4, 0.4, 0.4),
                                textcolor=(0.5, 0.5, 0.5))

    def _on_upgrade_press(self) -> None:
        from bastd.ui import getcurrency
        if self._status is None:
            # If it appears we don't have enough tickets, offer to buy more.
            tickets = _ba.get_account_ticket_count()
            if tickets < self._cost:
                ba.playsound(ba.getsound('error'))
                getcurrency.show_get_tickets_prompt()
                return
            ba.screenmessage(ba.Lstr(resource='purchasingText'),
                             color=(0, 1, 0))
            self._status = 'pre_upgrading'

            # Now we tell the original editor to save the profile, add an
            # upgrade transaction, and then sit and wait for everything to
            # go through.
            edit_profile_window = self._edit_profile_window()
            if edit_profile_window is None:
                print('profile upgrade: original edit window gone')
                return
            success = edit_profile_window.save(transition_out=False)
            if not success:
                print('profile upgrade: error occurred saving profile')
                ba.screenmessage(ba.Lstr(resource='errorText'),
                                 color=(1, 0, 0))
                ba.playsound(ba.getsound('error'))
                return
            _ba.add_transaction({
                'type': 'UPGRADE_PROFILE',
                'name': self._name
            })
            _ba.run_transactions()
            self._status = 'upgrading'
            self._upgrade_start_time = time.time()
        else:
            ba.playsound(ba.getsound('error'))

    def _update(self) -> None:
        try:
            t_str = str(_ba.get_account_ticket_count())
        except Exception:
            t_str = '?'
        if self._tickets_text is not None:
            ba.textwidget(edit=self._tickets_text,
                          text=ba.Lstr(
                              resource='getTicketsWindow.youHaveShortText',
                              subs=[('${COUNT}',
                                     ba.charstr(ba.SpecialChar.TICKET) + t_str)
                                    ]))

        # Once we've kicked off an upgrade attempt and all transactions go
        # through, we're done.
        if (self._status == 'upgrading'
                and not _ba.have_outstanding_transactions()):
            self._status = 'exiting'
            ba.containerwidget(edit=self._root_widget, transition='out_right')
            edit_profile_window = self._edit_profile_window()
            if edit_profile_window is None:
                print('profile upgrade transition out:'
                      ' original edit window gone')
                return
            ba.playsound(ba.getsound('gunCocking'))
            edit_profile_window.reload_window()

    def _cancel(self) -> None:
        # If we recently sent out an upgrade request, disallow canceling
        # for a bit.
        if (self._upgrade_start_time is not None
                and time.time() - self._upgrade_start_time < 10.0):
            ba.playsound(ba.getsound('error'))
            return
        ba.containerwidget(edit=self._root_widget, transition='out_right')
