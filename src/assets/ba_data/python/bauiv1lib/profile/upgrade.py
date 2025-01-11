# Released under the MIT License. See LICENSE for details.
#
"""UI for player profile upgrades."""

from __future__ import annotations

import time
import weakref
from typing import TYPE_CHECKING

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any

    from bauiv1lib.profile.edit import EditProfileWindow


class ProfileUpgradeWindow(bui.Window):
    """Window for player profile upgrades to global."""

    def __init__(
        self,
        edit_profile_window: EditProfileWindow,
        transition: str = 'in_right',
    ):
        if bui.app.classic is None:
            raise RuntimeError('This requires classic.')

        plus = bui.app.plus
        assert plus is not None

        self._r = 'editProfileWindow'

        uiscale = bui.app.ui_v1.uiscale
        self._width = 750 if uiscale is bui.UIScale.SMALL else 680
        self._height = 450 if uiscale is bui.UIScale.SMALL else 350
        assert bui.app.classic is not None
        self._base_scale = (
            1.9
            if uiscale is bui.UIScale.SMALL
            else 1.5 if uiscale is bui.UIScale.MEDIUM else 1.2
        )
        yoffs = -60.0 if uiscale is bui.UIScale.SMALL else 0
        self._upgrade_start_time: float | None = None
        self._name = edit_profile_window.getname()
        self._edit_profile_window = weakref.ref(edit_profile_window)

        top_extra = 15 if uiscale is bui.UIScale.SMALL else 15
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height + top_extra),
                toolbar_visibility='menu_store_no_back',
                transition=transition,
                scale=self._base_scale,
                stack_offset=(
                    (0, 0) if uiscale is bui.UIScale.SMALL else (0, 0)
                ),
            )
        )
        cancel_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(52, self._height - 290 + yoffs),
            size=(155, 60),
            scale=0.8,
            autoselect=True,
            label=bui.Lstr(resource='cancelText'),
            on_activate_call=self._cancel,
        )
        self._upgrade_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width - 190, self._height - 290 + yoffs),
            size=(155, 60),
            scale=0.8,
            autoselect=True,
            label=bui.Lstr(resource='upgradeText'),
            on_activate_call=self._on_upgrade_press,
        )
        bui.containerwidget(
            edit=self._root_widget,
            cancel_button=cancel_button,
            start_button=self._upgrade_button,
            selected_child=self._upgrade_button,
        )

        assert bui.app.classic is not None
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 38 + yoffs),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.upgradeToGlobalProfileText'),
            color=bui.app.ui_v1.title_color,
            maxwidth=self._width * 0.45,
            scale=1.0,
            h_align='center',
            v_align='center',
        )

        assert bui.app.classic is not None
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 100 + yoffs),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.upgradeProfileInfoText'),
            color=bui.app.ui_v1.infotextcolor,
            maxwidth=self._width * 0.8,
            scale=0.7,
            h_align='center',
            v_align='center',
        )

        self._status_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 160 + yoffs),
            size=(0, 0),
            text=bui.Lstr(
                resource=f'{self._r}.checkingAvailabilityText',
                subs=[('${NAME}', self._name)],
            ),
            color=(0.8, 0.4, 0.0),
            maxwidth=self._width * 0.8,
            scale=0.65,
            h_align='center',
            v_align='center',
        )

        self._price_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 230 + yoffs),
            size=(0, 0),
            text='',
            color=(0.2, 1, 0.2),
            maxwidth=self._width * 0.8,
            scale=1.5,
            h_align='center',
            v_align='center',
        )

        bui.app.classic.master_server_v1_get(
            'bsGlobalProfileCheck',
            {'name': self._name, 'b': bui.app.env.engine_build_number},
            callback=bui.WeakCall(self._profile_check_result),
        )
        self._cost = plus.get_v1_account_misc_read_val(
            'price.global_profile', 500
        )
        self._status: str | None = 'waiting'
        self._update_timer = bui.AppTimer(
            1.023, bui.WeakCall(self._update), repeat=True
        )
        self._update()

    def _profile_check_result(self, result: dict[str, Any] | None) -> None:
        if result is None:
            bui.textwidget(
                edit=self._status_text,
                text=bui.Lstr(resource='internal.unavailableNoConnectionText'),
                color=(1, 0, 0),
            )
            self._status = 'error'
            bui.buttonwidget(
                edit=self._upgrade_button,
                color=(0.4, 0.4, 0.4),
                textcolor=(0.5, 0.5, 0.5),
            )
        else:
            if result['available']:
                bui.textwidget(
                    edit=self._status_text,
                    text=bui.Lstr(
                        resource=f'{self._r}.availableText',
                        subs=[('${NAME}', self._name)],
                    ),
                    color=(0, 1, 0),
                )
                bui.textwidget(
                    edit=self._price_text,
                    text=bui.charstr(bui.SpecialChar.TICKET) + str(self._cost),
                )
                self._status = None
            else:
                bui.textwidget(
                    edit=self._status_text,
                    text=bui.Lstr(
                        resource=f'{self._r}.unavailableText',
                        subs=[('${NAME}', self._name)],
                    ),
                    color=(1, 0, 0),
                )
                self._status = 'unavailable'
                bui.buttonwidget(
                    edit=self._upgrade_button,
                    color=(0.4, 0.4, 0.4),
                    textcolor=(0.5, 0.5, 0.5),
                )

    def _on_upgrade_press(self) -> None:
        # from bauiv1lib import gettickets

        if self._status is None:
            plus = bui.app.plus
            assert plus is not None

            # If it appears we don't have enough tickets, offer to buy more.
            tickets = plus.get_v1_account_ticket_count()
            if tickets < self._cost:
                bui.getsound('error').play()
                bui.screenmessage(
                    bui.Lstr(resource='notEnoughTicketsText'),
                    color=(1, 0, 0),
                )
                # gettickets.show_get_tickets_prompt()
                return
            bui.screenmessage(
                bui.Lstr(resource='purchasingText'), color=(0, 1, 0)
            )
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
                bui.screenmessage(
                    bui.Lstr(resource='errorText'), color=(1, 0, 0)
                )
                bui.getsound('error').play()
                return
            plus.add_v1_account_transaction(
                {'type': 'UPGRADE_PROFILE', 'name': self._name}
            )
            plus.run_v1_account_transactions()
            self._status = 'upgrading'
            self._upgrade_start_time = time.time()
        else:
            bui.getsound('error').play()

    def _update(self) -> None:
        plus = bui.app.plus
        assert plus is not None

        # If our originating window dies at any point, cancel.
        edit_profile_window = self._edit_profile_window()
        if edit_profile_window is None:
            self._cancel()
            return

        # Once we've kicked off an upgrade attempt and all transactions go
        # through, we're done.
        if (
            self._status == 'upgrading'
            and not plus.have_outstanding_v1_account_transactions()
        ):
            self._status = 'exiting'
            bui.containerwidget(edit=self._root_widget, transition='out_right')
            edit_profile_window = self._edit_profile_window()
            if edit_profile_window is None:
                print(
                    'profile upgrade transition out:'
                    ' original edit window gone'
                )
                return
            bui.getsound('gunCocking').play()
            edit_profile_window.reload_window()

    def _cancel(self) -> None:
        # If we recently sent out an upgrade request, disallow canceling
        # for a bit.
        if (
            self._upgrade_start_time is not None
            and time.time() - self._upgrade_start_time < 10.0
        ):
            bui.getsound('error').play()
            return
        bui.containerwidget(edit=self._root_widget, transition='out_right')
