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
"""Session and Activity for displaying the main menu bg."""

from __future__ import annotations

import random
import time
import weakref
from typing import TYPE_CHECKING

import ba
import _ba

if TYPE_CHECKING:
    from typing import Any, List, Optional

# FIXME: Clean this up if I ever revisit it.
# pylint: disable=attribute-defined-outside-init
# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
# pylint: disable=too-many-locals
# noinspection PyUnreachableCode
# noinspection PyAttributeOutsideInit


class MainMenuActivity(ba.Activity[ba.Player, ba.Team]):
    """Activity showing the rotating main menu bg stuff."""

    _stdassets = ba.Dependency(ba.AssetPackage, 'stdassets@1')

    def on_transition_in(self) -> None:
        super().on_transition_in()
        random.seed(123)
        self._logo_node: Optional[ba.Node] = None
        self._custom_logo_tex_name: Optional[str] = None
        self._word_actors: List[ba.Actor] = []
        app = ba.app

        # FIXME: We shouldn't be doing things conditionally based on whether
        #  the host is VR mode or not (clients may differ in that regard).
        #  Any differences need to happen at the engine level so everyone
        #  sees things in their own optimal way.
        vr_mode = ba.app.vr_mode

        if not ba.app.toolbar_test:
            color = ((1.0, 1.0, 1.0, 1.0) if vr_mode else (0.5, 0.6, 0.5, 0.6))
            # FIXME: Need a node attr for vr-specific-scale.
            scale = (0.9 if
                     (app.ui.uiscale is ba.UIScale.SMALL or vr_mode) else 0.7)
            self.my_name = ba.NodeActor(
                ba.newnode('text',
                           attrs={
                               'v_attach': 'bottom',
                               'h_align': 'center',
                               'color': color,
                               'flatness': 1.0,
                               'shadow': 1.0 if vr_mode else 0.5,
                               'scale': scale,
                               'position': (0, 10),
                               'vr_depth': -10,
                               'text': '\xa9 2011-2020 Eric Froemling'
                           }))

        # Throw up some text that only clients can see so they know that the
        # host is navigating menus while they're just staring at an
        # empty-ish screen.
        tval = ba.Lstr(resource='hostIsNavigatingMenusText',
                       subs=[('${HOST}', _ba.get_account_display_string())])
        self._host_is_navigating_text = ba.NodeActor(
            ba.newnode('text',
                       attrs={
                           'text': tval,
                           'client_only': True,
                           'position': (0, -200),
                           'flatness': 1.0,
                           'h_align': 'center'
                       }))
        if not ba.app.main_menu_did_initial_transition and hasattr(
                self, 'my_name'):
            assert self.my_name.node
            ba.animate(self.my_name.node, 'opacity', {2.3: 0, 3.0: 1.0})

        # FIXME: We shouldn't be doing things conditionally based on whether
        #  the host is vr mode or not (clients may not be or vice versa).
        #  Any differences need to happen at the engine level so everyone sees
        #  things in their own optimal way.
        vr_mode = app.vr_mode
        uiscale = app.ui.uiscale

        # In cases where we're doing lots of dev work lets always show the
        # build number.
        force_show_build_number = False

        if not ba.app.toolbar_test:
            if app.debug_build or app.test_build or force_show_build_number:
                if app.debug_build:
                    text = ba.Lstr(value='${V} (${B}) (${D})',
                                   subs=[
                                       ('${V}', app.version),
                                       ('${B}', str(app.build_number)),
                                       ('${D}', ba.Lstr(resource='debugText')),
                                   ])
                else:
                    text = ba.Lstr(value='${V} (${B})',
                                   subs=[
                                       ('${V}', app.version),
                                       ('${B}', str(app.build_number)),
                                   ])
            else:
                text = ba.Lstr(value='${V}', subs=[('${V}', app.version)])
            scale = 0.9 if (uiscale is ba.UIScale.SMALL or vr_mode) else 0.7
            color = (1, 1, 1, 1) if vr_mode else (0.5, 0.6, 0.5, 0.7)
            self.version = ba.NodeActor(
                ba.newnode(
                    'text',
                    attrs={
                        'v_attach': 'bottom',
                        'h_attach': 'right',
                        'h_align': 'right',
                        'flatness': 1.0,
                        'vr_depth': -10,
                        'shadow': 1.0 if vr_mode else 0.5,
                        'color': color,
                        'scale': scale,
                        'position': (-260, 10) if vr_mode else (-10, 10),
                        'text': text
                    }))
            if not ba.app.main_menu_did_initial_transition:
                assert self.version.node
                ba.animate(self.version.node, 'opacity', {2.3: 0, 3.0: 1.0})

        # Throw in test build info.
        self.beta_info = self.beta_info_2 = None
        if app.test_build and not app.kiosk_mode:
            pos = (230, 125) if app.kiosk_mode else (230, 35)
            self.beta_info = ba.NodeActor(
                ba.newnode('text',
                           attrs={
                               'v_attach': 'center',
                               'h_align': 'center',
                               'color': (1, 1, 1, 1),
                               'shadow': 0.5,
                               'flatness': 0.5,
                               'scale': 1,
                               'vr_depth': -60,
                               'position': pos,
                               'text': ba.Lstr(resource='testBuildText')
                           }))
            if not ba.app.main_menu_did_initial_transition:
                assert self.beta_info.node
                ba.animate(self.beta_info.node, 'opacity', {1.3: 0, 1.8: 1.0})

        model = ba.getmodel('thePadLevel')
        trees_model = ba.getmodel('trees')
        bottom_model = ba.getmodel('thePadLevelBottom')
        color_texture = ba.gettexture('thePadLevelColor')
        trees_texture = ba.gettexture('treesColor')
        bgtex = ba.gettexture('menuBG')
        bgmodel = ba.getmodel('thePadBG')

        # Load these last since most platforms don't use them.
        vr_bottom_fill_model = ba.getmodel('thePadVRFillBottom')
        vr_top_fill_model = ba.getmodel('thePadVRFillTop')

        gnode = self.globalsnode
        gnode.camera_mode = 'rotate'

        tint = (1.14, 1.1, 1.0)
        gnode.tint = tint
        gnode.ambient_color = (1.06, 1.04, 1.03)
        gnode.vignette_outer = (0.45, 0.55, 0.54)
        gnode.vignette_inner = (0.99, 0.98, 0.98)

        self.bottom = ba.NodeActor(
            ba.newnode('terrain',
                       attrs={
                           'model': bottom_model,
                           'lighting': False,
                           'reflection': 'soft',
                           'reflection_scale': [0.45],
                           'color_texture': color_texture
                       }))
        self.vr_bottom_fill = ba.NodeActor(
            ba.newnode('terrain',
                       attrs={
                           'model': vr_bottom_fill_model,
                           'lighting': False,
                           'vr_only': True,
                           'color_texture': color_texture
                       }))
        self.vr_top_fill = ba.NodeActor(
            ba.newnode('terrain',
                       attrs={
                           'model': vr_top_fill_model,
                           'vr_only': True,
                           'lighting': False,
                           'color_texture': bgtex
                       }))
        self.terrain = ba.NodeActor(
            ba.newnode('terrain',
                       attrs={
                           'model': model,
                           'color_texture': color_texture,
                           'reflection': 'soft',
                           'reflection_scale': [0.3]
                       }))
        self.trees = ba.NodeActor(
            ba.newnode('terrain',
                       attrs={
                           'model': trees_model,
                           'lighting': False,
                           'reflection': 'char',
                           'reflection_scale': [0.1],
                           'color_texture': trees_texture
                       }))
        self.bgterrain = ba.NodeActor(
            ba.newnode('terrain',
                       attrs={
                           'model': bgmodel,
                           'color': (0.92, 0.91, 0.9),
                           'lighting': False,
                           'background': True,
                           'color_texture': bgtex
                       }))

        self._ts = 0.86

        self._language: Optional[str] = None
        self._update_timer = ba.Timer(1.0, self._update, repeat=True)
        self._update()

        # Hopefully this won't hitch but lets space these out anyway.
        _ba.add_clean_frame_callback(ba.WeakCall(self._start_preloads))

        random.seed()

        # On the main menu, also show our news.
        class News:
            """Wrangles news display."""

            def __init__(self, activity: ba.Activity):
                self._valid = True
                self._message_duration = 10.0
                self._message_spacing = 2.0
                self._text: Optional[ba.NodeActor] = None
                self._activity = weakref.ref(activity)

                # If we're signed in, fetch news immediately.
                # Otherwise wait until we are signed in.
                self._fetch_timer: Optional[ba.Timer] = ba.Timer(
                    1.0, ba.WeakCall(self._try_fetching_news), repeat=True)
                self._try_fetching_news()

            # We now want to wait until we're signed in before fetching news.
            def _try_fetching_news(self) -> None:
                if _ba.get_account_state() == 'signed_in':
                    self._fetch_news()
                    self._fetch_timer = None

            def _fetch_news(self) -> None:
                ba.app.main_menu_last_news_fetch_time = time.time()

                # UPDATE - We now just pull news from MRVs.
                news = _ba.get_account_misc_read_val('n', None)
                if news is not None:
                    self._got_news(news)

            def _change_phrase(self) -> None:
                from bastd.actor.text import Text

                # If our news is way out of date, lets re-request it;
                # otherwise, rotate our phrase.
                assert ba.app.main_menu_last_news_fetch_time is not None
                if time.time() - ba.app.main_menu_last_news_fetch_time > 600.0:
                    self._fetch_news()
                    self._text = None
                else:
                    if self._text is not None:
                        if not self._phrases:
                            for phr in self._used_phrases:
                                self._phrases.insert(0, phr)
                        val = self._phrases.pop()
                        if val == '__ACH__':
                            vrmode = app.vr_mode
                            Text(ba.Lstr(resource='nextAchievementsText'),
                                 color=((1, 1, 1, 1) if vrmode else
                                        (0.95, 0.9, 1, 0.4)),
                                 host_only=True,
                                 maxwidth=200,
                                 position=(-300, -35),
                                 h_align=Text.HAlign.RIGHT,
                                 transition=Text.Transition.FADE_IN,
                                 scale=0.9 if vrmode else 0.7,
                                 flatness=1.0 if vrmode else 0.6,
                                 shadow=1.0 if vrmode else 0.5,
                                 h_attach=Text.HAttach.CENTER,
                                 v_attach=Text.VAttach.TOP,
                                 transition_delay=1.0,
                                 transition_out_delay=self._message_duration
                                 ).autoretain()
                            achs = [
                                a for a in app.achievements if not a.complete
                            ]
                            if achs:
                                ach = achs.pop(
                                    random.randrange(min(4, len(achs))))
                                ach.create_display(
                                    -180,
                                    -35,
                                    1.0,
                                    outdelay=self._message_duration,
                                    style='news')
                            if achs:
                                ach = achs.pop(
                                    random.randrange(min(8, len(achs))))
                                ach.create_display(
                                    180,
                                    -35,
                                    1.25,
                                    outdelay=self._message_duration,
                                    style='news')
                        else:
                            spc = self._message_spacing
                            keys = {
                                spc: 0.0,
                                spc + 1.0: 1.0,
                                spc + self._message_duration - 1.0: 1.0,
                                spc + self._message_duration: 0.0
                            }
                            assert self._text.node
                            ba.animate(self._text.node, 'opacity', keys)
                            # {k: v
                            #  for k, v in list(keys.items())})
                            self._text.node.text = val

            def _got_news(self, news: str) -> None:
                # Run this stuff in the context of our activity since we
                # need to make nodes and stuff.. should fix the serverget
                # call so it.
                activity = self._activity()
                if activity is None or activity.expired:
                    return
                with ba.Context(activity):

                    self._phrases: List[str] = []

                    # Show upcoming achievements in non-vr versions
                    # (currently too hard to read in vr).
                    self._used_phrases = (
                        ['__ACH__'] if not ba.app.vr_mode else
                        []) + [s for s in news.split('<br>\n') if s != '']
                    self._phrase_change_timer = ba.Timer(
                        (self._message_duration + self._message_spacing),
                        ba.WeakCall(self._change_phrase),
                        repeat=True)

                    scl = 1.2 if (ba.app.ui.uiscale is ba.UIScale.SMALL
                                  or ba.app.vr_mode) else 0.8

                    color2 = ((1, 1, 1, 1) if ba.app.vr_mode else
                              (0.7, 0.65, 0.75, 1.0))
                    shadow = (1.0 if ba.app.vr_mode else 0.4)
                    self._text = ba.NodeActor(
                        ba.newnode('text',
                                   attrs={
                                       'v_attach': 'top',
                                       'h_attach': 'center',
                                       'h_align': 'center',
                                       'vr_depth': -20,
                                       'shadow': shadow,
                                       'flatness': 0.8,
                                       'v_align': 'top',
                                       'color': color2,
                                       'scale': scl,
                                       'maxwidth': 900.0 / scl,
                                       'position': (0, -10)
                                   }))
                    self._change_phrase()

        if not app.kiosk_mode and not app.toolbar_test:
            self._news = News(self)

        # Bring up the last place we were, or start at the main menu otherwise.
        with ba.Context('ui'):
            from bastd.ui import specialoffer
            if bool(False):
                uicontroller = ba.app.ui.controller
                assert uicontroller is not None
                uicontroller.show_main_menu()
            else:
                main_menu_location = ba.app.ui.get_main_menu_location()

                # When coming back from a kiosk-mode game, jump to
                # the kiosk start screen.
                if ba.app.kiosk_mode:
                    # pylint: disable=cyclic-import
                    from bastd.ui.kiosk import KioskWindow
                    ba.app.ui.set_main_menu_window(
                        KioskWindow().get_root_widget())
                # ..or in normal cases go back to the main menu
                else:
                    if main_menu_location == 'Gather':
                        # pylint: disable=cyclic-import
                        from bastd.ui.gather import GatherWindow
                        ba.app.ui.set_main_menu_window(
                            GatherWindow(transition=None).get_root_widget())
                    elif main_menu_location == 'Watch':
                        # pylint: disable=cyclic-import
                        from bastd.ui.watch import WatchWindow
                        ba.app.ui.set_main_menu_window(
                            WatchWindow(transition=None).get_root_widget())
                    elif main_menu_location == 'Team Game Select':
                        # pylint: disable=cyclic-import
                        from bastd.ui.playlist.browser import (
                            PlaylistBrowserWindow)
                        ba.app.ui.set_main_menu_window(
                            PlaylistBrowserWindow(
                                sessiontype=ba.DualTeamSession,
                                transition=None).get_root_widget())
                    elif main_menu_location == 'Free-for-All Game Select':
                        # pylint: disable=cyclic-import
                        from bastd.ui.playlist.browser import (
                            PlaylistBrowserWindow)
                        ba.app.ui.set_main_menu_window(
                            PlaylistBrowserWindow(
                                sessiontype=ba.FreeForAllSession,
                                transition=None).get_root_widget())
                    elif main_menu_location == 'Coop Select':
                        # pylint: disable=cyclic-import
                        from bastd.ui.coop.browser import CoopBrowserWindow
                        ba.app.ui.set_main_menu_window(
                            CoopBrowserWindow(
                                transition=None).get_root_widget())
                    else:
                        # pylint: disable=cyclic-import
                        from bastd.ui.mainmenu import MainMenuWindow
                        ba.app.ui.set_main_menu_window(
                            MainMenuWindow(transition=None).get_root_widget())

                # attempt to show any pending offers immediately.
                # If that doesn't work, try again in a few seconds
                # (we may not have heard back from the server)
                # ..if that doesn't work they'll just have to wait
                # until the next opportunity.
                if not specialoffer.show_offer():

                    def try_again() -> None:
                        if not specialoffer.show_offer():
                            # Try one last time..
                            ba.timer(2.0,
                                     specialoffer.show_offer,
                                     timetype=ba.TimeType.REAL)

                    ba.timer(2.0, try_again, timetype=ba.TimeType.REAL)
        ba.app.main_menu_did_initial_transition = True

    def _update(self) -> None:
        app = ba.app

        # Update logo in case it changes.
        if self._logo_node:
            custom_texture = self._get_custom_logo_tex_name()
            if custom_texture != self._custom_logo_tex_name:
                self._custom_logo_tex_name = custom_texture
                self._logo_node.texture = ba.gettexture(
                    custom_texture if custom_texture is not None else 'logo')
                self._logo_node.model_opaque = (None
                                                if custom_texture is not None
                                                else ba.getmodel('logo'))
                self._logo_node.model_transparent = (
                    None if custom_texture is not None else
                    ba.getmodel('logoTransparent'))

        # If language has changed, recreate our logo text/graphics.
        lang = app.language
        if lang != self._language:
            self._language = lang
            y = 20
            base_scale = 1.1
            self._word_actors = []
            base_delay = 1.0
            delay = base_delay
            delay_inc = 0.02

            # Come on faster after the first time.
            if app.main_menu_did_initial_transition:
                base_delay = 0.0
                delay = base_delay
                delay_inc = 0.02

            # We draw higher in kiosk mode (make sure to test this
            # when making adjustments) for now we're hard-coded for
            # a few languages.. should maybe look into generalizing this?..
            if app.language == 'Chinese':
                base_x = -270.0
                x = base_x - 20.0
                spacing = 85.0 * base_scale
                y_extra = 0.0 if app.kiosk_mode else 0.0
                self._make_logo(x - 110 + 50,
                                113 + y + 1.2 * y_extra,
                                0.34 * base_scale,
                                delay=base_delay + 0.1,
                                custom_texture='chTitleChar1',
                                jitter_scale=2.0,
                                vr_depth_offset=-30)
                x += spacing
                delay += delay_inc
                self._make_logo(x - 10 + 50,
                                110 + y + 1.2 * y_extra,
                                0.31 * base_scale,
                                delay=base_delay + 0.15,
                                custom_texture='chTitleChar2',
                                jitter_scale=2.0,
                                vr_depth_offset=-30)
                x += 2.0 * spacing
                delay += delay_inc
                self._make_logo(x + 180 - 140,
                                110 + y + 1.2 * y_extra,
                                0.3 * base_scale,
                                delay=base_delay + 0.25,
                                custom_texture='chTitleChar3',
                                jitter_scale=2.0,
                                vr_depth_offset=-30)
                x += spacing
                delay += delay_inc
                self._make_logo(x + 241 - 120,
                                110 + y + 1.2 * y_extra,
                                0.31 * base_scale,
                                delay=base_delay + 0.3,
                                custom_texture='chTitleChar4',
                                jitter_scale=2.0,
                                vr_depth_offset=-30)
                x += spacing
                delay += delay_inc
                self._make_logo(x + 300 - 90,
                                105 + y + 1.2 * y_extra,
                                0.34 * base_scale,
                                delay=base_delay + 0.35,
                                custom_texture='chTitleChar5',
                                jitter_scale=2.0,
                                vr_depth_offset=-30)
                self._make_logo(base_x + 155,
                                146 + y + 1.2 * y_extra,
                                0.28 * base_scale,
                                delay=base_delay + 0.2,
                                rotate=-7)
            else:
                base_x = -170
                x = base_x - 20
                spacing = 55 * base_scale
                y_extra = 0 if app.kiosk_mode else 0
                xv1 = x
                delay1 = delay
                for shadow in (True, False):
                    x = xv1
                    delay = delay1
                    self._make_word('B',
                                    x - 50,
                                    y - 23 + 0.8 * y_extra,
                                    scale=1.3 * base_scale,
                                    delay=delay,
                                    vr_depth_offset=3,
                                    shadow=shadow)
                    x += spacing
                    delay += delay_inc
                    self._make_word('m',
                                    x,
                                    y + y_extra,
                                    delay=delay,
                                    scale=base_scale,
                                    shadow=shadow)
                    x += spacing * 1.25
                    delay += delay_inc
                    self._make_word('b',
                                    x,
                                    y + y_extra - 10,
                                    delay=delay,
                                    scale=1.1 * base_scale,
                                    vr_depth_offset=5,
                                    shadow=shadow)
                    x += spacing * 0.85
                    delay += delay_inc
                    self._make_word('S',
                                    x,
                                    y - 25 + 0.8 * y_extra,
                                    scale=1.35 * base_scale,
                                    delay=delay,
                                    vr_depth_offset=14,
                                    shadow=shadow)
                    x += spacing
                    delay += delay_inc
                    self._make_word('q',
                                    x,
                                    y + y_extra,
                                    delay=delay,
                                    scale=base_scale,
                                    shadow=shadow)
                    x += spacing * 0.9
                    delay += delay_inc
                    self._make_word('u',
                                    x,
                                    y + y_extra,
                                    delay=delay,
                                    scale=base_scale,
                                    vr_depth_offset=7,
                                    shadow=shadow)
                    x += spacing * 0.9
                    delay += delay_inc
                    self._make_word('a',
                                    x,
                                    y + y_extra,
                                    delay=delay,
                                    scale=base_scale,
                                    shadow=shadow)
                    x += spacing * 0.64
                    delay += delay_inc
                    self._make_word('d',
                                    x,
                                    y + y_extra - 10,
                                    delay=delay,
                                    scale=1.1 * base_scale,
                                    vr_depth_offset=6,
                                    shadow=shadow)
                self._make_logo(base_x - 28,
                                125 + y + 1.2 * y_extra,
                                0.32 * base_scale,
                                delay=base_delay)

    def _make_word(self,
                   word: str,
                   x: float,
                   y: float,
                   scale: float = 1.0,
                   delay: float = 0.0,
                   vr_depth_offset: float = 0.0,
                   shadow: bool = False) -> None:
        if shadow:
            word_obj = ba.NodeActor(
                ba.newnode('text',
                           attrs={
                               'position': (x, y),
                               'big': True,
                               'color': (0.0, 0.0, 0.2, 0.08),
                               'tilt_translate': 0.09,
                               'opacity_scales_shadow': False,
                               'shadow': 0.2,
                               'vr_depth': -130,
                               'v_align': 'center',
                               'project_scale': 0.97 * scale,
                               'scale': 1.0,
                               'text': word
                           }))
            self._word_actors.append(word_obj)
        else:
            word_obj = ba.NodeActor(
                ba.newnode('text',
                           attrs={
                               'position': (x, y),
                               'big': True,
                               'color': (1.2, 1.15, 1.15, 1.0),
                               'tilt_translate': 0.11,
                               'shadow': 0.2,
                               'vr_depth': -40 + vr_depth_offset,
                               'v_align': 'center',
                               'project_scale': scale,
                               'scale': 1.0,
                               'text': word
                           }))
            self._word_actors.append(word_obj)

        # Add a bit of stop-motion-y jitter to the logo
        # (unless we're in VR mode in which case its best to
        # leave things still).
        if not ba.app.vr_mode:
            cmb: Optional[ba.Node]
            cmb2: Optional[ba.Node]
            if not shadow:
                cmb = ba.newnode('combine',
                                 owner=word_obj.node,
                                 attrs={'size': 2})
            else:
                cmb = None
            if shadow:
                cmb2 = ba.newnode('combine',
                                  owner=word_obj.node,
                                  attrs={'size': 2})
            else:
                cmb2 = None
            if not shadow:
                assert cmb and word_obj.node
                cmb.connectattr('output', word_obj.node, 'position')
            if shadow:
                assert cmb2 and word_obj.node
                cmb2.connectattr('output', word_obj.node, 'position')
            keys = {}
            keys2 = {}
            time_v = 0.0
            for _i in range(10):
                val = x + (random.random() - 0.5) * 0.8
                val2 = x + (random.random() - 0.5) * 0.8
                keys[time_v * self._ts] = val
                keys2[time_v * self._ts] = val2 + 5
                time_v += random.random() * 0.1
            if cmb is not None:
                ba.animate(cmb, 'input0', keys, loop=True)
            if cmb2 is not None:
                ba.animate(cmb2, 'input0', keys2, loop=True)
            keys = {}
            keys2 = {}
            time_v = 0
            for _i in range(10):
                val = y + (random.random() - 0.5) * 0.8
                val2 = y + (random.random() - 0.5) * 0.8
                keys[time_v * self._ts] = val
                keys2[time_v * self._ts] = val2 - 9
                time_v += random.random() * 0.1
            if cmb is not None:
                ba.animate(cmb, 'input1', keys, loop=True)
            if cmb2 is not None:
                ba.animate(cmb2, 'input1', keys2, loop=True)

        if not shadow:
            assert word_obj.node
            ba.animate(word_obj.node, 'project_scale', {
                delay: 0.0,
                delay + 0.1: scale * 1.1,
                delay + 0.2: scale
            })
        else:
            assert word_obj.node
            ba.animate(word_obj.node, 'project_scale', {
                delay: 0.0,
                delay + 0.1: scale * 1.1,
                delay + 0.2: scale
            })

    def _get_custom_logo_tex_name(self) -> Optional[str]:
        if _ba.get_account_misc_read_val('easter', False):
            return 'logoEaster'
        return None

    # Pop the logo and menu in.
    def _make_logo(self,
                   x: float,
                   y: float,
                   scale: float,
                   delay: float,
                   custom_texture: str = None,
                   jitter_scale: float = 1.0,
                   rotate: float = 0.0,
                   vr_depth_offset: float = 0.0) -> None:

        # Temp easter goodness.
        if custom_texture is None:
            custom_texture = self._get_custom_logo_tex_name()
        self._custom_logo_tex_name = custom_texture
        ltex = ba.gettexture(
            custom_texture if custom_texture is not None else 'logo')
        mopaque = (None if custom_texture is not None else ba.getmodel('logo'))
        mtrans = (None if custom_texture is not None else
                  ba.getmodel('logoTransparent'))
        logo = ba.NodeActor(
            ba.newnode('image',
                       attrs={
                           'texture': ltex,
                           'model_opaque': mopaque,
                           'model_transparent': mtrans,
                           'vr_depth': -10 + vr_depth_offset,
                           'rotate': rotate,
                           'attach': 'center',
                           'tilt_translate': 0.21,
                           'absolute_scale': True
                       }))
        self._logo_node = logo.node
        self._word_actors.append(logo)

        # Add a bit of stop-motion-y jitter to the logo
        # (unless we're in VR mode in which case its best to
        # leave things still).
        assert logo.node
        if not ba.app.vr_mode:
            cmb = ba.newnode('combine', owner=logo.node, attrs={'size': 2})
            cmb.connectattr('output', logo.node, 'position')
            keys = {}
            time_v = 0.0

            # Gen some random keys for that stop-motion-y look
            for _i in range(10):
                keys[time_v] = x + (random.random() - 0.5) * 0.7 * jitter_scale
                time_v += random.random() * 0.1
            ba.animate(cmb, 'input0', keys, loop=True)
            keys = {}
            time_v = 0.0
            for _i in range(10):
                keys[time_v * self._ts] = y + (random.random() -
                                               0.5) * 0.7 * jitter_scale
                time_v += random.random() * 0.1
            ba.animate(cmb, 'input1', keys, loop=True)
        else:
            logo.node.position = (x, y)

        cmb = ba.newnode('combine', owner=logo.node, attrs={'size': 2})

        keys = {
            delay: 0.0,
            delay + 0.1: 700.0 * scale,
            delay + 0.2: 600.0 * scale
        }
        ba.animate(cmb, 'input0', keys)
        ba.animate(cmb, 'input1', keys)
        cmb.connectattr('output', logo.node, 'scale')

    def _start_preloads(self) -> None:
        # FIXME: The func that calls us back doesn't save/restore state
        #  or check for a dead activity so we have to do that ourself.
        if self.expired:
            return
        with ba.Context(self):
            _preload1()

        ba.timer(0.5, lambda: ba.setmusic(ba.MusicType.MENU))


