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
"""UI functionality related to users rating the game."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Optional


def ask_for_rating() -> Optional[ba.Widget]:
    """(internal)"""
    app = ba.app
    platform = app.platform
    subplatform = app.subplatform
    if not (platform == 'mac' or (platform == 'android'
                                  and subplatform in ['google', 'cardboard'])):
        return None
    width = 700
    height = 400
    spacing = 40
    uiscale = ba.app.ui.uiscale
    dlg = ba.containerwidget(
        size=(width, height),
        transition='in_right',
        scale=(1.6 if uiscale is ba.UIScale.SMALL else
               1.35 if uiscale is ba.UIScale.MEDIUM else 1.0))
    v = height - 50
    v -= spacing
    v -= 140
    ba.imagewidget(parent=dlg,
                   position=(width / 2 - 100, v + 10),
                   size=(200, 200),
                   texture=ba.gettexture('cuteSpaz'))
    ba.textwidget(parent=dlg,
                  position=(15, v - 55),
                  size=(width - 30, 30),
                  color=ba.app.ui.infotextcolor,
                  text=ba.Lstr(resource='pleaseRateText',
                               subs=[('${APP_NAME}',
                                      ba.Lstr(resource='titleText'))]),
                  maxwidth=width * 0.95,
                  max_height=130,
                  scale=0.85,
                  h_align='center',
                  v_align='center')

    def do_rating() -> None:
        import _ba
        if platform == 'android':
            appname = _ba.appname()
            if subplatform == 'google':
                url = f'market://details?id=net.froemling.{appname}'
            else:
                url = 'market://details?id=net.froemling.{appname}cb'
        else:
            url = 'macappstore://itunes.apple.com/app/id416482767?ls=1&mt=12'

        ba.open_url(url)
        ba.containerwidget(edit=dlg, transition='out_left')

    ba.buttonwidget(parent=dlg,
                    position=(60, 20),
                    size=(200, 60),
                    label=ba.Lstr(resource='wellSureText'),
                    autoselect=True,
                    on_activate_call=do_rating)

    def close() -> None:
        ba.containerwidget(edit=dlg, transition='out_left')

    btn = ba.buttonwidget(parent=dlg,
                          position=(width - 270, 20),
                          size=(200, 60),
                          label=ba.Lstr(resource='noThanksText'),
                          autoselect=True,
                          on_activate_call=close)
    ba.containerwidget(edit=dlg, cancel_button=btn, selected_child=btn)
    return dlg
