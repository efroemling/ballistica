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
"""UI functionality for advanced settings."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
import ba
from bastd.ui import popup as popup_ui

if TYPE_CHECKING:
    from typing import Tuple, Any, Optional, List, Dict


class AdvancedSettingsWindow(ba.Window):
    """Window for editing advanced game settings."""

    def __init__(self,
                 transition: str = 'in_right',
                 origin_widget: ba.Widget = None):
        # pylint: disable=too-many-statements
        from ba.internal import master_server_get

        import threading

        # Preload some modules we use in a background thread so we won't
        # have a visual hitch when the user taps them.
        threading.Thread(target=self._preload_modules).start()

        app = ba.app

        # If they provided an origin-widget, scale up from that.
        scale_origin: Optional[Tuple[float, float]]
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None

        uiscale = ba.app.ui.uiscale
        self._width = 870.0 if uiscale is ba.UIScale.SMALL else 670.0
        x_inset = 100 if uiscale is ba.UIScale.SMALL else 0
        self._height = (390.0 if uiscale is ba.UIScale.SMALL else
                        450.0 if uiscale is ba.UIScale.MEDIUM else 520.0)
        self._spacing = 32
        self._menu_open = False
        top_extra = 10 if uiscale is ba.UIScale.SMALL else 0
        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height + top_extra),
            transition=transition,
            toolbar_visibility='menu_minimal',
            scale_origin_stack_offset=scale_origin,
            scale=(2.06 if uiscale is ba.UIScale.SMALL else
                   1.4 if uiscale is ba.UIScale.MEDIUM else 1.0),
            stack_offset=(0, -25) if uiscale is ba.UIScale.SMALL else (0, 0)))
        self._prev_lang = ''
        self._prev_lang_list: List[str] = []
        self._complete_langs_list: Optional[List] = None
        self._complete_langs_error = False
        self._language_popup: Optional[popup_ui.PopupMenu] = None

        # In vr-mode, the internal keyboard is currently the *only* option,
        # so no need to show this.
        self._show_always_use_internal_keyboard = (not app.vr_mode)

        self._scroll_width = self._width - (100 + 2 * x_inset)
        self._scroll_height = self._height - 115.0
        self._sub_width = self._scroll_width * 0.95
        self._sub_height = 724.0

        if self._show_always_use_internal_keyboard:
            self._sub_height += 62

        self._show_disable_gyro = app.platform in {'ios', 'android'}
        if self._show_disable_gyro:
            self._sub_height += 42

        self._do_vr_test_button = app.vr_mode
        self._do_net_test_button = True
        self._extra_button_spacing = self._spacing * 2.5

        if self._do_vr_test_button:
            self._sub_height += self._extra_button_spacing
        if self._do_net_test_button:
            self._sub_height += self._extra_button_spacing
        self._sub_height += self._spacing * 2.0  # plugins

        self._r = 'settingsWindowAdvanced'

        if app.ui.use_toolbars and uiscale is ba.UIScale.SMALL:
            ba.containerwidget(edit=self._root_widget,
                               on_cancel_call=self._do_back)
            self._back_button = None
        else:
            self._back_button = ba.buttonwidget(
                parent=self._root_widget,
                position=(53 + x_inset, self._height - 60),
                size=(140, 60),
                scale=0.8,
                autoselect=True,
                label=ba.Lstr(resource='backText'),
                button_type='back',
                on_activate_call=self._do_back)
            ba.containerwidget(edit=self._root_widget,
                               cancel_button=self._back_button)

        self._title_text = ba.textwidget(parent=self._root_widget,
                                         position=(0, self._height - 52),
                                         size=(self._width, 25),
                                         text=ba.Lstr(resource=self._r +
                                                      '.titleText'),
                                         color=app.ui.title_color,
                                         h_align='center',
                                         v_align='top')

        if self._back_button is not None:
            ba.buttonwidget(edit=self._back_button,
                            button_type='backSmall',
                            size=(60, 60),
                            label=ba.charstr(ba.SpecialChar.BACK))

        self._scrollwidget = ba.scrollwidget(parent=self._root_widget,
                                             position=(50 + x_inset, 50),
                                             simple_culling_v=20.0,
                                             highlight=False,
                                             size=(self._scroll_width,
                                                   self._scroll_height),
                                             selection_loops_to_parent=True)
        ba.widget(edit=self._scrollwidget, right_widget=self._scrollwidget)
        self._subcontainer = ba.containerwidget(parent=self._scrollwidget,
                                                size=(self._sub_width,
                                                      self._sub_height),
                                                background=False,
                                                selection_loops_to_parent=True)

        self._rebuild()

        # Rebuild periodically to pick up language changes/additions/etc.
        self._rebuild_timer = ba.Timer(1.0,
                                       ba.WeakCall(self._rebuild),
                                       repeat=True,
                                       timetype=ba.TimeType.REAL)

        # Fetch the list of completed languages.
        master_server_get('bsLangGetCompleted', {'b': app.build_number},
                          callback=ba.WeakCall(self._completed_langs_cb))

    @staticmethod
    def _preload_modules() -> None:
        """Preload modules we use (called in bg thread)."""
        from bastd.ui import config as _unused1
        from ba import modutils as _unused2
        from bastd.ui.settings import vrtesting as _unused3
        from bastd.ui.settings import nettesting as _unused4
        from bastd.ui import appinvite as _unused5
        from bastd.ui import account as _unused6
        from bastd.ui import promocode as _unused7
        from bastd.ui import debug as _unused8
        from bastd.ui.settings import plugins as _unused9

    def _update_lang_status(self) -> None:
        if self._complete_langs_list is not None:
            up_to_date = (ba.app.language in self._complete_langs_list)
            ba.textwidget(
                edit=self._lang_status_text,
                text='' if ba.app.language == 'Test' else ba.Lstr(
                    resource=self._r + '.translationNoUpdateNeededText')
                if up_to_date else ba.Lstr(resource=self._r +
                                           '.translationUpdateNeededText'),
                color=(0.2, 1.0, 0.2, 0.8) if up_to_date else
                (1.0, 0.2, 0.2, 0.8))
        else:
            ba.textwidget(
                edit=self._lang_status_text,
                text=ba.Lstr(resource=self._r + '.translationFetchErrorText')
                if self._complete_langs_error else ba.Lstr(
                    resource=self._r + '.translationFetchingStatusText'),
                color=(1.0, 0.5, 0.2) if self._complete_langs_error else
                (0.7, 0.7, 0.7))

    def _rebuild(self) -> None:
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        from bastd.ui.config import ConfigCheckBox
        from ba.modutils import show_user_scripts

        # Don't rebuild if the menu is open or if our language and
        # language-list hasn't changed.
        # NOTE - although we now support widgets updating their own
        # translations, we still change the label formatting on the language
        # menu based on the language so still need this. ...however we could
        # make this more limited to it only rebuilds that one menu instead
        # of everything.
        if self._menu_open or (
                self._prev_lang == _ba.app.config.get('Lang', None)
                and self._prev_lang_list == ba.get_valid_languages()):
            return
        self._prev_lang = _ba.app.config.get('Lang', None)
        self._prev_lang_list = ba.get_valid_languages()

        # Clear out our sub-container.
        children = self._subcontainer.get_children()
        for child in children:
            child.delete()

        v = self._sub_height - 35

        v -= self._spacing * 1.2

        # Update our existing back button and title.
        if self._back_button is not None:
            ba.buttonwidget(edit=self._back_button,
                            label=ba.Lstr(resource='backText'))
            ba.buttonwidget(edit=self._back_button,
                            label=ba.charstr(ba.SpecialChar.BACK))

        ba.textwidget(edit=self._title_text,
                      text=ba.Lstr(resource=self._r + '.titleText'))

        this_button_width = 410

        self._promo_code_button = ba.buttonwidget(
            parent=self._subcontainer,
            position=(self._sub_width / 2 - this_button_width / 2, v - 14),
            size=(this_button_width, 60),
            autoselect=True,
            label=ba.Lstr(resource=self._r + '.enterPromoCodeText'),
            text_scale=1.0,
            on_activate_call=self._on_promo_code_press)
        if self._back_button is not None:
            ba.widget(edit=self._promo_code_button,
                      up_widget=self._back_button,
                      left_widget=self._back_button)
        v -= self._extra_button_spacing * 0.8

        ba.textwidget(parent=self._subcontainer,
                      position=(200, v + 10),
                      size=(0, 0),
                      text=ba.Lstr(resource=self._r + '.languageText'),
                      maxwidth=150,
                      scale=0.95,
                      color=ba.app.ui.title_color,
                      h_align='right',
                      v_align='center')

        languages = ba.get_valid_languages()
        cur_lang = _ba.app.config.get('Lang', None)
        if cur_lang is None:
            cur_lang = 'Auto'

        # We have a special dict of language names in that language
        # so we don't have to go digging through each full language.
        try:
            import json
            with open('ba_data/data/langdata.json') as infile:
                lang_names_translated = (json.loads(
                    infile.read())['lang_names_translated'])
        except Exception:
            ba.print_exception('Error reading lang data.')
            lang_names_translated = {}

        langs_translated = {}
        for lang in languages:
            langs_translated[lang] = lang_names_translated.get(lang, lang)

        langs_full = {}
        for lang in languages:
            lang_translated = ba.Lstr(translate=('languages', lang)).evaluate()
            if langs_translated[lang] == lang_translated:
                langs_full[lang] = lang_translated
            else:
                langs_full[lang] = (langs_translated[lang] + ' (' +
                                    lang_translated + ')')

        self._language_popup = popup_ui.PopupMenu(
            parent=self._subcontainer,
            position=(210, v - 19),
            width=150,
            opening_call=ba.WeakCall(self._on_menu_open),
            closing_call=ba.WeakCall(self._on_menu_close),
            autoselect=False,
            on_value_change_call=ba.WeakCall(self._on_menu_choice),
            choices=['Auto'] + languages,
            button_size=(250, 60),
            choices_display=([
                ba.Lstr(value=(ba.Lstr(resource='autoText').evaluate() + ' (' +
                               ba.Lstr(translate=(
                                   'languages',
                                   ba.app.default_language)).evaluate() + ')'))
            ] + [ba.Lstr(value=langs_full[l]) for l in languages]),
            current_choice=cur_lang)

        v -= self._spacing * 1.8

        ba.textwidget(parent=self._subcontainer,
                      position=(self._sub_width * 0.5, v + 10),
                      size=(0, 0),
                      text=ba.Lstr(resource=self._r + '.helpTranslateText',
                                   subs=[('${APP_NAME}',
                                          ba.Lstr(resource='titleText'))]),
                      maxwidth=self._sub_width * 0.9,
                      max_height=55,
                      flatness=1.0,
                      scale=0.65,
                      color=(0.4, 0.9, 0.4, 0.8),
                      h_align='center',
                      v_align='center')
        v -= self._spacing * 1.9
        this_button_width = 410
        self._translation_editor_button = ba.buttonwidget(
            parent=self._subcontainer,
            position=(self._sub_width / 2 - this_button_width / 2, v - 24),
            size=(this_button_width, 60),
            label=ba.Lstr(resource=self._r + '.translationEditorButtonText',
                          subs=[('${APP_NAME}', ba.Lstr(resource='titleText'))
                                ]),
            autoselect=True,
            on_activate_call=ba.Call(ba.open_url,
                                     'http://bombsquadgame.com/translate'))

        self._lang_status_text = ba.textwidget(parent=self._subcontainer,
                                               position=(self._sub_width * 0.5,
                                                         v - 40),
                                               size=(0, 0),
                                               text='',
                                               flatness=1.0,
                                               scale=0.63,
                                               h_align='center',
                                               v_align='center',
                                               maxwidth=400.0)
        self._update_lang_status()
        v -= 40

        lang_inform = _ba.get_account_misc_val('langInform', False)

        self._language_inform_checkbox = cbw = ba.checkboxwidget(
            parent=self._subcontainer,
            position=(50, v - 50),
            size=(self._sub_width - 100, 30),
            autoselect=True,
            maxwidth=430,
            textcolor=(0.8, 0.8, 0.8),
            value=lang_inform,
            text=ba.Lstr(resource=self._r + '.translationInformMe'),
            on_value_change_call=ba.WeakCall(
                self._on_lang_inform_value_change))

        ba.widget(edit=self._translation_editor_button,
                  down_widget=cbw,
                  up_widget=self._language_popup.get_button())

        v -= self._spacing * 3.0

        self._kick_idle_players_check_box = ConfigCheckBox(
            parent=self._subcontainer,
            position=(50, v),
            size=(self._sub_width - 100, 30),
            configkey='Kick Idle Players',
            displayname=ba.Lstr(resource=self._r + '.kickIdlePlayersText'),
            scale=1.0,
            maxwidth=430)

        v -= 42
        self._disable_camera_shake_check_box = ConfigCheckBox(
            parent=self._subcontainer,
            position=(50, v),
            size=(self._sub_width - 100, 30),
            configkey='Disable Camera Shake',
            displayname=ba.Lstr(resource=self._r + '.disableCameraShakeText'),
            scale=1.0,
            maxwidth=430)

        self._disable_gyro_check_box: Optional[ConfigCheckBox] = None
        if self._show_disable_gyro:
            v -= 42
            self._disable_gyro_check_box = ConfigCheckBox(
                parent=self._subcontainer,
                position=(50, v),
                size=(self._sub_width - 100, 30),
                configkey='Disable Camera Gyro',
                displayname=ba.Lstr(resource=self._r +
                                    '.disableCameraGyroscopeMotionText'),
                scale=1.0,
                maxwidth=430)

        self._always_use_internal_keyboard_check_box: Optional[ConfigCheckBox]
        if self._show_always_use_internal_keyboard:
            v -= 42
            self._always_use_internal_keyboard_check_box = ConfigCheckBox(
                parent=self._subcontainer,
                position=(50, v),
                size=(self._sub_width - 100, 30),
                configkey='Always Use Internal Keyboard',
                autoselect=True,
                displayname=ba.Lstr(resource=self._r +
                                    '.alwaysUseInternalKeyboardText'),
                scale=1.0,
                maxwidth=430)
            ba.textwidget(
                parent=self._subcontainer,
                position=(90, v - 10),
                size=(0, 0),
                text=ba.Lstr(resource=self._r +
                             '.alwaysUseInternalKeyboardDescriptionText'),
                maxwidth=400,
                flatness=1.0,
                scale=0.65,
                color=(0.4, 0.9, 0.4, 0.8),
                h_align='left',
                v_align='center')
            v -= 20
        else:
            self._always_use_internal_keyboard_check_box = None

        v -= self._spacing * 2.1

        this_button_width = 410
        self._show_user_mods_button = ba.buttonwidget(
            parent=self._subcontainer,
            position=(self._sub_width / 2 - this_button_width / 2, v - 10),
            size=(this_button_width, 60),
            autoselect=True,
            label=ba.Lstr(resource=self._r + '.showUserModsText'),
            text_scale=1.0,
            on_activate_call=show_user_scripts)
        if self._show_always_use_internal_keyboard:
            assert self._always_use_internal_keyboard_check_box is not None
            ba.widget(edit=self._always_use_internal_keyboard_check_box.widget,
                      down_widget=self._show_user_mods_button)
            ba.widget(
                edit=self._show_user_mods_button,
                up_widget=self._always_use_internal_keyboard_check_box.widget)
        else:
            ba.widget(edit=self._show_user_mods_button,
                      up_widget=self._kick_idle_players_check_box.widget)
            ba.widget(edit=self._kick_idle_players_check_box.widget,
                      down_widget=self._show_user_mods_button)

        v -= self._spacing * 2.0

        self._modding_guide_button = ba.buttonwidget(
            parent=self._subcontainer,
            position=(self._sub_width / 2 - this_button_width / 2, v - 10),
            size=(this_button_width, 60),
            autoselect=True,
            label=ba.Lstr(resource=self._r + '.moddingGuideText'),
            text_scale=1.0,
            on_activate_call=ba.Call(
                ba.open_url,
                'http://www.froemling.net/docs/bombsquad-modding-guide'))

        v -= self._spacing * 2.0

        self._plugins_button = ba.buttonwidget(
            parent=self._subcontainer,
            position=(self._sub_width / 2 - this_button_width / 2, v - 10),
            size=(this_button_width, 60),
            autoselect=True,
            label=ba.Lstr(resource='pluginsText'),
            text_scale=1.0,
            on_activate_call=self._on_plugins_button_press)

        v -= self._spacing * 0.6

        self._vr_test_button: Optional[ba.Widget]
        if self._do_vr_test_button:
            v -= self._extra_button_spacing
            self._vr_test_button = ba.buttonwidget(
                parent=self._subcontainer,
                position=(self._sub_width / 2 - this_button_width / 2, v - 14),
                size=(this_button_width, 60),
                autoselect=True,
                label=ba.Lstr(resource=self._r + '.vrTestingText'),
                text_scale=1.0,
                on_activate_call=self._on_vr_test_press)
        else:
            self._vr_test_button = None

        self._net_test_button: Optional[ba.Widget]
        if self._do_net_test_button:
            v -= self._extra_button_spacing
            self._net_test_button = ba.buttonwidget(
                parent=self._subcontainer,
                position=(self._sub_width / 2 - this_button_width / 2, v - 14),
                size=(this_button_width, 60),
                autoselect=True,
                label=ba.Lstr(resource=self._r + '.netTestingText'),
                text_scale=1.0,
                on_activate_call=self._on_net_test_press)
        else:
            self._net_test_button = None

        v -= 70
        self._benchmarks_button = ba.buttonwidget(
            parent=self._subcontainer,
            position=(self._sub_width / 2 - this_button_width / 2, v - 14),
            size=(this_button_width, 60),
            autoselect=True,
            label=ba.Lstr(resource=self._r + '.benchmarksText'),
            text_scale=1.0,
            on_activate_call=self._on_benchmark_press)

        for child in self._subcontainer.get_children():
            ba.widget(edit=child, show_buffer_bottom=30, show_buffer_top=20)

        if ba.app.ui.use_toolbars:
            pbtn = _ba.get_special_widget('party_button')
            ba.widget(edit=self._scrollwidget, right_widget=pbtn)
            if self._back_button is None:
                ba.widget(edit=self._scrollwidget,
                          left_widget=_ba.get_special_widget('back_button'))

        self._restore_state()

    def _show_restart_needed(self, value: Any) -> None:
        del value  # Unused.
        ba.screenmessage(ba.Lstr(resource=self._r + '.mustRestartText'),
                         color=(1, 1, 0))

    def _on_lang_inform_value_change(self, val: bool) -> None:
        _ba.add_transaction({
            'type': 'SET_MISC_VAL',
            'name': 'langInform',
            'value': val
        })
        _ba.run_transactions()

    def _on_vr_test_press(self) -> None:
        from bastd.ui.settings.vrtesting import VRTestingWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            VRTestingWindow(transition='in_right').get_root_widget())

    def _on_net_test_press(self) -> None:
        from bastd.ui.settings.nettesting import NetTestingWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            NetTestingWindow(transition='in_right').get_root_widget())

    def _on_friend_promo_code_press(self) -> None:
        from bastd.ui import appinvite
        from bastd.ui import account
        if _ba.get_account_state() != 'signed_in':
            account.show_sign_in_prompt()
            return
        appinvite.handle_app_invites_press()

    def _on_plugins_button_press(self) -> None:
        from bastd.ui.settings.plugins import PluginSettingsWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            PluginSettingsWindow(
                origin_widget=self._plugins_button).get_root_widget())

    def _on_promo_code_press(self) -> None:
        from bastd.ui.promocode import PromoCodeWindow
        from bastd.ui.account import show_sign_in_prompt

        # We have to be logged in for promo-codes to work.
        if _ba.get_account_state() != 'signed_in':
            show_sign_in_prompt()
            return
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            PromoCodeWindow(
                origin_widget=self._promo_code_button).get_root_widget())

    def _on_benchmark_press(self) -> None:
        from bastd.ui.debug import DebugWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            DebugWindow(transition='in_right').get_root_widget())

    def _save_state(self) -> None:
        # pylint: disable=too-many-branches
        try:
            sel = self._root_widget.get_selected_child()
            if sel == self._scrollwidget:
                sel = self._subcontainer.get_selected_child()
                if sel == self._vr_test_button:
                    sel_name = 'VRTest'
                elif sel == self._net_test_button:
                    sel_name = 'NetTest'
                elif sel == self._promo_code_button:
                    sel_name = 'PromoCode'
                elif sel == self._benchmarks_button:
                    sel_name = 'Benchmarks'
                elif sel == self._kick_idle_players_check_box.widget:
                    sel_name = 'KickIdlePlayers'
                elif sel == self._disable_camera_shake_check_box.widget:
                    sel_name = 'DisableCameraShake'
                elif (self._always_use_internal_keyboard_check_box is not None
                      and sel
                      == self._always_use_internal_keyboard_check_box.widget):
                    sel_name = 'AlwaysUseInternalKeyboard'
                elif (self._disable_gyro_check_box is not None
                      and sel == self._disable_gyro_check_box.widget):
                    sel_name = 'DisableGyro'
                elif (self._language_popup is not None
                      and sel == self._language_popup.get_button()):
                    sel_name = 'Languages'
                elif sel == self._translation_editor_button:
                    sel_name = 'TranslationEditor'
                elif sel == self._show_user_mods_button:
                    sel_name = 'ShowUserMods'
                elif sel == self._plugins_button:
                    sel_name = 'Plugins'
                elif sel == self._modding_guide_button:
                    sel_name = 'ModdingGuide'
                elif sel == self._language_inform_checkbox:
                    sel_name = 'LangInform'
                else:
                    raise ValueError(f'unrecognized selection \'{sel}\'')
            elif sel == self._back_button:
                sel_name = 'Back'
            else:
                raise ValueError(f'unrecognized selection \'{sel}\'')
            ba.app.ui.window_states[self.__class__.__name__] = {
                'sel_name': sel_name
            }
        except Exception:
            ba.print_exception(f'Error saving state for {self.__class__}')

    def _restore_state(self) -> None:
        # pylint: disable=too-many-branches
        try:
            sel_name = ba.app.ui.window_states.get(self.__class__.__name__,
                                                   {}).get('sel_name')
            if sel_name == 'Back':
                sel = self._back_button
            else:
                ba.containerwidget(edit=self._root_widget,
                                   selected_child=self._scrollwidget)
                if sel_name == 'VRTest':
                    sel = self._vr_test_button
                elif sel_name == 'NetTest':
                    sel = self._net_test_button
                elif sel_name == 'PromoCode':
                    sel = self._promo_code_button
                elif sel_name == 'Benchmarks':
                    sel = self._benchmarks_button
                elif sel_name == 'KickIdlePlayers':
                    sel = self._kick_idle_players_check_box.widget
                elif sel_name == 'DisableCameraShake':
                    sel = self._disable_camera_shake_check_box.widget
                elif (sel_name == 'AlwaysUseInternalKeyboard'
                      and self._always_use_internal_keyboard_check_box
                      is not None):
                    sel = self._always_use_internal_keyboard_check_box.widget
                elif (sel_name == 'DisableGyro'
                      and self._disable_gyro_check_box is not None):
                    sel = self._disable_gyro_check_box.widget
                elif (sel_name == 'Languages'
                      and self._language_popup is not None):
                    sel = self._language_popup.get_button()
                elif sel_name == 'TranslationEditor':
                    sel = self._translation_editor_button
                elif sel_name == 'ShowUserMods':
                    sel = self._show_user_mods_button
                elif sel_name == 'Plugins':
                    sel = self._plugins_button
                elif sel_name == 'ModdingGuide':
                    sel = self._modding_guide_button
                elif sel_name == 'LangInform':
                    sel = self._language_inform_checkbox
                else:
                    sel = None
                if sel is not None:
                    ba.containerwidget(edit=self._subcontainer,
                                       selected_child=sel,
                                       visible_child=sel)
        except Exception:
            ba.print_exception(f'Error restoring state for {self.__class__}')

    def _on_menu_open(self) -> None:
        self._menu_open = True

    def _on_menu_close(self) -> None:
        self._menu_open = False

    def _on_menu_choice(self, choice: str) -> None:
        ba.setlanguage(None if choice == 'Auto' else choice)
        self._save_state()
        ba.timer(0.1, ba.WeakCall(self._rebuild), timetype=ba.TimeType.REAL)

    def _completed_langs_cb(self, results: Optional[Dict[str, Any]]) -> None:
        if results is not None and results['langs'] is not None:
            self._complete_langs_list = results['langs']
            self._complete_langs_error = False
        else:
            self._complete_langs_list = None
            self._complete_langs_error = True
        ba.timer(0.001,
                 ba.WeakCall(self._update_lang_status),
                 timetype=ba.TimeType.REAL)

    def _do_back(self) -> None:
        from bastd.ui.settings.allsettings import AllSettingsWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget,
                           transition=self._transition_out)
        ba.app.ui.set_main_menu_window(
            AllSettingsWindow(transition='in_left').get_root_widget())
