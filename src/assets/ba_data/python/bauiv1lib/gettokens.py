# Released under the MIT License. See LICENSE for details.
#
"""UI functionality for purchasing/acquiring currency."""

from __future__ import annotations

import logging
from enum import Enum
from functools import partial
from dataclasses import dataclass
from typing import TYPE_CHECKING, assert_never

import bacommon.cloud

import bauiv1 as bui
from bauiv1lib.connectivity import wait_for_connectivity

if TYPE_CHECKING:
    from typing import Any, Callable


@dataclass
class _ButtonDef:
    itemid: str
    width: float
    color: tuple[float, float, float]
    imgdefs: list[_ImgDef]
    txtdefs: list[_TxtDef]
    prepad: float = 0.0


@dataclass
class _ImgDef:
    tex: str
    pos: tuple[float, float]
    size: tuple[float, float]
    color: tuple[float, float, float] = (1, 1, 1)
    opacity: float = 1.0
    draw_controller_mult: float | None = None


class TextContents(Enum):
    """Some type of text to show."""

    PRICE = 'price'


@dataclass
class _TxtDef:
    text: str | TextContents
    pos: tuple[float, float]
    maxwidth: float | None
    scale: float = 1.0
    color: tuple[float, float, float] = (1, 1, 1)
    rotate: float | None = None


