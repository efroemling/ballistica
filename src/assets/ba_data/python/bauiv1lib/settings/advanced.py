# Released under the MIT License. See LICENSE for details.
#
# pylint: disable=too-many-lines

"""UI functionality for advanced settings."""

from __future__ import annotations

import os
import logging
from typing import TYPE_CHECKING, override

from bacommon.locale import LocaleResolved
from bauiv1lib.popup import PopupMenu
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any


class AdvancedSettingsWindow(bui.MainWindow):
    """Window for editing advanced app settings."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-statements

        if bui.app.classic is None:
            raise RuntimeError('This requires classic support.')

        # Preload some modules we use in a background thread so we won't
        # have a visual hitch when the user taps them.
        bui.app.threadpool.submit_no_wait(self._preload_modules)

        app = bui.app
        assert app.classic is not None

        uiscale = bui.app.ui_v1.uiscale
        self._width = 1030.0 if uiscale is bui.UIScale.SMALL else 670.0
        self._height = (
            490.0
            if uiscale is bui.UIScale.SMALL
            else 450.0 if uiscale is bui.UIScale.MEDIUM else 600.0
        )
        self._lang_status_text: bui.Widget | None = None

        self._spacing = 32
        self._menu_open = False

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            2.2
            if uiscale is bui.UIScale.SMALL
            else 1.3 if uiscale is bui.UIScale.MEDIUM else 0.9
        )

        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        target_width = min(self._width - 80, screensize[0] / scale)
        target_height = min(self._height - 80, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * self._height + 0.5 * target_height + 30.0

        self._scroll_width = target_width
        self._scroll_height = target_height - 25
        scroll_bottom = yoffs - 56 - self._scroll_height

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        self._prev_lang: str | None = ''
        self._prev_lang_list: list[str] = []
        self._complete_langs_list: list | None = None
        self._complete_langs_error = False
        self._language_popup: PopupMenu | None = None

        # In vr-mode, the internal keyboard is currently the *only* option,
        # so no need to show this.
        self._show_always_use_internal_keyboard = not app.env.vr

        self._sub_width = min(550, self._scroll_width * 0.95)
        self._sub_height = 870.0

        if self._show_always_use_internal_keyboard:
            self._sub_height += 62

        self._show_disable_gyro = app.classic.platform in {'ios', 'android'}
        if self._show_disable_gyro:
            self._sub_height += 42

        self._show_use_insecure_connections = True
        if self._show_use_insecure_connections:
            self._sub_height += 82

        self._do_vr_test_button = app.env.vr
        self._do_net_test_button = True
        self._extra_button_spacing = self._spacing * 2.5

        if self._do_vr_test_button:
            self._sub_height += self._extra_button_spacing
        if self._do_net_test_button:
            self._sub_height += self._extra_button_spacing
        self._sub_height += self._spacing * 2.0  # plugins
        self._sub_height += self._spacing * 2.0  # dev tools

        self._r = 'settingsWindowAdvanced'

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
            self._back_button = None
        else:
            self._back_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(50, yoffs - 48),
                size=(60, 60),
                scale=0.8,
                autoselect=True,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )

        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5,
                yoffs - (43 if uiscale is bui.UIScale.SMALL else 25),
            ),
            size=(0, 0),
            scale=0.75 if uiscale is bui.UIScale.SMALL else 1.0,
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=app.ui_v1.title_color,
            h_align='center',
            v_align='center',
        )

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            size=(self._scroll_width, self._scroll_height),
            position=(
                self._width * 0.5 - self._scroll_width * 0.5,
                scroll_bottom,
            ),
            simple_culling_v=20.0,
            highlight=False,
            center_small_content_horizontally=True,
            selection_loops_to_parent=True,
            border_opacity=0.4,
        )
        bui.widget(edit=self._scrollwidget, right_widget=self._scrollwidget)
        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(self._sub_width, self._sub_height),
            background=False,
            selection_loops_to_parent=True,
        )

        self._rebuild()

        # Rebuild periodically to pick up language changes/additions/etc.
        self._rebuild_timer = bui.AppTimer(
            1.0, bui.WeakCall(self._rebuild), repeat=True
        )

        # Fetch the list of completed languages.
        bui.app.classic.master_server_v1_get(
            'bsLangGetCompleted',
            {'b': app.env.engine_build_number},
            callback=bui.WeakCall(self._completed_langs_cb),
        )

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

    @override
    def on_main_window_close(self) -> None:
        self._save_state()

    @staticmethod
    def _preload_modules() -> None:
        """Preload stuff in bg thread to avoid hitches in logic thread"""
        from babase import modutils as _unused2
        from bauiv1lib import config as _unused1
        from bauiv1lib.settings import vrtesting as _unused3
        from bauiv1lib.settings import nettesting as _unused4
        from bauiv1lib import appinvite as _unused5
        from bauiv1lib import account as _unused6
        from bauiv1lib import sendinfo as _unused7
        from bauiv1lib.settings import benchmarks as _unused8
        from bauiv1lib.settings import plugins as _unused9
        from bauiv1lib.settings import devtools as _unused10

    def _update_lang_status(self) -> None:
        if self._complete_langs_list is not None:
            up_to_date = bui.app.lang.language in self._complete_langs_list
            bui.textwidget(
                edit=self._lang_status_text,
                text=(
                    ''
                    if bui.app.lang.language == 'Test'
                    else (
                        bui.Lstr(
                            resource=f'{self._r}.translationNoUpdateNeededText'
                        )
                        if up_to_date
                        else bui.Lstr(
                            resource=f'{self._r}.translationUpdateNeededText'
                        )
                    )
                ),
                color=(
                    (0.2, 1.0, 0.2, 0.8) if up_to_date else (1.0, 0.2, 0.2, 0.8)
                ),
            )
        else:
            bui.textwidget(
                edit=self._lang_status_text,
                text=(
                    bui.Lstr(resource=f'{self._r}.translationFetchErrorText')
                    if self._complete_langs_error
                    else bui.Lstr(
                        resource=f'{self._r}.translationFetchingStatusText'
                    )
                ),
                color=(
                    (1.0, 0.5, 0.2)
                    if self._complete_langs_error
                    else (0.7, 0.7, 0.7)
                ),
            )

    def _rebuild(self) -> None:
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals

        from bauiv1lib.config import ConfigCheckBox
        from babase.modutils import show_user_scripts

        plus = bui.app.plus
        assert plus is not None

        locale_ss = bui.app.locale

        # Build a list of long-values for locales we are able to display.
        available_languages = sorted(
            lr.locale.long_value
            for lr in LocaleResolved
            if (locale_ss.can_display_locale(lr.locale))
        )

        # Don't rebuild if the menu is open or if our language and
        # language-list hasn't changed.

        # NOTE - although we now support widgets updating their own
        # translations, we still change the label formatting on the
        # language menu based on the language so still need this.
        # ...however we could make this more limited to it only rebuilds
        # that one menu instead of everything.
        if self._menu_open or (
            self._prev_lang == bui.app.config.get('Lang', None)
            and self._prev_lang_list == available_languages
        ):
            return
        self._prev_lang = bui.app.config.get('Lang', None)
        self._prev_lang_list = available_languages

        # Clear out our sub-container.
        children = self._subcontainer.get_children()
        for child in children:
            child.delete()

        v = self._sub_height - 35

        v -= self._spacing * 1.2

        # Update our existing back button and title.
        if self._back_button is not None:
            bui.buttonwidget(
                edit=self._back_button, label=bui.Lstr(resource='backText')
            )
            bui.buttonwidget(
                edit=self._back_button, label=bui.charstr(bui.SpecialChar.BACK)
            )

        bui.textwidget(
            edit=self._title_text,
            text=bui.Lstr(resource=f'{self._r}.titleText'),
        )

        this_button_width = 410

        assert bui.app.classic is not None
        bui.textwidget(
            parent=self._subcontainer,
            position=(70, v + 10),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.languageText'),
            maxwidth=150,
            scale=1.2,
            color=bui.app.ui_v1.title_color,
            h_align='left',
            v_align='center',
        )

        cur_lang = bui.app.locale.current_locale.long_value

        # We have a special dict of language names in that language so
        # we don't have to go digging through each full language.
        try:
            import json

            with open(
                os.path.join(
                    bui.app.env.data_directory,
                    'ba_data',
                    'data',
                    'langdata.json',
                ),
                encoding='utf-8',
            ) as infile:
                lang_names_translated = json.loads(infile.read())[
                    'lang_names_translated'
                ]
        except Exception:
            logging.exception('Error reading lang data.')
            lang_names_translated = {}

        langs_translated = {}
        for lang in available_languages:
            langs_translated[lang] = lang_names_translated.get(lang, lang)

        langs_full = {}
        for lang in available_languages:
            lang_translated = bui.Lstr(translate=('languages', lang)).evaluate()
            if langs_translated[lang] == lang_translated:
                langs_full[lang] = lang_translated
            else:
                langs_full[lang] = (
                    langs_translated[lang] + ' (' + lang_translated + ')'
                )

        self._language_popup = PopupMenu(
            parent=self._subcontainer,
            position=(210, v - 19),
            width=250,
            opening_call=bui.WeakCall(self._on_menu_open),
            closing_call=bui.WeakCall(self._on_menu_close),
            autoselect=False,
            on_value_change_call=bui.WeakCall(self._on_menu_choice),
            choices=['Auto'] + available_languages,
            button_size=(300, 60),
            choices_display=(
                [
                    bui.Lstr(
                        value=(
                            bui.Lstr(resource='autoText').evaluate()
                            + ' ('
                            + bui.Lstr(
                                translate=(
                                    'languages',
                                    bui.app.locale.default_locale.long_value,
                                )
                            ).evaluate()
                            + ')'
                        )
                    )
                ]
                + [bui.Lstr(value=langs_full[l]) for l in available_languages]
            ),
            current_choice=cur_lang,
        )

        v -= self._spacing * 1.8

        bui.textwidget(
            parent=self._subcontainer,
            position=(90, v + 10),
            size=(0, 0),
            text=bui.Lstr(
                resource=f'{self._r}.helpTranslateText',
                subs=[('${APP_NAME}', bui.Lstr(resource='titleText'))],
            ),
            maxwidth=self._sub_width * 0.9,
            max_height=55,
            flatness=1.0,
            scale=0.65,
            color=(0.4, 0.9, 0.4, 0.8),
            h_align='left',
            v_align='center',
        )
        v -= self._spacing * 1.9
        this_button_width = 410
        self._translation_editor_button = bui.buttonwidget(
            parent=self._subcontainer,
            position=(self._sub_width / 2 - this_button_width / 2, v - 24),
            size=(this_button_width, 60),
            label=bui.Lstr(
                resource=f'{self._r}.translationEditorButtonText',
                subs=[('${APP_NAME}', bui.Lstr(resource='titleText'))],
            ),
            autoselect=True,
            on_activate_call=bui.Call(
                bui.open_url, 'https://legacy.ballistica.net/translate'
            ),
        )

        self._lang_status_text = bui.textwidget(
            parent=self._subcontainer,
            position=(self._sub_width * 0.5, v - 40),
            size=(0, 0),
            text='',
            flatness=1.0,
            scale=0.63,
            h_align='center',
            v_align='center',
            maxwidth=400.0,
        )
        self._update_lang_status()
        v -= 50

        lang_inform = plus.get_v1_account_misc_val('langInform', False)

        self._language_inform_checkbox = cbw = bui.checkboxwidget(
            parent=self._subcontainer,
            position=(50, v - 50),
            size=(self._sub_width - 100, 30),
            autoselect=True,
            maxwidth=430,
            textcolor=(0.8, 0.8, 0.8),
            value=lang_inform,
            text=bui.Lstr(resource=f'{self._r}.translationInformMe'),
            on_value_change_call=bui.WeakCall(
                self._on_lang_inform_value_change
            ),
        )

        bui.widget(
            edit=self._translation_editor_button,
            down_widget=cbw,
            up_widget=self._language_popup.get_button(),
        )

        v -= self._spacing * 3.0

        self._kick_idle_players_check_box = ConfigCheckBox(
            parent=self._subcontainer,
            position=(50, v),
            size=(self._sub_width - 100, 30),
            configkey='Kick Idle Players',
            displayname=bui.Lstr(resource=f'{self._r}.kickIdlePlayersText'),
            scale=1.0,
            maxwidth=430,
        )

        v -= 42
        self._show_game_ping_check_box = ConfigCheckBox(
            parent=self._subcontainer,
            position=(50, v),
            size=(self._sub_width - 100, 30),
            configkey='Show Ping',
            displayname=bui.Lstr(resource=f'{self._r}.showInGamePingText'),
            scale=1.0,
            maxwidth=430,
        )

        v -= 42
        self._show_demos_when_idle_check_box = ConfigCheckBox(
            parent=self._subcontainer,
            position=(50, v),
            size=(self._sub_width - 100, 30),
            configkey='Show Demos When Idle',
            displayname=bui.Lstr(resource=f'{self._r}.showDemosWhenIdleText'),
            scale=1.0,
            maxwidth=430,
        )

        v -= 42
        self._show_deprecated_login_types_check_box = ConfigCheckBox(
            parent=self._subcontainer,
            position=(50, v),
            size=(self._sub_width - 100, 30),
            configkey='Show Deprecated Login Types',
            displayname=bui.Lstr(
                resource=f'{self._r}.showDeprecatedLoginTypesText'
            ),
            scale=1.0,
            maxwidth=430,
        )

        v -= 42
        self._disable_camera_shake_check_box = ConfigCheckBox(
            parent=self._subcontainer,
            position=(50, v),
            size=(self._sub_width - 100, 30),
            configkey='Disable Camera Shake',
            displayname=bui.Lstr(resource=f'{self._r}.disableCameraShakeText'),
            scale=1.0,
            maxwidth=430,
        )

        self._disable_gyro_check_box: ConfigCheckBox | None = None
        if self._show_disable_gyro:
            v -= 42
            self._disable_gyro_check_box = ConfigCheckBox(
                parent=self._subcontainer,
                position=(50, v),
                size=(self._sub_width - 100, 30),
                configkey='Disable Camera Gyro',
                displayname=bui.Lstr(
                    resource=f'{self._r}.disableCameraGyroscopeMotionText'
                ),
                scale=1.0,
                maxwidth=430,
            )

        self._use_insecure_connections_check_box: ConfigCheckBox | None
        if self._show_use_insecure_connections:
            v -= 42
            self._use_insecure_connections_check_box = ConfigCheckBox(
                parent=self._subcontainer,
                position=(50, v),
                size=(self._sub_width - 100, 30),
                configkey='Use Insecure Connections',
                autoselect=True,
                # displayname='USE INSECURE CONNECTIONS',
                displayname=bui.Lstr(
                    resource=(f'{self._r}.insecureConnectionsText')
                ),
                # displayname=bui.Lstr(
                #     resource=f'{self._r}.alwaysUseInternalKeyboardText'
                # ),
                scale=1.0,
                maxwidth=430,
            )
            bui.textwidget(
                parent=self._subcontainer,
                position=(90, v - 20),
                size=(0, 0),
                # text=(
                #     'not recommended, but may allow online play\n'
                #     'from restricted countries or networks'
                # ),
                text=bui.Lstr(
                    resource=(f'{self._r}.insecureConnectionsDescriptionText')
                ),
                maxwidth=400,
                flatness=1.0,
                scale=0.65,
                color=(0.4, 0.9, 0.4, 0.8),
                h_align='left',
                v_align='center',
            )
            v -= 40
        else:
            self._use_insecure_connections_check_box = None

        self._always_use_internal_keyboard_check_box: ConfigCheckBox | None
        if self._show_always_use_internal_keyboard:
            v -= 42
            self._always_use_internal_keyboard_check_box = ConfigCheckBox(
                parent=self._subcontainer,
                position=(50, v),
                size=(self._sub_width - 100, 30),
                configkey='Always Use Internal Keyboard',
                autoselect=True,
                displayname=bui.Lstr(
                    resource=f'{self._r}.alwaysUseInternalKeyboardText'
                ),
                scale=1.0,
                maxwidth=430,
            )
            bui.textwidget(
                parent=self._subcontainer,
                position=(90, v - 10),
                size=(0, 0),
                text=bui.Lstr(
                    resource=(
                        f'{self._r}.alwaysUseInternalKeyboardDescriptionText'
                    )
                ),
                maxwidth=400,
                flatness=1.0,
                scale=0.65,
                color=(0.4, 0.9, 0.4, 0.8),
                h_align='left',
                v_align='center',
            )
            v -= 20
        else:
            self._always_use_internal_keyboard_check_box = None

        v -= self._spacing * 2.1

        this_button_width = 410
        self._modding_guide_button = bui.buttonwidget(
            parent=self._subcontainer,
            position=(self._sub_width / 2 - this_button_width / 2, v - 10),
            size=(this_button_width, 60),
            autoselect=True,
            label=bui.Lstr(resource=f'{self._r}.moddingGuideText'),
            text_scale=1.0,
            on_activate_call=bui.Call(
                bui.open_url, 'https://ballistica.net/wiki/modding-guide'
            ),
        )

        v -= self._spacing * 2.0

        self._dev_tools_button = bui.buttonwidget(
            parent=self._subcontainer,
            position=(self._sub_width / 2 - this_button_width / 2, v - 10),
            size=(this_button_width, 60),
            autoselect=True,
            label=bui.Lstr(resource=f'{self._r}.devToolsText'),
            text_scale=1.0,
            on_activate_call=self._on_dev_tools_button_press,
        )

        if self._show_always_use_internal_keyboard:
            assert self._always_use_internal_keyboard_check_box is not None
            bui.widget(
                edit=self._always_use_internal_keyboard_check_box.widget,
                down_widget=self._modding_guide_button,
            )
            bui.widget(
                edit=self._modding_guide_button,
                up_widget=self._always_use_internal_keyboard_check_box.widget,
            )
        else:
            # ew.
            next_widget_up = (
                self._disable_gyro_check_box.widget
                if self._disable_gyro_check_box is not None
                else self._disable_camera_shake_check_box.widget
            )
            bui.widget(
                edit=self._modding_guide_button,
                up_widget=next_widget_up,
            )
            bui.widget(
                edit=next_widget_up,
                down_widget=self._modding_guide_button,
            )

        v -= self._spacing * 2.0

        self._show_user_mods_button = bui.buttonwidget(
            parent=self._subcontainer,
            position=(self._sub_width / 2 - this_button_width / 2, v - 10),
            size=(this_button_width, 60),
            autoselect=True,
            label=bui.Lstr(resource=f'{self._r}.showUserModsText'),
            text_scale=1.0,
            on_activate_call=show_user_scripts,
        )

        v -= self._spacing * 2.0

        self._plugins_button = bui.buttonwidget(
            parent=self._subcontainer,
            position=(self._sub_width / 2 - this_button_width / 2, v - 10),
            size=(this_button_width, 60),
            autoselect=True,
            label=bui.Lstr(resource='pluginsText'),
            text_scale=1.0,
            on_activate_call=self._on_plugins_button_press,
        )

        v -= self._spacing * 0.6

        self._vr_test_button: bui.Widget | None
        if self._do_vr_test_button:
            v -= self._extra_button_spacing
            self._vr_test_button = bui.buttonwidget(
                parent=self._subcontainer,
                position=(self._sub_width / 2 - this_button_width / 2, v - 14),
                size=(this_button_width, 60),
                autoselect=True,
                label=bui.Lstr(resource=f'{self._r}.vrTestingText'),
                text_scale=1.0,
                on_activate_call=self._on_vr_test_press,
            )
        else:
            self._vr_test_button = None

        self._net_test_button: bui.Widget | None
        if self._do_net_test_button:
            v -= self._extra_button_spacing
            self._net_test_button = bui.buttonwidget(
                parent=self._subcontainer,
                position=(self._sub_width / 2 - this_button_width / 2, v - 14),
                size=(this_button_width, 60),
                autoselect=True,
                label=bui.Lstr(resource=f'{self._r}.netTestingText'),
                text_scale=1.0,
                on_activate_call=self._on_net_test_press,
            )
        else:
            self._net_test_button = None

        v -= 70
        self._benchmarks_button = bui.buttonwidget(
            parent=self._subcontainer,
            position=(self._sub_width / 2 - this_button_width / 2, v - 14),
            size=(this_button_width, 60),
            autoselect=True,
            label=bui.Lstr(resource=f'{self._r}.benchmarksText'),
            text_scale=1.0,
            on_activate_call=self._on_benchmark_press,
        )

        v -= 100
        self._send_info_button = bui.buttonwidget(
            parent=self._subcontainer,
            position=(self._sub_width / 2 - this_button_width / 2, v - 14),
            size=(this_button_width, 60),
            autoselect=True,
            label=bui.Lstr(resource=f'{self._r}.sendInfoText'),
            text_scale=1.0,
            on_activate_call=self._on_send_info_press,
        )

        for child in self._subcontainer.get_children():
            bui.widget(edit=child, show_buffer_bottom=30, show_buffer_top=20)

        pbtn = bui.get_special_widget('squad_button')
        bui.widget(edit=self._scrollwidget, right_widget=pbtn)
        if self._back_button is None:
            bui.widget(
                edit=self._scrollwidget,
                left_widget=bui.get_special_widget('back_button'),
            )

        self._restore_state()

    def _show_restart_needed(self, value: Any) -> None:
        del value  # Unused.
        bui.screenmessage(
            bui.Lstr(resource=f'{self._r}.mustRestartText'), color=(1, 1, 0)
        )

    def _on_lang_inform_value_change(self, val: bool) -> None:
        plus = bui.app.plus
        assert plus is not None
        plus.add_v1_account_transaction(
            {'type': 'SET_MISC_VAL', 'name': 'langInform', 'value': val}
        )
        plus.run_v1_account_transactions()

    def _on_vr_test_press(self) -> None:
        from bauiv1lib.settings.vrtesting import VRTestingWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(VRTestingWindow(transition='in_right'))

    def _on_net_test_press(self) -> None:
        from bauiv1lib.settings.nettesting import NetTestingWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(NetTestingWindow(transition='in_right'))

    def _on_friend_promo_code_press(self) -> None:
        from bauiv1lib import appinvite
        from bauiv1lib.account.signin import show_sign_in_prompt

        plus = bui.app.plus
        assert plus is not None

        if plus.get_v1_account_state() != 'signed_in':
            show_sign_in_prompt()
            return
        appinvite.handle_app_invites_press()

    def _on_plugins_button_press(self) -> None:
        from bauiv1lib.settings.plugins import PluginWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            PluginWindow(origin_widget=self._plugins_button)
        )

    def _on_dev_tools_button_press(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.devtools import DevToolsWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            DevToolsWindow(origin_widget=self._dev_tools_button)
        )

    def _on_send_info_press(self) -> None:
        from bauiv1lib.sendinfo import SendInfoWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            SendInfoWindow(origin_widget=self._send_info_button)
        )

    def _on_benchmark_press(self) -> None:
        from bauiv1lib.settings.benchmarks import BenchmarksAndStressTestsWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            BenchmarksAndStressTestsWindow(transition='in_right')
        )

    def _save_state(self) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        try:
            sel = self._root_widget.get_selected_child()
            if sel == self._scrollwidget:
                sel = self._subcontainer.get_selected_child()
                if sel == self._vr_test_button:
                    sel_name = 'VRTest'
                elif sel == self._net_test_button:
                    sel_name = 'NetTest'
                elif sel == self._send_info_button:
                    sel_name = 'SendInfo'
                elif sel == self._benchmarks_button:
                    sel_name = 'Benchmarks'
                elif sel == self._kick_idle_players_check_box.widget:
                    sel_name = 'KickIdlePlayers'
                elif sel == self._show_demos_when_idle_check_box.widget:
                    sel_name = 'ShowDemosWhenIdle'
                elif sel == self._show_deprecated_login_types_check_box.widget:
                    sel_name = 'ShowDeprecatedLoginTypes'
                elif sel == self._show_game_ping_check_box.widget:
                    sel_name = 'ShowPing'
                elif sel == self._disable_camera_shake_check_box.widget:
                    sel_name = 'DisableCameraShake'
                elif (
                    self._always_use_internal_keyboard_check_box is not None
                    and sel
                    == self._always_use_internal_keyboard_check_box.widget
                ):
                    sel_name = 'AlwaysUseInternalKeyboard'
                elif (
                    self._use_insecure_connections_check_box is not None
                    and sel == self._use_insecure_connections_check_box.widget
                ):
                    sel_name = 'UseInsecureConnections'
                elif (
                    self._disable_gyro_check_box is not None
                    and sel == self._disable_gyro_check_box.widget
                ):
                    sel_name = 'DisableGyro'
                elif (
                    self._language_popup is not None
                    and sel == self._language_popup.get_button()
                ):
                    sel_name = 'Languages'
                elif sel == self._translation_editor_button:
                    sel_name = 'TranslationEditor'
                elif sel == self._show_user_mods_button:
                    sel_name = 'ShowUserMods'
                elif sel == self._plugins_button:
                    sel_name = 'Plugins'
                elif sel == self._dev_tools_button:
                    sel_name = 'DevTools'
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
            assert bui.app.classic is not None
            bui.app.ui_v1.window_states[type(self)] = {'sel_name': sel_name}

        except Exception:
            logging.exception('Error saving state for %s.', self)

    def _restore_state(self) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        try:
            assert bui.app.classic is not None
            sel_name = bui.app.ui_v1.window_states.get(type(self), {}).get(
                'sel_name'
            )
            if sel_name == 'Back':
                sel = self._back_button
            else:
                bui.containerwidget(
                    edit=self._root_widget, selected_child=self._scrollwidget
                )
                if sel_name == 'VRTest':
                    sel = self._vr_test_button
                elif sel_name == 'NetTest':
                    sel = self._net_test_button
                elif sel_name == 'SendInfo':
                    sel = self._send_info_button
                elif sel_name == 'Benchmarks':
                    sel = self._benchmarks_button
                elif sel_name == 'KickIdlePlayers':
                    sel = self._kick_idle_players_check_box.widget
                elif sel_name == 'ShowDemosWhenIdle':
                    sel = self._show_demos_when_idle_check_box.widget
                elif sel_name == 'ShowDeprecatedLoginTypes':
                    sel = self._show_deprecated_login_types_check_box.widget
                elif sel_name == 'ShowPing':
                    sel = self._show_game_ping_check_box.widget
                elif sel_name == 'DisableCameraShake':
                    sel = self._disable_camera_shake_check_box.widget
                elif (
                    sel_name == 'AlwaysUseInternalKeyboard'
                    and self._always_use_internal_keyboard_check_box is not None
                ):
                    sel = self._always_use_internal_keyboard_check_box.widget
                elif (
                    sel_name == 'UseInsecureConnections'
                    and self._use_insecure_connections_check_box is not None
                ):
                    sel = self._use_insecure_connections_check_box.widget
                elif (
                    sel_name == 'DisableGyro'
                    and self._disable_gyro_check_box is not None
                ):
                    sel = self._disable_gyro_check_box.widget
                elif (
                    sel_name == 'Languages' and self._language_popup is not None
                ):
                    sel = self._language_popup.get_button()
                elif sel_name == 'TranslationEditor':
                    sel = self._translation_editor_button
                elif sel_name == 'ShowUserMods':
                    sel = self._show_user_mods_button
                elif sel_name == 'Plugins':
                    sel = self._plugins_button
                elif sel_name == 'DevTools':
                    sel = self._dev_tools_button
                elif sel_name == 'ModdingGuide':
                    sel = self._modding_guide_button
                elif sel_name == 'LangInform':
                    sel = self._language_inform_checkbox
                else:
                    sel = None
                if sel is not None:
                    bui.containerwidget(
                        edit=self._subcontainer,
                        selected_child=sel,
                        visible_child=sel,
                    )
        except Exception:
            logging.exception('Error restoring state for %s.', self)

    def _on_menu_open(self) -> None:
        self._menu_open = True

    def _on_menu_close(self) -> None:
        self._menu_open = False

    def _on_menu_choice(self, choice: str) -> None:

        cfg = bui.app.config
        cfgkey = 'Lang'

        if choice == 'Auto':
            if cfgkey in cfg:
                del cfg[cfgkey]
        else:
            cfg[cfgkey] = choice

        cfg.apply_and_commit()

        self._save_state()

        # bui.app.lang.setlanguage(None if choice == 'Auto' else choice)
        bui.apptimer(0.1, bui.WeakCall(self._rebuild))

    def _completed_langs_cb(self, results: dict[str, Any] | None) -> None:
        if results is not None and results['langs'] is not None:
            self._complete_langs_list = results['langs']
            self._complete_langs_error = False
        else:
            self._complete_langs_list = None
            self._complete_langs_error = True
        bui.apptimer(0.001, bui.WeakCall(self._update_lang_status))