def _preload1() -> None:
    """Pre-load some assets a second or two into the main menu.

    Helps avoid hitches later on.
    """
    for mname in [
            'plasticEyesTransparent', 'playerLineup1Transparent',
            'playerLineup2Transparent', 'playerLineup3Transparent',
            'playerLineup4Transparent', 'angryComputerTransparent',
            'scrollWidgetShort', 'windowBGBlotch'
    ]:
        ba.getmodel(mname)
    for tname in ['playerLineup', 'lock']:
        ba.gettexture(tname)
    for tex in [
            'iconRunaround', 'iconOnslaught', 'medalComplete', 'medalBronze',
            'medalSilver', 'medalGold', 'characterIconMask'
    ]:
        ba.gettexture(tex)
    ba.gettexture('bg')
    from bastd.actor.powerupbox import PowerupBoxFactory
    PowerupBoxFactory.get()
    ba.timer(0.1, _preload2)


def _preload2() -> None:
    # FIXME: Could integrate these loads with the classes that use them
    #  so they don't have to redundantly call the load
    #  (even if the actual result is cached).
    for mname in ['powerup', 'powerupSimple']:
        ba.getmodel(mname)
    for tname in [
            'powerupBomb', 'powerupSpeed', 'powerupPunch', 'powerupIceBombs',
            'powerupStickyBombs', 'powerupShield', 'powerupImpactBombs',
            'powerupHealth'
    ]:
        ba.gettexture(tname)
    for sname in [
            'powerup01', 'boxDrop', 'boxingBell', 'scoreHit01', 'scoreHit02',
            'dripity', 'spawn', 'gong'
    ]:
        ba.getsound(sname)
    from bastd.actor.bomb import BombFactory
    BombFactory.get()
    ba.timer(0.1, _preload3)