class GetTokensWindow(bui.Window):
    """Window for purchasing/acquiring classic tickets."""

    def __del__(self) -> None:
        print('~GetTokensWindow()')

    def __init__(
        self,
        transition: str = 'in_right',
        origin_widget: bui.Widget | None = None,
        restore_previous_call: Callable[[bui.Widget], None] | None = None,
    ):
        # pylint: disable=too-many-locals

        bwidthstd = 170
        bwidthwide = 300
        ycolor = (0, 0, 0.3)
        pcolor = (0, 0, 0.3)
        pos1 = 65
        pos2 = 34
        titlescale = 0.9
        pricescale = 0.65
        bcapcol1 = (0.25, 0.13, 0.02)
        self._buttondefs: list[_ButtonDef] = [
            _ButtonDef(
                itemid='tokens1',
                width=bwidthstd,
                color=ycolor,
                imgdefs=[
                    _ImgDef(
                        'tokens1',
                        pos=(-3, 85),
                        size=(172, 172),
                        opacity=1.0,
                        draw_controller_mult=0.5,
                    ),
                    _ImgDef(
                        'windowBottomCap',
                        pos=(1.5, 4),
                        size=(bwidthstd * 0.960, 100),
                        color=bcapcol1,
                        opacity=1.0,
                    ),
                ],
                txtdefs=[
                    _TxtDef(
                        '50 Tokens',
                        pos=(bwidthstd * 0.5, pos1),
                        color=(1.1, 1.05, 1.0),
                        scale=titlescale,
                        maxwidth=bwidthstd * 0.9,
                    ),
                    _TxtDef(
                        TextContents.PRICE,
                        pos=(bwidthstd * 0.5, pos2),
                        color=(1.1, 1.05, 1.0),
                        scale=pricescale,
                        maxwidth=bwidthstd * 0.9,
                    ),
                ],
            ),
            _ButtonDef(
                itemid='tokens2',
                width=bwidthstd,
                color=ycolor,
                imgdefs=[
                    _ImgDef(
                        'tokens2',
                        pos=(-3, 85),
                        size=(172, 172),
                        opacity=1.0,
                        draw_controller_mult=0.5,
                    ),
                    _ImgDef(
                        'windowBottomCap',
                        pos=(1.5, 4),
                        size=(bwidthstd * 0.960, 100),
                        color=bcapcol1,
                        opacity=1.0,
                    ),
                ],
                txtdefs=[
                    _TxtDef(
                        '500 Tokens',
                        pos=(bwidthstd * 0.5, pos1),
                        color=(1.1, 1.05, 1.0),
                        scale=titlescale,
                        maxwidth=bwidthstd * 0.9,
                    ),
                    _TxtDef(
                        TextContents.PRICE,
                        pos=(bwidthstd * 0.5, pos2),
                        color=(1.1, 1.05, 1.0),
                        scale=pricescale,
                        maxwidth=bwidthstd * 0.9,
                    ),
                ],
            ),
            _ButtonDef(
                itemid='tokens3',
                width=bwidthstd,
                color=ycolor,
                imgdefs=[
                    _ImgDef(
                        'tokens3',
                        pos=(-3, 85),
                        size=(172, 172),
                        opacity=1.0,
                        draw_controller_mult=0.5,
                    ),
                    _ImgDef(
                        'windowBottomCap',
                        pos=(1.5, 4),
                        size=(bwidthstd * 0.960, 100),
                        color=bcapcol1,
                        opacity=1.0,
                    ),
                ],
                txtdefs=[
                    _TxtDef(
                        '1200 Tokens',
                        pos=(bwidthstd * 0.5, pos1),
                        color=(1.1, 1.05, 1.0),
                        scale=titlescale,
                        maxwidth=bwidthstd * 0.9,
                    ),
                    _TxtDef(
                        TextContents.PRICE,
                        pos=(bwidthstd * 0.5, pos2),
                        color=(1.1, 1.05, 1.0),
                        scale=pricescale,
                        maxwidth=bwidthstd * 0.9,
                    ),
                ],
            ),
            _ButtonDef(
                itemid='tokens4',
                width=bwidthstd,
                color=ycolor,
                imgdefs=[
                    _ImgDef(
                        'tokens4',
                        pos=(-3, 85),
                        size=(172, 172),
                        opacity=1.0,
                        draw_controller_mult=0.5,
                    ),
                    _ImgDef(
                        'windowBottomCap',
                        pos=(1.5, 4),
                        size=(bwidthstd * 0.960, 100),
                        color=bcapcol1,
                        opacity=1.0,
                    ),
                ],
                txtdefs=[
                    _TxtDef(
                        '2600 Tokens',
                        pos=(bwidthstd * 0.5, pos1),
                        color=(1.1, 1.05, 1.0),
                        scale=titlescale,
                        maxwidth=bwidthstd * 0.9,
                    ),
                    _TxtDef(
                        TextContents.PRICE,
                        pos=(bwidthstd * 0.5, pos2),
                        color=(1.1, 1.05, 1.0),
                        scale=pricescale,
                        maxwidth=bwidthstd * 0.9,
                    ),
                ],
            ),
            _ButtonDef(
                itemid='gold_pass',
                width=bwidthwide,
                color=pcolor,
                imgdefs=[
                    _ImgDef(
                        'goldPass',
                        pos=(-7, 102),
                        size=(312, 156),
                        draw_controller_mult=0.3,
                    ),
                    _ImgDef(
                        'windowBottomCap',
                        pos=(8, 4),
                        size=(bwidthwide * 0.923, 116),
                        color=(0.25, 0.12, 0.15),
                        opacity=1.0,
                    ),
                ],
                txtdefs=[
                    _TxtDef(
                        'Gold Pass',
                        pos=(bwidthwide * 0.5, pos1 + 27),
                        color=(1.1, 1.05, 1.0),
                        scale=titlescale,
                        maxwidth=bwidthwide * 0.8,
                    ),
                    _TxtDef(
                        'Infinite tokens.',
                        pos=(bwidthwide * 0.5, pos1 + 6),
                        color=(1.1, 1.05, 1.0),
                        scale=0.4,
                        maxwidth=bwidthwide * 0.8,
                    ),
                    _TxtDef(
                        'No ads.',
                        pos=(bwidthwide * 0.5, pos1 + 6 - 13 * 1),
                        color=(1.1, 1.05, 1.0),
                        scale=0.4,
                        maxwidth=bwidthwide * 0.8,
                    ),
                    _TxtDef(
                        'Forever.',
                        pos=(bwidthwide * 0.5, pos1 + 6 - 13 * 2),
                        color=(1.1, 1.05, 1.0),
                        scale=0.4,
                        maxwidth=bwidthwide * 0.8,
                    ),
                    _TxtDef(
                        TextContents.PRICE,
                        pos=(bwidthwide * 0.5, pos2 - 9),
                        color=(1.1, 1.05, 1.0),
                        scale=pricescale,
                        maxwidth=bwidthwide * 0.8,
                    ),
                ],
                prepad=-8,
            ),
        ]

        self._transitioning_out = False
        self._restore_previous_call = restore_previous_call
        self._textcolor = (0.92, 0.92, 2.0)

        # If they provided an origin-widget, scale up from that.
        scale_origin: tuple[float, float] | None
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None

        uiscale = bui.app.ui_v1.uiscale
        self._width = 1000.0 if uiscale is bui.UIScale.SMALL else 800.0
        self._x_inset = 100.0 if uiscale is bui.UIScale.SMALL else 0.0
        self._height = 480.0

        self._r = 'getTokensWindow'

        top_extra = 20 if uiscale is bui.UIScale.SMALL else 0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height + top_extra),
                transition=transition,
                scale_origin_stack_offset=scale_origin,
                color=(0.3, 0.23, 0.36),
                scale=(
                    1.63
                    if uiscale is bui.UIScale.SMALL
                    else 1.2 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
                stack_offset=(
                    (0, -3) if uiscale is bui.UIScale.SMALL else (0, 0)
                ),
            )
        )

        self._back_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(45 + self._x_inset, self._height - 80),
            size=(
                (140, 60) if self._restore_previous_call is None else (60, 60)
            ),
            scale=1.0,
            autoselect=True,
            label=(
                bui.Lstr(resource='doneText')
                if self._restore_previous_call is None
                else bui.charstr(bui.SpecialChar.BACK)
            ),
            button_type=(
                'regular'
                if self._restore_previous_call is None
                else 'backSmall'
            ),
            on_activate_call=self._back,
        )

        bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 47),
            size=(0, 0),
            color=self._textcolor,
            flatness=0.0,
            shadow=1.0,
            scale=1.2,
            h_align='center',
            v_align='center',
            text='Get Tokens',
            maxwidth=260,
        )

        self._status_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.5),
            h_align='center',
            v_align='center',
            color=(0.6, 0.6, 0.6),
            scale=0.75,
            text='Loading...',
        )

        # Get all textures used by our buttons preloading so hopefully
        # they'll be in place by the time we show them.
        for bdef in self._buttondefs:
            for bimg in bdef.imgdefs:
                bui.gettexture(bimg.tex)

        # Wait for a master-server connection if need be. Otherwise we
        # could error if called at the wrong time even with an internet
        # connection, which is unintuitive.
        wait_for_connectivity(
            on_connected=bui.WeakCall(self._on_have_connectivity),
            on_cancel=bui.WeakCall(self._back),
        )

    def _on_have_connectivity(self) -> None:
        plus = bui.app.plus
        assert plus is not None

        # Sanity check; we need to be signed in. (we should not be
        # allowed to get here if we aren't, but it could happen for
        # fluke-ish reasons.)
        if plus.accounts.primary is None:
            bui.screenmessage(
                bui.Lstr(resource='notSignedInErrorText'), color=(1, 0, 0)
            )
            bui.getsound('error').play()
            self._back()
            return

        with plus.accounts.primary:
            plus.cloud.send_message_cb(
                bacommon.cloud.StoreQueryMessage(),
                on_response=bui.WeakCall(self._on_store_query_response),
            )

    def _on_load_error(self) -> None:
        bui.textwidget(
            edit=self._status_text,
            text=bui.Lstr(resource='internal.unavailableNoConnectionText'),
            color=(1, 0, 0),
        )

    def _on_store_query_response(
        self, response: bacommon.cloud.StoreQueryResponse | Exception
    ) -> None:
        # pylint: disable=too-many-locals

        plus = bui.app.plus

        # If our message failed, just error and back out.
        if isinstance(response, Exception):
            logging.info('Store query failed.', exc_info=response)

            bui.screenmessage(bui.Lstr(resource='errorText'), color=(1, 0, 0))
            bui.getsound('error').play()
            self._back()
            return

        bui.textwidget(edit=self._status_text, text='')

        xinset = 40

        scrollwidth = self._width - 2 * (self._x_inset + xinset)
        scrollheight = 280
        buttonpadding = -5

        yoffs = 5

        # We currently don't handle the zero-button case.
        assert self._buttondefs

        total_button_width = sum(
            b.width + b.prepad for b in self._buttondefs
        ) + buttonpadding * (len(self._buttondefs) - 1)

        h_scroll = bui.hscrollwidget(
            parent=self._root_widget,
            size=(scrollwidth, scrollheight),
            position=(self._x_inset + xinset, 45),
            claims_left_right=True,
            highlight=False,
            border_opacity=0.25,
        )
        subcontainer = bui.containerwidget(
            parent=h_scroll,
            background=False,
            size=(max(total_button_width, scrollwidth), scrollheight),
        )
        tinfobtn = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            label='Learn More',
            position=(self._width * 0.5 - 75, self._height * 0.703),
            size=(180, 43),
            scale=0.8,
            color=(0.4, 0.25, 0.5),
            textcolor=self._textcolor,
            on_activate_call=partial(
                self._on_learn_more_press, response.token_info_url
            ),
        )

        x = 0.0
        bwidgets: list[bui.Widget] = []
        for i, buttondef in enumerate(self._buttondefs):

            price = None if plus is None else plus.get_price(buttondef.itemid)

            x += buttondef.prepad
            tdelay = 0.3 - i / len(self._buttondefs) * 0.25
            btn = bui.buttonwidget(
                autoselect=True,
                label='',
                color=buttondef.color,
                transition_delay=tdelay,
                up_widget=tinfobtn,
                parent=subcontainer,
                size=(buttondef.width, 275),
                position=(x, -10 + yoffs),
                button_type='square',
                on_activate_call=partial(
                    self._purchase_press, buttondef.itemid
                ),
            )
            bwidgets.append(btn)
            for imgdef in buttondef.imgdefs:
                _img = bui.imagewidget(
                    parent=subcontainer,
                    size=imgdef.size,
                    position=(x + imgdef.pos[0], imgdef.pos[1] + yoffs),
                    draw_controller=btn,
                    draw_controller_mult=imgdef.draw_controller_mult,
                    color=imgdef.color,
                    texture=bui.gettexture(imgdef.tex),
                    transition_delay=tdelay,
                    opacity=imgdef.opacity,
                )
            for txtdef in buttondef.txtdefs:
                txt: bui.Lstr | str
                if isinstance(txtdef.text, TextContents):
                    if txtdef.text is TextContents.PRICE:
                        tcolor = (
                            (1, 1, 1, 0.5) if price is None else txtdef.color
                        )
                        txt = (
                            bui.Lstr(resource='unavailableText')
                            if price is None
                            else price
                        )
                    else:
                        # Make sure we cover all cases.
                        assert_never(txtdef.text)
                else:
                    tcolor = txtdef.color
                    txt = txtdef.text
                _txt = bui.textwidget(
                    parent=subcontainer,
                    text=txt,
                    position=(x + txtdef.pos[0], txtdef.pos[1] + yoffs),
                    size=(0, 0),
                    scale=txtdef.scale,
                    h_align='center',
                    v_align='center',
                    draw_controller=btn,
                    color=tcolor,
                    transition_delay=tdelay,
                    flatness=0.0,
                    shadow=1.0,
                    rotate=txtdef.rotate,
                    maxwidth=txtdef.maxwidth,
                )
            x += buttondef.width + buttonpadding
        bui.containerwidget(edit=subcontainer, visible_child=bwidgets[0])

        _tinfotxt = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.812),
            color=self._textcolor,
            shadow=1.0,
            scale=0.7,
            size=(0, 0),
            h_align='center',
            v_align='center',
            text='BombSquad\'s shiny new currency.',
        )
        _tnumtxt = bui.textwidget(
            parent=self._root_widget,
            position=(self._width - self._x_inset - 120.0, self._height - 48),
            color=(2.0, 0.7, 0.0),
            shadow=1.0,
            flatness=0.0,
            size=(0, 0),
            h_align='left',
            v_align='center',
            text=str(response.tokens),
        )
        _tlabeltxt = bui.textwidget(
            parent=self._root_widget,
            position=(self._width - self._x_inset - 123.0, self._height - 48),
            size=(0, 0),
            h_align='right',
            v_align='center',
            text=bui.charstr(bui.SpecialChar.TOKEN),
        )

    def _purchase_press(self, itemid: str) -> None:
        plus = bui.app.plus

        price = None if plus is None else plus.get_price(itemid)

        if price is None:
            if plus is not None and plus.supports_purchases():
                # Looks like internet is down or something temporary.
                errmsg = 'This purchase is not available.'
            else:
                # Looks like purchases will never work here.
                errmsg = (
                    'Sorry, purchases are not available on this build.\n'
                    'As a fallback, sign in to this account on another'
                    ' platform and make purchases from there.'
                )

            bui.screenmessage(errmsg, color=(1, 0.5, 0))
            bui.getsound('error').play()
            return

        print(f'WOULD PURCHASE {itemid}')

    def _back(self) -> None:

        # No-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        bui.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )
        if self._restore_previous_call is not None:
            self._restore_previous_call(self._root_widget)

    def _on_learn_more_press(self, url: str) -> None:
        bui.open_url(url)
