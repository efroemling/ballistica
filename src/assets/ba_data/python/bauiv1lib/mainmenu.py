# Released under the MIT License. See LICENSE for details.
#
"""Implements the main menu window."""

from __future__ import annotations

from typing import TYPE_CHECKING, override
import logging

import bauiv1 as bui
import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any, Callable


class MainMenuWindow(bui.MainWindow):
    """The main menu window."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):

        # Preload some modules we use in a background thread so we won't
        # have a visual hitch when the user taps them.
        bui.app.threadpool.submit_no_wait(self._preload_modules)

        bui.set_analytics_screen('Main Menu')
        self._show_remote_app_info_on_first_launch()

        uiscale = bui.app.ui_v1.uiscale

        # Make a vanilla container; we'll modify it to our needs in
        # refresh.
        super().__init__(
            root_widget=bui.containerwidget(
                toolbar_visibility=('menu_full_no_back')
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        # Grab this stuff in case it changes.
        # self._is_demo = bui.app.env.demo
        # self._is_arcade = bui.app.env.arcade

        self._tdelay = 0.0
        self._t_delay_inc = 0.02
        self._t_delay_play = 1.7
        self._use_autoselect = True
        self._button_width = 200.0
        self._button_height = 45.0
        self._width = 100.0
        self._height = 100.0
        self._demo_menu_button: bui.Widget | None = None
        self._gather_button: bui.Widget | None = None
        self._play_button: bui.Widget | None = None
        self._watch_button: bui.Widget | None = None
        self._how_to_play_button: bui.Widget | None = None
        self._credits_button: bui.Widget | None = None

        self._refresh()

        self._restore_state()

    @override
    def on_main_window_close(self) -> None:
        self._save_state()

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

    @staticmethod
    def _preload_modules() -> None:
        """Preload modules we use; avoids hitches (called in bg thread)."""
        # pylint: disable=cyclic-import
        import bauiv1lib.getremote as _unused
        import bauiv1lib.confirm as _unused2
        import bauiv1lib.account.settings as _unused5
        import bauiv1lib.store.browser as _unused6
        import bauiv1lib.credits as _unused7
        import bauiv1lib.help as _unused8
        import bauiv1lib.settings.allsettings as _unused9
        import bauiv1lib.gather as _unused10
        import bauiv1lib.watch as _unused11
        import bauiv1lib.play as _unused12

    def _show_remote_app_info_on_first_launch(self) -> None:
        app = bui.app
        assert app.classic is not None

        # The first time the non-in-game menu pops up, we might wanna
        # show a 'get-remote-app' dialog in front of it.
        if app.classic.first_main_menu:
            app.classic.first_main_menu = False
            try:
                force_test = False
                bs.get_local_active_input_devices_count()
                if (
                    (app.env.tv or app.classic.platform == 'mac')
                    and bui.app.config.get('launchCount', 0) <= 1
                ) or force_test:

                    def _check_show_bs_remote_window() -> None:
                        try:
                            from bauiv1lib.getremote import GetBSRemoteWindow

                            bui.getsound('swish').play()
                            GetBSRemoteWindow()
                        except Exception:
                            logging.exception(
                                'Error showing get-remote window.'
                            )

                    bui.apptimer(2.5, _check_show_bs_remote_window)
            except Exception:
                logging.exception('Error showing get-remote-app info.')

    def get_play_button(self) -> bui.Widget | None:
        """Return the play button."""
        return self._play_button

    def _refresh(self) -> None:
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals

        classic = bui.app.classic
        assert classic is not None

        # Clear everything that was there.
        children = self._root_widget.get_children()
        for child in children:
            child.delete()

        self._tdelay = 0.0
        self._t_delay_inc = 0.0
        self._t_delay_play = 0.0
        self._button_width = 200.0
        self._button_height = 45.0

        self._r = 'mainMenu'

        app = bui.app
        assert app.classic is not None
        uiscale = app.ui_v1.uiscale

        # Temp note about UI changes.
        if bool(False):
            bui.textwidget(
                parent=self._root_widget,
                position=(
                    (-400, 400)
                    if uiscale is bui.UIScale.LARGE
                    else (
                        (-270, 320)
                        if uiscale is bui.UIScale.MEDIUM
                        else (-280, 280)
                    )
                ),
                size=(0, 0),
                scale=0.4,
                flatness=1.0,
                text=(
                    'WARNING: This build contains a revamped UI\n'
                    'which is still a work-in-progress. A number\n'
                    'of features are not currently functional or\n'
                    'contain bugs. To go back to the stable legacy UI,\n'
                    'grab version 1.7.36 from ballistica.net'
                ),
                h_align='left',
                v_align='top',
            )

        self._have_quit_button = app.classic.platform in (
            'windows',
            'mac',
            'linux',
        )

        if not classic.did_menu_intro:
            self._tdelay = 1.6
            self._t_delay_inc = 0.03
            classic.did_menu_intro = True

        td1 = 2
        td2 = 1
        td3 = 0
        td4 = -1
        td5 = -2

        self._width = 400.0
        self._height = 200.0

        play_button_width = self._button_width * 0.65
        play_button_height = self._button_height * 1.1
        play_button_scale = 1.7
        hspace = 20.0
        side_button_width = self._button_width * 0.4
        side_button_height = side_button_width
        side_button_scale = 0.95
        side_button_y_offs = 5.0
        hspace2 = 15.0
        side_button_2_width = self._button_width * 1.0
        side_button_2_height = side_button_2_width * 0.3
        side_button_2_y_offs = 10.0
        side_button_2_scale = 0.5

        if uiscale is bui.UIScale.SMALL:
            # We're a generally widescreen shaped window, so bump our
            # overall scale up a bit when screen width is wider than safe
            # bounds to take advantage of the extra space.
            screensize = bui.get_virtual_screen_size()
            safesize = bui.get_virtual_safe_area_size()
            root_widget_scale = min(1.55, 1.3 * screensize[0] / safesize[0])
            button_y_offs = -20.0
            self._button_height *= 1.3
        elif uiscale is bui.UIScale.MEDIUM:
            root_widget_scale = 1.3
            button_y_offs = -55.0
            self._button_height *= 1.25
        else:
            root_widget_scale = 1.0
            button_y_offs = -90.0
            self._button_height *= 1.2

        bui.containerwidget(
            edit=self._root_widget,
            size=(self._width, self._height),
            background=False,
            scale=root_widget_scale,
        )

        # Version/copyright info.
        thistdelay = self._tdelay + td3 * self._t_delay_inc
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, button_y_offs - 10),
            size=(0, 0),
            scale=0.4,
            flatness=1.0,
            color=(1, 1, 1, 0.3),
            text=(
                f'{app.env.engine_version}'
                f' build {app.env.engine_build_number}.'
                f' Copyright 2011-2025 Eric Froemling.'
            ),
            h_align='center',
            v_align='center',
            # transition_delay=self._t_delay_play,
            transition_delay=thistdelay,
        )

        variant = bui.app.env.variant
        vart = type(variant)
        arcade_or_demo = variant is vart.ARCADE or variant is vart.DEMO

        # In kiosk mode, provide a button to get back to the kiosk menu.
        if arcade_or_demo:
            # h, v, scale = positions[self._p_index]
            h = self._width * 0.5
            v = button_y_offs
            scale = 1.0
            this_b_width = self._button_width * 0.4 * scale
            # demo_menu_delay = (
            #     0.0
            #     if self._t_delay_play == 0.0
            #     else max(0, self._t_delay_play + 0.1)
            # )
            demo_menu_delay = 0.0
            self._demo_menu_button = bui.buttonwidget(
                parent=self._root_widget,
                id='demo',
                position=(self._width * 0.5 - this_b_width * 0.5, v + 90),
                size=(this_b_width, 45),
                autoselect=True,
                color=(0.45, 0.55, 0.45),
                textcolor=(0.7, 0.8, 0.7),
                label=bui.Lstr(
                    resource=(
                        'modeArcadeText'
                        if variant is vart.ARCADE
                        else 'modeDemoText'
                    )
                ),
                transition_delay=demo_menu_delay,
                on_activate_call=self.main_window_back,
            )
        else:
            self._demo_menu_button = None

        # Gather button
        h = self._width * 0.5
        h = (
            self._width * 0.5
            - play_button_width * play_button_scale * 0.5
            - hspace
            - side_button_width * side_button_scale * 0.5
        )
        v = button_y_offs + side_button_y_offs

        thistdelay = self._tdelay + td2 * self._t_delay_inc
        self._gather_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(h - side_button_width * side_button_scale * 0.5, v),
            size=(side_button_width, side_button_height),
            scale=side_button_scale,
            autoselect=self._use_autoselect,
            button_type='square',
            label='',
            transition_delay=thistdelay,
            on_activate_call=self._gather_press,
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(h, v + side_button_height * side_button_scale * 0.25),
            size=(0, 0),
            scale=0.75,
            transition_delay=thistdelay,
            draw_controller=self._gather_button,
            color=(0.75, 1.0, 0.7),
            maxwidth=side_button_width * side_button_scale * 0.8,
            text=bui.Lstr(resource='gatherWindow.titleText'),
            h_align='center',
            v_align='center',
        )
        icon_size = side_button_width * side_button_scale * 0.63
        bui.imagewidget(
            parent=self._root_widget,
            size=(icon_size, icon_size),
            draw_controller=self._gather_button,
            transition_delay=thistdelay,
            position=(
                h - 0.5 * icon_size,
                v
                + 0.65 * side_button_height * side_button_scale
                - 0.5 * icon_size,
            ),
            texture=bui.gettexture('usersButton'),
        )
        thistdelay = self._tdelay + td1 * self._t_delay_inc

        h -= (
            side_button_width * side_button_scale * 0.5
            + hspace2
            + side_button_2_width * side_button_2_scale
        )
        v = button_y_offs + side_button_2_y_offs

        self._how_to_play_button = bui.buttonwidget(
            parent=self._root_widget,
            id='howtoplay',
            position=(h, v),
            autoselect=self._use_autoselect,
            size=(side_button_2_width, side_button_2_height * 2.0),
            button_type='square',
            scale=side_button_2_scale,
            label=bui.Lstr(resource=f'{self._r}.howToPlayText'),
            transition_delay=thistdelay,
            on_activate_call=self._howtoplay,
        )
        bui.widget(
            edit=self._how_to_play_button,
            left_widget=bui.get_special_widget('settings_button'),
        )

        # Play button.
        h = self._width * 0.5
        v = button_y_offs
        assert play_button_width is not None
        assert play_button_height is not None
        thistdelay = self._tdelay + td3 * self._t_delay_inc
        self._play_button = start_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(h - play_button_width * 0.5 * play_button_scale, v),
            size=(play_button_width, play_button_height),
            autoselect=self._use_autoselect,
            scale=play_button_scale,
            text_res_scale=2.0,
            label=bui.Lstr(resource='playText'),
            transition_delay=thistdelay,
            on_activate_call=self._play_press,
        )
        bui.containerwidget(
            edit=self._root_widget,
            start_button=start_button,
            selected_child=start_button,
        )

        # self._tdelay += self._t_delay_inc

        h = (
            self._width * 0.5
            + play_button_width * play_button_scale * 0.5
            + hspace
            + side_button_width * side_button_scale * 0.5
        )
        v = button_y_offs + side_button_y_offs
        thistdelay = self._tdelay + td4 * self._t_delay_inc
        self._watch_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(h - side_button_width * side_button_scale * 0.5, v),
            size=(side_button_width, side_button_height),
            scale=side_button_scale,
            autoselect=self._use_autoselect,
            button_type='square',
            label='',
            transition_delay=thistdelay,
            on_activate_call=self._watch_press,
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(h, v + side_button_height * side_button_scale * 0.25),
            size=(0, 0),
            scale=0.75,
            transition_delay=thistdelay,
            color=(0.75, 1.0, 0.7),
            draw_controller=self._watch_button,
            maxwidth=side_button_width * side_button_scale * 0.8,
            text=bui.Lstr(resource='watchWindow.titleText'),
            h_align='center',
            v_align='center',
        )
        icon_size = side_button_width * side_button_scale * 0.63
        bui.imagewidget(
            parent=self._root_widget,
            size=(icon_size, icon_size),
            draw_controller=self._watch_button,
            transition_delay=thistdelay,
            position=(
                h - 0.5 * icon_size,
                v
                + 0.65 * side_button_height * side_button_scale
                - 0.5 * icon_size,
            ),
            texture=bui.gettexture('tv'),
        )

        # Credits button.
        thistdelay = self._tdelay + td5 * self._t_delay_inc

        h += side_button_width * side_button_scale * 0.5 + hspace2
        v = button_y_offs + side_button_2_y_offs

        if self._have_quit_button:
            v += 1.17 * side_button_2_height * side_button_2_scale

        self._credits_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            button_type=None if self._have_quit_button else 'square',
            size=(
                side_button_2_width,
                side_button_2_height * (1.0 if self._have_quit_button else 2.0),
            ),
            scale=side_button_2_scale,
            autoselect=self._use_autoselect,
            label=bui.Lstr(resource=f'{self._r}.creditsText'),
            transition_delay=thistdelay,
            on_activate_call=self._credits,
        )

        self._quit_button: bui.Widget | None
        if self._have_quit_button:
            v -= 1.1 * side_button_2_height * side_button_2_scale
            # Nudge this a tiny bit right so we can press right from the
            # credits button to get to it.
            self._quit_button = quit_button = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=self._use_autoselect,
                position=(h + 4.0, v),
                size=(side_button_2_width, side_button_2_height),
                scale=side_button_2_scale,
                label=bui.Lstr(
                    resource=self._r
                    + (
                        '.quitText'
                        if 'Mac' in app.classic.legacy_user_agent_string
                        else '.exitGameText'
                    )
                ),
                on_activate_call=self._quit,
                transition_delay=thistdelay,
            )

            bui.containerwidget(
                edit=self._root_widget, cancel_button=quit_button
            )
            # self._tdelay += self._t_delay_inc
            rightmost_button = quit_button
        else:
            rightmost_button = self._credits_button
            self._quit_button = None

            # If we're not in-game, have no quit button, and this is
            # android, we want back presses to quit our activity.
            if app.classic.platform == 'android':

                def _do_quit() -> None:
                    bui.quit(confirm=True, quit_type=bui.QuitType.BACK)

                bui.containerwidget(
                    edit=self._root_widget, on_cancel_call=_do_quit
                )
        bui.widget(
            edit=rightmost_button,
            right_widget=bui.get_special_widget('store_button'),
        )

    def _quit(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.confirm import QuitWindow

        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return

        # Note: Normally we should go through bui.quit(confirm=True) but
        # invoking the window directly lets us scale it up from the
        # button.
        QuitWindow(origin_widget=self._quit_button)

    def _credits(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.credits import CreditsWindow

        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            CreditsWindow(origin_widget=self._credits_button),
        )

    def _howtoplay(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.help import HelpWindow

        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            HelpWindow(origin_widget=self._how_to_play_button),
        )

    def _save_state(self) -> None:
        try:
            sel = self._root_widget.get_selected_child()
            if sel == self._play_button:
                sel_name = 'Start'
            elif sel == self._gather_button:
                sel_name = 'Gather'
            elif sel == self._watch_button:
                sel_name = 'Watch'
            elif sel == self._how_to_play_button:
                sel_name = 'HowToPlay'
            elif sel == self._credits_button:
                sel_name = 'Credits'
            elif sel == self._quit_button:
                sel_name = 'Quit'
            elif sel == self._demo_menu_button:
                sel_name = 'DemoMenu'
            else:
                print(f'Unknown widget in main menu selection: {sel}.')
                sel_name = 'Start'
            bui.app.ui_v1.window_states[type(self)] = {'sel_name': sel_name}
        except Exception:
            logging.exception('Error saving state for %s.', self)

    def _restore_state(self) -> None:
        try:

            sel: bui.Widget | None

            sel_name = bui.app.ui_v1.window_states.get(type(self), {}).get(
                'sel_name'
            )
            assert isinstance(sel_name, (str, type(None)))
            if sel_name is None:
                sel_name = 'Start'
            if sel_name == 'HowToPlay':
                sel = self._how_to_play_button
            elif sel_name == 'Gather':
                sel = self._gather_button
            elif sel_name == 'Watch':
                sel = self._watch_button
            elif sel_name == 'Credits':
                sel = self._credits_button
            elif sel_name == 'Quit':
                sel = self._quit_button
            elif sel_name == 'DemoMenu':
                sel = self._demo_menu_button
            else:
                sel = self._play_button
            if sel is not None:
                bui.containerwidget(edit=self._root_widget, selected_child=sel)

        except Exception:
            logging.exception('Error restoring state for %s.', self)

    def _gather_press(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.gather import GatherWindow

        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            GatherWindow(origin_widget=self._gather_button)
        )

    def _watch_press(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.watch import WatchWindow

        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            WatchWindow(origin_widget=self._watch_button),
        )

    def _play_press(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.play import PlayWindow

        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(PlayWindow(origin_widget=self._play_button))
