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
"""Provides help related ui."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Optional, Tuple


class HelpWindow(ba.Window):
    """A window providing help on how to play."""

    def __init__(self,
                 main_menu: bool = False,
                 origin_widget: ba.Widget = None):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        from ba.internal import get_remote_app_name
        from ba.deprecated import get_resource
        ba.set_analytics_screen('Help Window')

        # If they provided an origin-widget, scale up from that.
        scale_origin: Optional[Tuple[float, float]]
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None
            transition = 'in_right'

        self._r = 'helpWindow'

        self._main_menu = main_menu
        uiscale = ba.app.ui.uiscale
        width = 950 if uiscale is ba.UIScale.SMALL else 750
        x_offs = 100 if uiscale is ba.UIScale.SMALL else 0
        height = (460 if uiscale is ba.UIScale.SMALL else
                  530 if uiscale is ba.UIScale.MEDIUM else 600)

        super().__init__(root_widget=ba.containerwidget(
            size=(width, height),
            transition=transition,
            toolbar_visibility='menu_minimal',
            scale_origin_stack_offset=scale_origin,
            scale=(1.77 if uiscale is ba.UIScale.SMALL else
                   1.25 if uiscale is ba.UIScale.MEDIUM else 1.0),
            stack_offset=(0, -30) if uiscale is ba.UIScale.SMALL else (
                0, 15) if uiscale is ba.UIScale.MEDIUM else (0, 0)))

        ba.textwidget(parent=self._root_widget,
                      position=(0, height -
                                (50 if uiscale is ba.UIScale.SMALL else 45)),
                      size=(width, 25),
                      text=ba.Lstr(resource=self._r + '.titleText',
                                   subs=[('${APP_NAME}',
                                          ba.Lstr(resource='titleText'))]),
                      color=ba.app.ui.title_color,
                      h_align='center',
                      v_align='top')

        self._scrollwidget = ba.scrollwidget(
            parent=self._root_widget,
            position=(44 + x_offs, 55 if uiscale is ba.UIScale.SMALL else 55),
            simple_culling_v=100.0,
            size=(width - (88 + 2 * x_offs),
                  height - 120 + (5 if uiscale is ba.UIScale.SMALL else 0)),
            capture_arrows=True)

        if ba.app.ui.use_toolbars:
            ba.widget(edit=self._scrollwidget,
                      right_widget=_ba.get_special_widget('party_button'))
        ba.containerwidget(edit=self._root_widget,
                           selected_child=self._scrollwidget)

        # ugly: create this last so it gets first dibs at touch events (since
        # we have it close to the scroll widget)
        if uiscale is ba.UIScale.SMALL and ba.app.ui.use_toolbars:
            ba.containerwidget(edit=self._root_widget,
                               on_cancel_call=self._close)
            ba.widget(edit=self._scrollwidget,
                      left_widget=_ba.get_special_widget('back_button'))
        else:
            btn = ba.buttonwidget(
                parent=self._root_widget,
                position=(x_offs +
                          (40 + 0 if uiscale is ba.UIScale.SMALL else 70),
                          height -
                          (59 if uiscale is ba.UIScale.SMALL else 50)),
                size=(140, 60),
                scale=0.7 if uiscale is ba.UIScale.SMALL else 0.8,
                label=ba.Lstr(
                    resource='backText') if self._main_menu else 'Close',
                button_type='back' if self._main_menu else None,
                extra_touch_border_scale=2.0,
                autoselect=True,
                on_activate_call=self._close)
            ba.containerwidget(edit=self._root_widget, cancel_button=btn)

            if self._main_menu:
                ba.buttonwidget(edit=btn,
                                button_type='backSmall',
                                size=(60, 55),
                                label=ba.charstr(ba.SpecialChar.BACK))

        self._sub_width = 660
        self._sub_height = 1590 + get_resource(
            self._r + '.someDaysExtraSpace') + get_resource(
                self._r + '.orPunchingSomethingExtraSpace')

        self._subcontainer = ba.containerwidget(parent=self._scrollwidget,
                                                size=(self._sub_width,
                                                      self._sub_height),
                                                background=False,
                                                claims_left_right=False,
                                                claims_tab=False)

        spacing = 1.0
        h = self._sub_width * 0.5
        v = self._sub_height - 55
        logo_tex = ba.gettexture('logo')
        icon_buffer = 1.1
        header = (0.7, 1.0, 0.7, 1.0)
        header2 = (0.8, 0.8, 1.0, 1.0)
        paragraph = (0.8, 0.8, 1.0, 1.0)

        txt = ba.Lstr(resource=self._r + '.welcomeText',
                      subs=[('${APP_NAME}', ba.Lstr(resource='titleText'))
                            ]).evaluate()
        txt_scale = 1.4
        txt_maxwidth = 480
        ba.textwidget(parent=self._subcontainer,
                      position=(h, v),
                      size=(0, 0),
                      scale=txt_scale,
                      flatness=0.5,
                      res_scale=1.5,
                      text=txt,
                      h_align='center',
                      color=header,
                      v_align='center',
                      maxwidth=txt_maxwidth)
        txt_width = min(
            txt_maxwidth,
            _ba.get_string_width(txt, suppress_warning=True) * txt_scale)

        icon_size = 70
        hval2 = h - (txt_width * 0.5 + icon_size * 0.5 * icon_buffer)
        ba.imagewidget(parent=self._subcontainer,
                       size=(icon_size, icon_size),
                       position=(hval2 - 0.5 * icon_size,
                                 v - 0.45 * icon_size),
                       texture=logo_tex)

        force_test = False
        app = ba.app
        if (app.platform == 'android'
                and app.subplatform == 'alibaba') or force_test:
            v -= 120.0
            txtv = (
                '\xe8\xbf\x99\xe6\x98\xaf\xe4\xb8\x80\xe4\xb8\xaa\xe5\x8f\xaf'
                '\xe4\xbb\xa5\xe5\x92\x8c\xe5\xae\xb6\xe4\xba\xba\xe6\x9c\x8b'
                '\xe5\x8f\x8b\xe4\xb8\x80\xe8\xb5\xb7\xe7\x8e\xa9\xe7\x9a\x84'
                '\xe6\xb8\xb8\xe6\x88\x8f,\xe5\x90\x8c\xe6\x97\xb6\xe6\x94\xaf'
                '\xe6\x8c\x81\xe8\x81\x94 \xe2\x80\xa8\xe7\xbd\x91\xe5\xaf\xb9'
                '\xe6\x88\x98\xe3\x80\x82\n'
                '\xe5\xa6\x82\xe6\xb2\xa1\xe6\x9c\x89\xe6\xb8\xb8\xe6\x88\x8f'
                '\xe6\x89\x8b\xe6\x9f\x84,\xe5\x8f\xaf\xe4\xbb\xa5\xe4\xbd\xbf'
                '\xe7\x94\xa8\xe7\xa7\xbb\xe5\x8a\xa8\xe8\xae\xbe\xe5\xa4\x87'
                '\xe6\x89\xab\xe7\xa0\x81\xe4\xb8\x8b\xe8\xbd\xbd\xe2\x80\x9c'
                '\xe9\x98\xbf\xe9\x87\x8c\xc2'
                '\xa0TV\xc2\xa0\xe5\x8a\xa9\xe6\x89'
                '\x8b\xe2\x80\x9d\xe7\x94\xa8 \xe6\x9d\xa5\xe4\xbb\xa3\xe6\x9b'
                '\xbf\xe5\xa4\x96\xe8\xae\xbe\xe3\x80\x82\n'
                '\xe6\x9c\x80\xe5\xa4\x9a\xe6\x94\xaf\xe6\x8c\x81\xe6\x8e\xa5'
                '\xe5\x85\xa5\xc2\xa08\xc2\xa0\xe4\xb8\xaa\xe5\xa4\x96\xe8'
                '\xae\xbe')
            ba.textwidget(parent=self._subcontainer,
                          size=(0, 0),
                          h_align='center',
                          v_align='center',
                          maxwidth=self._sub_width * 0.9,
                          position=(self._sub_width * 0.5, v - 180),
                          text=txtv)
            ba.imagewidget(parent=self._subcontainer,
                           position=(self._sub_width - 320, v - 120),
                           size=(200, 200),
                           texture=ba.gettexture('aliControllerQR'))
            ba.imagewidget(parent=self._subcontainer,
                           position=(90, v - 130),
                           size=(210, 210),
                           texture=ba.gettexture('multiplayerExamples'))
            v -= 120.0

        else:
            v -= spacing * 50.0
            txt = ba.Lstr(resource=self._r + '.someDaysText').evaluate()
            ba.textwidget(parent=self._subcontainer,
                          position=(h, v),
                          size=(0, 0),
                          scale=1.2,
                          maxwidth=self._sub_width * 0.9,
                          text=txt,
                          h_align='center',
                          color=paragraph,
                          v_align='center',
                          flatness=1.0)
            v -= (spacing * 25.0 +
                  get_resource(self._r + '.someDaysExtraSpace'))
            txt_scale = 0.66
            txt = ba.Lstr(resource=self._r +
                          '.orPunchingSomethingText').evaluate()
            ba.textwidget(parent=self._subcontainer,
                          position=(h, v),
                          size=(0, 0),
                          scale=txt_scale,
                          maxwidth=self._sub_width * 0.9,
                          text=txt,
                          h_align='center',
                          color=paragraph,
                          v_align='center',
                          flatness=1.0)
            v -= (spacing * 27.0 +
                  get_resource(self._r + '.orPunchingSomethingExtraSpace'))
            txt_scale = 1.0
            txt = ba.Lstr(resource=self._r + '.canHelpText',
                          subs=[('${APP_NAME}', ba.Lstr(resource='titleText'))
                                ]).evaluate()
            ba.textwidget(parent=self._subcontainer,
                          position=(h, v),
                          size=(0, 0),
                          scale=txt_scale,
                          flatness=1.0,
                          text=txt,
                          h_align='center',
                          color=paragraph,
                          v_align='center')

            v -= spacing * 70.0
            txt_scale = 1.0
            txt = ba.Lstr(resource=self._r + '.toGetTheMostText').evaluate()
            ba.textwidget(parent=self._subcontainer,
                          position=(h, v),
                          size=(0, 0),
                          scale=txt_scale,
                          maxwidth=self._sub_width * 0.9,
                          text=txt,
                          h_align='center',
                          color=header,
                          v_align='center',
                          flatness=1.0)

            v -= spacing * 40.0
            txt_scale = 0.74
            txt = ba.Lstr(resource=self._r + '.friendsText').evaluate()
            hval2 = h - 220
            ba.textwidget(parent=self._subcontainer,
                          position=(hval2, v),
                          size=(0, 0),
                          scale=txt_scale,
                          maxwidth=100,
                          text=txt,
                          h_align='right',
                          color=header,
                          v_align='center',
                          flatness=1.0)

            txt = ba.Lstr(resource=self._r + '.friendsGoodText',
                          subs=[('${APP_NAME}', ba.Lstr(resource='titleText'))
                                ]).evaluate()
            txt_scale = 0.7
            ba.textwidget(parent=self._subcontainer,
                          position=(hval2 + 10, v + 8),
                          size=(0, 0),
                          scale=txt_scale,
                          maxwidth=500,
                          text=txt,
                          h_align='left',
                          color=paragraph,
                          flatness=1.0)

            app = ba.app

            v -= spacing * 45.0
            txt = (ba.Lstr(resource=self._r + '.devicesText').evaluate()
                   if app.vr_mode else ba.Lstr(resource=self._r +
                                               '.controllersText').evaluate())
            txt_scale = 0.74
            hval2 = h - 220
            ba.textwidget(parent=self._subcontainer,
                          position=(hval2, v),
                          size=(0, 0),
                          scale=txt_scale,
                          maxwidth=100,
                          text=txt,
                          h_align='right',
                          color=header,
                          v_align='center',
                          flatness=1.0)

            txt_scale = 0.7
            if not app.vr_mode:
                txt = ba.Lstr(resource=self._r + '.controllersInfoText',
                              subs=[('${APP_NAME}',
                                     ba.Lstr(resource='titleText')),
                                    ('${REMOTE_APP_NAME}',
                                     get_remote_app_name())]).evaluate()
            else:
                txt = ba.Lstr(resource=self._r + '.devicesInfoText',
                              subs=[('${APP_NAME}',
                                     ba.Lstr(resource='titleText'))
                                    ]).evaluate()

            ba.textwidget(parent=self._subcontainer,
                          position=(hval2 + 10, v + 8),
                          size=(0, 0),
                          scale=txt_scale,
                          maxwidth=500,
                          max_height=105,
                          text=txt,
                          h_align='left',
                          color=paragraph,
                          flatness=1.0)

        v -= spacing * 150.0

        txt = ba.Lstr(resource=self._r + '.controlsText').evaluate()
        txt_scale = 1.4
        txt_maxwidth = 480
        ba.textwidget(parent=self._subcontainer,
                      position=(h, v),
                      size=(0, 0),
                      scale=txt_scale,
                      flatness=0.5,
                      text=txt,
                      h_align='center',
                      color=header,
                      v_align='center',
                      res_scale=1.5,
                      maxwidth=txt_maxwidth)
        txt_width = min(
            txt_maxwidth,
            _ba.get_string_width(txt, suppress_warning=True) * txt_scale)
        icon_size = 70

        hval2 = h - (txt_width * 0.5 + icon_size * 0.5 * icon_buffer)
        ba.imagewidget(parent=self._subcontainer,
                       size=(icon_size, icon_size),
                       position=(hval2 - 0.5 * icon_size,
                                 v - 0.45 * icon_size),
                       texture=logo_tex)

        v -= spacing * 45.0

        txt_scale = 0.7
        txt = ba.Lstr(resource=self._r + '.controlsSubtitleText',
                      subs=[('${APP_NAME}', ba.Lstr(resource='titleText'))
                            ]).evaluate()
        ba.textwidget(parent=self._subcontainer,
                      position=(h, v),
                      size=(0, 0),
                      scale=txt_scale,
                      maxwidth=self._sub_width * 0.9,
                      flatness=1.0,
                      text=txt,
                      h_align='center',
                      color=paragraph,
                      v_align='center')
        v -= spacing * 160.0

        sep = 70
        icon_size = 100
        # icon_size_2 = 30
        hval2 = h - sep
        vval2 = v
        ba.imagewidget(parent=self._subcontainer,
                       size=(icon_size, icon_size),
                       position=(hval2 - 0.5 * icon_size,
                                 vval2 - 0.5 * icon_size),
                       texture=ba.gettexture('buttonPunch'),
                       color=(1, 0.7, 0.3))

        txt_scale = get_resource(self._r + '.punchInfoTextScale')
        txt = ba.Lstr(resource=self._r + '.punchInfoText').evaluate()
        ba.textwidget(parent=self._subcontainer,
                      position=(h - sep - 185 + 70, v + 120),
                      size=(0, 0),
                      scale=txt_scale,
                      flatness=1.0,
                      text=txt,
                      h_align='center',
                      color=(1, 0.7, 0.3, 1.0),
                      v_align='top')

        hval2 = h + sep
        vval2 = v
        ba.imagewidget(parent=self._subcontainer,
                       size=(icon_size, icon_size),
                       position=(hval2 - 0.5 * icon_size,
                                 vval2 - 0.5 * icon_size),
                       texture=ba.gettexture('buttonBomb'),
                       color=(1, 0.3, 0.3))

        txt = ba.Lstr(resource=self._r + '.bombInfoText').evaluate()
        txt_scale = get_resource(self._r + '.bombInfoTextScale')
        ba.textwidget(parent=self._subcontainer,
                      position=(h + sep + 50 + 60, v - 35),
                      size=(0, 0),
                      scale=txt_scale,
                      flatness=1.0,
                      maxwidth=270,
                      text=txt,
                      h_align='center',
                      color=(1, 0.3, 0.3, 1.0),
                      v_align='top')

        hval2 = h
        vval2 = v + sep
        ba.imagewidget(parent=self._subcontainer,
                       size=(icon_size, icon_size),
                       position=(hval2 - 0.5 * icon_size,
                                 vval2 - 0.5 * icon_size),
                       texture=ba.gettexture('buttonPickUp'),
                       color=(0.5, 0.5, 1))

        txtl = ba.Lstr(resource=self._r + '.pickUpInfoText')
        txt_scale = get_resource(self._r + '.pickUpInfoTextScale')
        ba.textwidget(parent=self._subcontainer,
                      position=(h + 60 + 120, v + sep + 50),
                      size=(0, 0),
                      scale=txt_scale,
                      flatness=1.0,
                      text=txtl,
                      h_align='center',
                      color=(0.5, 0.5, 1, 1.0),
                      v_align='top')

        hval2 = h
        vval2 = v - sep
        ba.imagewidget(parent=self._subcontainer,
                       size=(icon_size, icon_size),
                       position=(hval2 - 0.5 * icon_size,
                                 vval2 - 0.5 * icon_size),
                       texture=ba.gettexture('buttonJump'),
                       color=(0.4, 1, 0.4))

        txt = ba.Lstr(resource=self._r + '.jumpInfoText').evaluate()
        txt_scale = get_resource(self._r + '.jumpInfoTextScale')
        ba.textwidget(parent=self._subcontainer,
                      position=(h - 250 + 75, v - sep - 15 + 30),
                      size=(0, 0),
                      scale=txt_scale,
                      flatness=1.0,
                      text=txt,
                      h_align='center',
                      color=(0.4, 1, 0.4, 1.0),
                      v_align='top')

        txt = ba.Lstr(resource=self._r + '.runInfoText').evaluate()
        txt_scale = get_resource(self._r + '.runInfoTextScale')
        ba.textwidget(parent=self._subcontainer,
                      position=(h, v - sep - 100),
                      size=(0, 0),
                      scale=txt_scale,
                      maxwidth=self._sub_width * 0.93,
                      flatness=1.0,
                      text=txt,
                      h_align='center',
                      color=(0.7, 0.7, 1.0, 1.0),
                      v_align='center')

        v -= spacing * 280.0

        txt = ba.Lstr(resource=self._r + '.powerupsText').evaluate()
        txt_scale = 1.4
        txt_maxwidth = 480
        ba.textwidget(parent=self._subcontainer,
                      position=(h, v),
                      size=(0, 0),
                      scale=txt_scale,
                      flatness=0.5,
                      text=txt,
                      h_align='center',
                      color=header,
                      v_align='center',
                      maxwidth=txt_maxwidth)
        txt_width = min(
            txt_maxwidth,
            _ba.get_string_width(txt, suppress_warning=True) * txt_scale)
        icon_size = 70
        hval2 = h - (txt_width * 0.5 + icon_size * 0.5 * icon_buffer)
        ba.imagewidget(parent=self._subcontainer,
                       size=(icon_size, icon_size),
                       position=(hval2 - 0.5 * icon_size,
                                 v - 0.45 * icon_size),
                       texture=logo_tex)

        v -= spacing * 50.0
        txt_scale = get_resource(self._r + '.powerupsSubtitleTextScale')
        txt = ba.Lstr(resource=self._r + '.powerupsSubtitleText').evaluate()
        ba.textwidget(parent=self._subcontainer,
                      position=(h, v),
                      size=(0, 0),
                      scale=txt_scale,
                      maxwidth=self._sub_width * 0.9,
                      text=txt,
                      h_align='center',
                      color=paragraph,
                      v_align='center',
                      flatness=1.0)

        v -= spacing * 1.0

        mm1 = -270
        mm2 = -215
        mm3 = 0
        icon_size = 50
        shadow_size = 80
        shadow_offs_x = 3
        shadow_offs_y = -4
        t_big = 1.1
        t_small = 0.65

        shadow_tex = ba.gettexture('shadowSharp')

        for tex in [
                'powerupPunch', 'powerupShield', 'powerupBomb',
                'powerupHealth', 'powerupIceBombs', 'powerupImpactBombs',
                'powerupStickyBombs', 'powerupLandMines', 'powerupCurse'
        ]:
            name = ba.Lstr(resource=self._r + '.' + tex + 'NameText')
            desc = ba.Lstr(resource=self._r + '.' + tex + 'DescriptionText')

            v -= spacing * 60.0

            ba.imagewidget(
                parent=self._subcontainer,
                size=(shadow_size, shadow_size),
                position=(h + mm1 + shadow_offs_x - 0.5 * shadow_size,
                          v + shadow_offs_y - 0.5 * shadow_size),
                texture=shadow_tex,
                color=(0, 0, 0),
                opacity=0.5)
            ba.imagewidget(parent=self._subcontainer,
                           size=(icon_size, icon_size),
                           position=(h + mm1 - 0.5 * icon_size,
                                     v - 0.5 * icon_size),
                           texture=ba.gettexture(tex))

            txt_scale = t_big
            txtl = name
            ba.textwidget(parent=self._subcontainer,
                          position=(h + mm2, v + 3),
                          size=(0, 0),
                          scale=txt_scale,
                          maxwidth=200,
                          flatness=1.0,
                          text=txtl,
                          h_align='left',
                          color=header2,
                          v_align='center')
            txt_scale = t_small
            txtl = desc
            ba.textwidget(parent=self._subcontainer,
                          position=(h + mm3, v),
                          size=(0, 0),
                          scale=txt_scale,
                          maxwidth=300,
                          flatness=1.0,
                          text=txtl,
                          h_align='left',
                          color=paragraph,
                          v_align='center',
                          res_scale=0.5)

    def _close(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.mainmenu import MainMenuWindow
        ba.containerwidget(edit=self._root_widget,
                           transition=self._transition_out)
        if self._main_menu:
            ba.app.ui.set_main_menu_window(
                MainMenuWindow(transition='in_left').get_root_widget())
