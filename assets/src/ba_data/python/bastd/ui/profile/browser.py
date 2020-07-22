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
"""UI functionality related to browsing player profiles."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Any, Optional, Tuple, List, Dict


class ProfileBrowserWindow(ba.Window):
    """Window for browsing player profiles."""

    def __init__(self,
                 transition: str = 'in_right',
                 in_main_menu: bool = True,
                 selected_profile: str = None,
                 origin_widget: ba.Widget = None):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        from ba.internal import ensure_have_account_player_profile
        self._in_main_menu = in_main_menu
        if self._in_main_menu:
            back_label = ba.Lstr(resource='backText')
        else:
            back_label = ba.Lstr(resource='doneText')
        uiscale = ba.app.ui.uiscale
        self._width = 700.0 if uiscale is ba.UIScale.SMALL else 600.0
        x_inset = 50.0 if uiscale is ba.UIScale.SMALL else 0.0
        self._height = (360.0 if uiscale is ba.UIScale.SMALL else
                        385.0 if uiscale is ba.UIScale.MEDIUM else 410.0)

        # If we're being called up standalone, handle pause/resume ourself.
        if not self._in_main_menu:
            ba.app.pause()

        # If they provided an origin-widget, scale up from that.
        scale_origin: Optional[Tuple[float, float]]
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None

        self._r = 'playerProfilesWindow'

        # Ensure we've got an account-profile in cases where we're signed in.
        ensure_have_account_player_profile()

        top_extra = 20 if uiscale is ba.UIScale.SMALL else 0

        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height + top_extra),
            transition=transition,
            scale_origin_stack_offset=scale_origin,
            scale=(2.2 if uiscale is ba.UIScale.SMALL else
                   1.6 if uiscale is ba.UIScale.MEDIUM else 1.0),
            stack_offset=(0, -14) if uiscale is ba.UIScale.SMALL else (0, 0)))

        self._back_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(40 + x_inset, self._height - 59),
            size=(120, 60),
            scale=0.8,
            label=back_label,
            button_type='back' if self._in_main_menu else None,
            autoselect=True,
            on_activate_call=self._back)
        ba.containerwidget(edit=self._root_widget, cancel_button=btn)

        ba.textwidget(parent=self._root_widget,
                      position=(self._width * 0.5, self._height - 36),
                      size=(0, 0),
                      text=ba.Lstr(resource=self._r + '.titleText'),
                      maxwidth=300,
                      color=ba.app.ui.title_color,
                      scale=0.9,
                      h_align='center',
                      v_align='center')

        if self._in_main_menu:
            ba.buttonwidget(edit=btn,
                            button_type='backSmall',
                            size=(60, 60),
                            label=ba.charstr(ba.SpecialChar.BACK))

        scroll_height = self._height - 140.0
        self._scroll_width = self._width - (188 + x_inset * 2)
        v = self._height - 84.0
        h = 50 + x_inset
        b_color = (0.6, 0.53, 0.63)

        scl = (1.055 if uiscale is ba.UIScale.SMALL else
               1.18 if uiscale is ba.UIScale.MEDIUM else 1.3)
        v -= 70.0 * scl
        self._new_button = ba.buttonwidget(parent=self._root_widget,
                                           position=(h, v),
                                           size=(80, 66.0 * scl),
                                           on_activate_call=self._new_profile,
                                           color=b_color,
                                           button_type='square',
                                           autoselect=True,
                                           textcolor=(0.75, 0.7, 0.8),
                                           text_scale=0.7,
                                           label=ba.Lstr(resource=self._r +
                                                         '.newButtonText'))
        v -= 70.0 * scl
        self._edit_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(80, 66.0 * scl),
            on_activate_call=self._edit_profile,
            color=b_color,
            button_type='square',
            autoselect=True,
            textcolor=(0.75, 0.7, 0.8),
            text_scale=0.7,
            label=ba.Lstr(resource=self._r + '.editButtonText'))
        v -= 70.0 * scl
        self._delete_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(80, 66.0 * scl),
            on_activate_call=self._delete_profile,
            color=b_color,
            button_type='square',
            autoselect=True,
            textcolor=(0.75, 0.7, 0.8),
            text_scale=0.7,
            label=ba.Lstr(resource=self._r + '.deleteButtonText'))

        v = self._height - 87

        ba.textwidget(parent=self._root_widget,
                      position=(self._width * 0.5, self._height - 71),
                      size=(0, 0),
                      text=ba.Lstr(resource=self._r + '.explanationText'),
                      color=ba.app.ui.infotextcolor,
                      maxwidth=self._width * 0.83,
                      scale=0.6,
                      h_align='center',
                      v_align='center')

        self._scrollwidget = ba.scrollwidget(parent=self._root_widget,
                                             highlight=False,
                                             position=(140 + x_inset,
                                                       v - scroll_height),
                                             size=(self._scroll_width,
                                                   scroll_height))
        ba.widget(edit=self._scrollwidget,
                  autoselect=True,
                  left_widget=self._new_button)
        ba.containerwidget(edit=self._root_widget,
                           selected_child=self._scrollwidget)
        self._columnwidget = ba.columnwidget(parent=self._scrollwidget,
                                             border=2,
                                             margin=0)
        v -= 255
        self._profiles: Optional[Dict[str, Dict[str, Any]]] = None
        self._selected_profile = selected_profile
        self._profile_widgets: List[ba.Widget] = []
        self._refresh()
        self._restore_state()

    def _new_profile(self) -> None:
        # pylint: disable=cyclic-import
        from ba.internal import have_pro_options
        from bastd.ui.profile.edit import EditProfileWindow
        from bastd.ui.purchase import PurchaseWindow

        # Limit to a handful profiles if they don't have pro-options.
        max_non_pro_profiles = _ba.get_account_misc_read_val('mnpp', 5)
        assert self._profiles is not None
        if (not have_pro_options()
                and len(self._profiles) >= max_non_pro_profiles):
            PurchaseWindow(items=['pro'],
                           header_text=ba.Lstr(
                               resource='unlockThisProfilesText',
                               subs=[('${NUM}', str(max_non_pro_profiles))]))
            return

        # Clamp at 100 profiles (otherwise the server will and that's less
        # elegant looking).
        if len(self._profiles) > 100:
            ba.screenmessage(
                ba.Lstr(translate=('serverResponses',
                                   'Max number of profiles reached.')),
                color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return

        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            EditProfileWindow(
                existing_profile=None,
                in_main_menu=self._in_main_menu).get_root_widget())

    def _delete_profile(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui import confirm
        if self._selected_profile is None:
            ba.playsound(ba.getsound('error'))
            ba.screenmessage(ba.Lstr(resource='nothingIsSelectedErrorText'),
                             color=(1, 0, 0))
            return
        if self._selected_profile == '__account__':
            ba.playsound(ba.getsound('error'))
            ba.screenmessage(ba.Lstr(resource=self._r +
                                     '.cantDeleteAccountProfileText'),
                             color=(1, 0, 0))
            return
        confirm.ConfirmWindow(
            ba.Lstr(resource=self._r + '.deleteConfirmText',
                    subs=[('${PROFILE}', self._selected_profile)]),
            self._do_delete_profile, 350)

    def _do_delete_profile(self) -> None:
        _ba.add_transaction({
            'type': 'REMOVE_PLAYER_PROFILE',
            'name': self._selected_profile
        })
        _ba.run_transactions()
        ba.playsound(ba.getsound('shieldDown'))
        self._refresh()

        # Select profile list.
        ba.containerwidget(edit=self._root_widget,
                           selected_child=self._scrollwidget)

    def _edit_profile(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.profile.edit import EditProfileWindow
        if self._selected_profile is None:
            ba.playsound(ba.getsound('error'))
            ba.screenmessage(ba.Lstr(resource='nothingIsSelectedErrorText'),
                             color=(1, 0, 0))
            return
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            EditProfileWindow(
                self._selected_profile,
                in_main_menu=self._in_main_menu).get_root_widget())

    def _select(self, name: str, index: int) -> None:
        del index  # Unused.
        self._selected_profile = name

    def _back(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.account.settings import AccountSettingsWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget,
                           transition=self._transition_out)
        if self._in_main_menu:
            ba.app.ui.set_main_menu_window(
                AccountSettingsWindow(transition='in_left').get_root_widget())

        # If we're being called up standalone, handle pause/resume ourself.
        else:
            ba.app.resume()

    def _refresh(self) -> None:
        # pylint: disable=too-many-locals
        from ba.internal import (PlayerProfilesChangedMessage,
                                 get_player_profile_colors,
                                 get_player_profile_icon)
        old_selection = self._selected_profile

        # Delete old.
        while self._profile_widgets:
            self._profile_widgets.pop().delete()
        self._profiles = ba.app.config.get('Player Profiles', {})
        assert self._profiles is not None
        items = list(self._profiles.items())
        items.sort(key=lambda x: x[0].lower())
        index = 0
        account_name: Optional[str]
        if _ba.get_account_state() == 'signed_in':
            account_name = _ba.get_account_display_string()
        else:
            account_name = None
        widget_to_select = None
        for p_name, _ in items:
            if p_name == '__account__' and account_name is None:
                continue
            color, _highlight = get_player_profile_colors(p_name)
            scl = 1.1
            tval = (account_name if p_name == '__account__' else
                    get_player_profile_icon(p_name) + p_name)
            assert isinstance(tval, str)
            txtw = ba.textwidget(
                parent=self._columnwidget,
                position=(0, 32),
                size=((self._width - 40) / scl, 28),
                text=ba.Lstr(value=tval),
                h_align='left',
                v_align='center',
                on_select_call=ba.WeakCall(self._select, p_name, index),
                maxwidth=self._scroll_width * 0.92,
                corner_scale=scl,
                color=ba.safecolor(color, 0.4),
                always_highlight=True,
                on_activate_call=ba.Call(self._edit_button.activate),
                selectable=True)
            if index == 0:
                ba.widget(edit=txtw, up_widget=self._back_button)
            ba.widget(edit=txtw, show_buffer_top=40, show_buffer_bottom=40)
            self._profile_widgets.append(txtw)

            # Select/show this one if it was previously selected
            # (but defer till after this loop since our height is
            # still changing).
            if p_name == old_selection:
                widget_to_select = txtw

            index += 1

        if widget_to_select is not None:
            ba.columnwidget(edit=self._columnwidget,
                            selected_child=widget_to_select,
                            visible_child=widget_to_select)

        # If there's a team-chooser in existence, tell it the profile-list
        # has probably changed.
        session = _ba.get_foreground_host_session()
        if session is not None:
            session.handlemessage(PlayerProfilesChangedMessage())

    def _save_state(self) -> None:
        try:
            sel = self._root_widget.get_selected_child()
            if sel == self._new_button:
                sel_name = 'New'
            elif sel == self._edit_button:
                sel_name = 'Edit'
            elif sel == self._delete_button:
                sel_name = 'Delete'
            elif sel == self._scrollwidget:
                sel_name = 'Scroll'
            else:
                sel_name = 'Back'
            ba.app.ui.window_states[self.__class__.__name__] = sel_name
        except Exception:
            ba.print_exception(f'Error saving state for {self}.')

    def _restore_state(self) -> None:
        try:
            sel_name = ba.app.ui.window_states.get(self.__class__.__name__)
            if sel_name == 'Scroll':
                sel = self._scrollwidget
            elif sel_name == 'New':
                sel = self._new_button
            elif sel_name == 'Delete':
                sel = self._delete_button
            elif sel_name == 'Edit':
                sel = self._edit_button
            elif sel_name == 'Back':
                sel = self._back_button
            else:
                # By default we select our scroll widget if we have profiles;
                # otherwise our new widget.
                if not self._profile_widgets:
                    sel = self._new_button
                else:
                    sel = self._scrollwidget
            ba.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            ba.print_exception(f'Error restoring state for {self}.')
