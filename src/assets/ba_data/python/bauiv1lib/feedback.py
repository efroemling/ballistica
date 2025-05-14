# Released under the MIT License. See LICENSE for details.
#
"""UI functionality related to users rating the game."""

from __future__ import annotations

import bauiv1 as bui


def ask_for_rating() -> bui.Widget | None:
    """(internal)"""
    app = bui.app
    assert app.classic is not None
    platform = app.classic.platform
    subplatform = app.classic.subplatform

    # FIXME: should whitelist platforms we *do* want this for.
    if bui.app.env.test:
        return None
    if not (
        platform == 'mac'
        or (platform == 'android' and subplatform in ['google', 'cardboard'])
    ):
        return None
    width = 700
    height = 400
    spacing = 40
    assert bui.app.classic is not None
    uiscale = bui.app.ui_v1.uiscale
    dlg = bui.containerwidget(
        size=(width, height),
        transition='in_right',
        scale=(
            1.6
            if uiscale is bui.UIScale.SMALL
            else 1.35 if uiscale is bui.UIScale.MEDIUM else 1.0
        ),
    )
    v = height - 50
    v -= spacing
    v -= 140
    bui.imagewidget(
        parent=dlg,
        position=(width / 2 - 100, v + 10),
        size=(200, 200),
        texture=bui.gettexture('cuteSpaz'),
    )
    bui.textwidget(
        parent=dlg,
        position=(15, v - 55),
        size=(width - 30, 30),
        color=bui.app.ui_v1.infotextcolor,
        text=bui.Lstr(
            resource='pleaseRateText',
            subs=[('${APP_NAME}', bui.Lstr(resource='titleText'))],
        ),
        maxwidth=width * 0.95,
        max_height=130,
        scale=0.85,
        h_align='center',
        v_align='center',
    )

    def do_rating() -> None:
        # This is not currently in use anywhere.
        bui.screenmessage(bui.Lstr(resource='error'))
        # bui.open_url(url)
        bui.containerwidget(edit=dlg, transition='out_left')

    bui.buttonwidget(
        parent=dlg,
        position=(60, 20),
        size=(200, 60),
        label=bui.Lstr(resource='wellSureText'),
        autoselect=True,
        on_activate_call=do_rating,
    )

    def close() -> None:
        bui.containerwidget(edit=dlg, transition='out_left')

    btn = bui.buttonwidget(
        parent=dlg,
        position=(width - 270, 20),
        size=(200, 60),
        label=bui.Lstr(resource='noThanksText'),
        autoselect=True,
        on_activate_call=close,
    )
    bui.containerwidget(edit=dlg, cancel_button=btn, selected_child=btn)
    return dlg
