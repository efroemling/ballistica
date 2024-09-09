# Released under the MIT License. See LICENSE for details.
#
"""UI functionality related to browsing player profiles."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

import bauiv1 as bui
import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any


class ProfileBrowserWindow(bui.MainWindow):
    """Window for browsing player profiles."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        # in_main_menu: bool = True,
        selected_profile: str | None = None,
        origin_widget: bui.Widget | None = None,
        minimal_toolbar: bool = False,
    ):
        self._minimal_toolbar = minimal_toolbar
        back_label = bui.Lstr(resource='backText')
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._width = 800.0 if uiscale is bui.UIScale.SMALL else 600.0
        x_inset = 100.0 if uiscale is bui.UIScale.SMALL else 0.0
        self._height = (
            360.0
            if uiscale is bui.UIScale.SMALL
            else 385.0 if uiscale is bui.UIScale.MEDIUM else 410.0
        )

        # Need to handle out-transitions ourself for modal mode.
        if origin_widget is not None:
            self._transition_out = 'out_scale'
        else:
            self._transition_out = 'out_right'

        self._r = 'playerProfilesWindow'

        # Ensure we've got an account-profile in cases where we're signed in.
        assert bui.app.classic is not None
        bui.app.classic.accounts.ensure_have_account_player_profile()

        top_extra = 20 if uiscale is bui.UIScale.SMALL else 0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height + top_extra),
                toolbar_visibility=(
                    'menu_minimal'
                    if (uiscale is bui.UIScale.SMALL or minimal_toolbar)
                    else 'menu_full'
                ),
                scale=(
                    2.0
                    if uiscale is bui.UIScale.SMALL
                    else 1.5 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
                stack_offset=(
                    (0, -14) if uiscale is bui.UIScale.SMALL else (0, 0)
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        if bui.app.ui_v1.uiscale is bui.UIScale.SMALL:
            self._back_button = bui.get_special_widget('back_button')
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            self._back_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(40 + x_inset, self._height - 59),
                size=(120, 60),
                scale=0.8,
                label=back_label,
                button_type='back',
                autoselect=True,
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)
            bui.buttonwidget(
                edit=btn,
                button_type='backSmall',
                size=(60, 60),
                label=bui.charstr(bui.SpecialChar.BACK),
            )

        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 36),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            maxwidth=300,
            color=bui.app.ui_v1.title_color,
            scale=0.9,
            h_align='center',
            v_align='center',
        )

        scroll_height = self._height - 140.0
        self._scroll_width = self._width - (188 + x_inset * 2)
        v = self._height - 84.0
        h = 50 + x_inset
        b_color = (0.6, 0.53, 0.63)

        scl = (
            1.055
            if uiscale is bui.UIScale.SMALL
            else 1.18 if uiscale is bui.UIScale.MEDIUM else 1.3
        )
        v -= 70.0 * scl
        self._new_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(80, 66.0 * scl),
            on_activate_call=self._new_profile,
            color=b_color,
            button_type='square',
            autoselect=True,
            textcolor=(0.75, 0.7, 0.8),
            text_scale=0.7,
            label=bui.Lstr(resource=f'{self._r}.newButtonText'),
        )
        v -= 70.0 * scl
        self._edit_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(80, 66.0 * scl),
            on_activate_call=self._edit_profile,
            color=b_color,
            button_type='square',
            autoselect=True,
            textcolor=(0.75, 0.7, 0.8),
            text_scale=0.7,
            label=bui.Lstr(resource=f'{self._r}.editButtonText'),
        )
        v -= 70.0 * scl
        self._delete_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(80, 66.0 * scl),
            on_activate_call=self._delete_profile,
            color=b_color,
            button_type='square',
            autoselect=True,
            textcolor=(0.75, 0.7, 0.8),
            text_scale=0.7,
            label=bui.Lstr(resource=f'{self._r}.deleteButtonText'),
        )

        v = self._height - 87

        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 71),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.explanationText'),
            color=bui.app.ui_v1.infotextcolor,
            maxwidth=self._width * 0.83,
            scale=0.6,
            h_align='center',
            v_align='center',
        )

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            highlight=False,
            position=(140 + x_inset, v - scroll_height),
            size=(self._scroll_width, scroll_height),
        )
        bui.widget(
            edit=self._scrollwidget,
            autoselect=True,
            left_widget=self._new_button,
        )
        bui.containerwidget(
            edit=self._root_widget, selected_child=self._scrollwidget
        )
        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(self._scroll_width, 32),
            background=False,
        )
        v -= 255
        self._profiles: dict[str, dict[str, Any]] | None = None
        self._selected_profile = selected_profile
        self._profile_widgets: list[bui.Widget] = []
        self._refresh()
        self._restore_state()

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        minimal_toolbar = self._minimal_toolbar

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition,
                origin_widget=origin_widget,
                minimal_toolbar=minimal_toolbar,
            )
        )

    @override
    def on_main_window_close(self) -> None:
        self._save_state()

    def _new_profile(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.profile.edit import EditProfileWindow
        from bauiv1lib.purchase import PurchaseWindow

        # No-op if we're not the in-control main window.
        if not self.main_window_has_control():
            return

        # no-op if our underlying widget is dead or on its way out.
        # if not self._root_widget or self._root_widget.transitioning_out:
        #     return

        plus = bui.app.plus
        assert plus is not None

        # Limit to a handful profiles if they don't have pro-options.
        max_non_pro_profiles = plus.get_v1_account_misc_read_val('mnpp', 5)
        assert self._profiles is not None
        assert bui.app.classic is not None
        if (
            not bui.app.classic.accounts.have_pro_options()
            and len(self._profiles) >= max_non_pro_profiles
        ):
            PurchaseWindow(
                items=['pro'],
                header_text=bui.Lstr(
                    resource='unlockThisProfilesText',
                    subs=[('${NUM}', str(max_non_pro_profiles))],
                ),
            )
            return

        # Clamp at 100 profiles (otherwise the server will and that's less
        # elegant looking).
        if len(self._profiles) > 100:
            bui.screenmessage(
                bui.Lstr(
                    translate=(
                        'serverResponses',
                        'Max number of profiles reached.',
                    )
                ),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return

        self.main_window_replace(EditProfileWindow(existing_profile=None))

    def _delete_profile(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib import confirm

        if self._selected_profile is None:
            bui.getsound('error').play()
            bui.screenmessage(
                bui.Lstr(resource='nothingIsSelectedErrorText'), color=(1, 0, 0)
            )
            return
        if self._selected_profile == '__account__':
            bui.getsound('error').play()
            bui.screenmessage(
                bui.Lstr(resource=f'{self._r}.cantDeleteAccountProfileText'),
                color=(1, 0, 0),
            )
            return
        confirm.ConfirmWindow(
            bui.Lstr(
                resource=f'{self._r}.deleteConfirmText',
                subs=[('${PROFILE}', self._selected_profile)],
            ),
            self._do_delete_profile,
            350,
        )

    def _do_delete_profile(self) -> None:
        plus = bui.app.plus
        assert plus is not None

        plus.add_v1_account_transaction(
            {'type': 'REMOVE_PLAYER_PROFILE', 'name': self._selected_profile}
        )
        plus.run_v1_account_transactions()
        bui.getsound('shieldDown').play()
        self._refresh()

        # Select profile list.
        bui.containerwidget(
            edit=self._root_widget, selected_child=self._scrollwidget
        )

    def _edit_profile(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.profile.edit import EditProfileWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        if self._selected_profile is None:
            bui.getsound('error').play()
            bui.screenmessage(
                bui.Lstr(resource='nothingIsSelectedErrorText'), color=(1, 0, 0)
            )
            return

        self.main_window_replace(EditProfileWindow(self._selected_profile))

    def _select(self, name: str, index: int) -> None:
        del index  # Unused.
        self._selected_profile = name

    def _refresh(self) -> None:
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        from efro.util import asserttype
        from bascenev1 import PlayerProfilesChangedMessage
        from bascenev1lib.actor import spazappearance

        assert bui.app.classic is not None

        plus = bui.app.plus
        assert plus is not None

        old_selection = self._selected_profile

        # Delete old.
        while self._profile_widgets:
            self._profile_widgets.pop().delete()
        self._profiles = bui.app.config.get('Player Profiles', {})
        assert self._profiles is not None
        items = list(self._profiles.items())
        items.sort(key=lambda x: asserttype(x[0], str).lower())
        spazzes = spazappearance.get_appearances()
        spazzes.sort()
        icon_textures = [
            bui.gettexture(bui.app.classic.spaz_appearances[s].icon_texture)
            for s in spazzes
        ]
        icon_tint_textures = [
            bui.gettexture(
                bui.app.classic.spaz_appearances[s].icon_mask_texture
            )
            for s in spazzes
        ]
        index = 0
        y_val = 35 * (len(self._profiles) - 1)
        account_name: str | None
        if plus.get_v1_account_state() == 'signed_in':
            account_name = plus.get_v1_account_display_string()
        else:
            account_name = None
        widget_to_select = None
        for p_name, p_info in items:
            if p_name == '__account__' and account_name is None:
                continue
            color, _highlight = bui.app.classic.get_player_profile_colors(
                p_name
            )
            scl = 1.1
            tval = (
                account_name
                if p_name == '__account__'
                else bui.app.classic.get_player_profile_icon(p_name) + p_name
            )

            try:
                char_index = spazzes.index(p_info['character'])
            except Exception:
                char_index = spazzes.index('Spaz')

            assert isinstance(tval, str)
            txtw = bui.textwidget(
                parent=self._subcontainer,
                position=(5, y_val),
                size=((self._width - 210) / scl, 28),
                text=bui.Lstr(value=f'    {tval}'),
                h_align='left',
                v_align='center',
                on_select_call=bui.WeakCall(self._select, p_name, index),
                maxwidth=self._scroll_width * 0.86,
                corner_scale=scl,
                color=bui.safecolor(color, 0.4),
                always_highlight=True,
                on_activate_call=bui.Call(self._edit_button.activate),
                selectable=True,
            )
            character = bui.imagewidget(
                parent=self._subcontainer,
                position=(0, y_val),
                size=(30, 30),
                color=(1, 1, 1),
                mask_texture=bui.gettexture('characterIconMask'),
                tint_color=color,
                tint2_color=_highlight,
                texture=icon_textures[char_index],
                tint_texture=icon_tint_textures[char_index],
            )
            if index == 0:
                bui.widget(edit=txtw, up_widget=self._back_button)
                if self._selected_profile is None:
                    self._selected_profile = p_name
            bui.widget(edit=txtw, show_buffer_top=40, show_buffer_bottom=40)
            self._profile_widgets.append(txtw)
            self._profile_widgets.append(character)

            # Select/show this one if it was previously selected
            # (but defer till after this loop since our height is
            # still changing).
            if p_name == old_selection:
                widget_to_select = txtw

            index += 1
            y_val -= 35

        bui.containerwidget(
            edit=self._subcontainer,
            size=(self._scroll_width, index * 35),
        )
        if widget_to_select is not None:
            bui.containerwidget(
                edit=self._subcontainer,
                selected_child=widget_to_select,
                visible_child=widget_to_select,
            )

        # If there's a team-chooser in existence, tell it the profile-list
        # has probably changed.
        session = bs.get_foreground_host_session()
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
            assert bui.app.classic is not None
            bui.app.ui_v1.window_states[type(self)] = sel_name
        except Exception:
            logging.exception('Error saving state for %s.', self)

    def _restore_state(self) -> None:
        try:
            assert bui.app.classic is not None
            sel_name = bui.app.ui_v1.window_states.get(type(self))
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
            bui.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            logging.exception('Error restoring state for %s.', self)