def _preload3() -> None:
    from bastd.actor.spazfactory import SpazFactory
    for mname in ['bomb', 'bombSticky', 'impactBomb']:
        ba.getmodel(mname)
    for tname in [
            'bombColor', 'bombColorIce', 'bombStickyColor', 'impactBombColor',
            'impactBombColorLit'
    ]:
        ba.gettexture(tname)
    for sname in ['freeze', 'fuse01', 'activateBeep', 'warnBeep']:
        ba.getsound(sname)
    SpazFactory.get()
    ba.timer(0.2, _preload4)


def _preload4() -> None:
    for tname in ['bar', 'meter', 'null', 'flagColor', 'achievementOutline']:
        ba.gettexture(tname)
    for mname in ['frameInset', 'meterTransparent', 'achievementOutline']:
        ba.getmodel(mname)
    for sname in ['metalHit', 'metalSkid', 'refWhistle', 'achievement']:
        ba.getsound(sname)
    from bastd.actor.flag import FlagFactory
    FlagFactory.get()


class MainMenuSession(ba.Session):
    """Session that runs the main menu environment."""

    def __init__(self) -> None:

        # Gather dependencies we'll need (just our activity).
        self._activity_deps = ba.DependencySet(ba.Dependency(MainMenuActivity))

        super().__init__([self._activity_deps])
        self._locked = False
        self.setactivity(ba.newactivity(MainMenuActivity))

    def on_activity_end(self, activity: ba.Activity, results: Any) -> None:
        if self._locked:
            _ba.unlock_all_input()

        # Any ending activity leads us into the main menu one.
        self.setactivity(ba.newactivity(MainMenuActivity))

    def on_player_request(self, player: ba.SessionPlayer) -> bool:
        # Reject all player requests.
        return False
