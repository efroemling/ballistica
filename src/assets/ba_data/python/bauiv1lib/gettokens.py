# Released under the MIT License. See LICENSE for details.
#
"""UI functionality for purchasing/acquiring currency."""

from __future__ import annotations

import time
from enum import Enum
from functools import partial
from dataclasses import dataclass
from typing import TYPE_CHECKING, assert_never, override

import bacommon.cloud
import bacommon.bs
import bauiv1 as bui


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
    text: str | TextContents | bui.Lstr
    pos: tuple[float, float]
    maxwidth: float | None
    scale: float = 1.0
    color: tuple[float, float, float] = (1, 1, 1)
    rotate: float | None = None


class GetTokensWindow(bui.MainWindow):
    """Window for purchasing/acquiring classic tickets."""

    class State(Enum):
        """What are we doing?"""

        LOADING = 'loading'
        NOT_SIGNED_IN = 'not_signed_in'
        HAVE_GOLD_PASS = 'have_gold_pass'
        SHOWING_STORE = 'showing_store'

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
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
                        bui.Lstr(
                            resource='tokens.numTokensText',
                            subs=[('${COUNT}', str(bacommon.bs.TOKENS1_COUNT))],
                        ),
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
                        bui.Lstr(
                            resource='tokens.numTokensText',
                            subs=[('${COUNT}', str(bacommon.bs.TOKENS2_COUNT))],
                        ),
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
                        bui.Lstr(
                            resource='tokens.numTokensText',
                            subs=[('${COUNT}', str(bacommon.bs.TOKENS3_COUNT))],
                        ),
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
                        bui.Lstr(
                            resource='tokens.numTokensText',
                            subs=[('${COUNT}', str(bacommon.bs.TOKENS4_COUNT))],
                        ),
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
                        bui.Lstr(resource='goldPass.goldPassText'),
                        pos=(bwidthwide * 0.5, pos1 + 27),
                        color=(1.1, 1.05, 1.0),
                        scale=titlescale,
                        maxwidth=bwidthwide * 0.8,
                    ),
                    _TxtDef(
                        bui.Lstr(resource='goldPass.desc1InfTokensText'),
                        pos=(bwidthwide * 0.5, pos1 + 6),
                        color=(1.1, 1.05, 1.0),
                        scale=0.4,
                        maxwidth=bwidthwide * 0.8,
                    ),
                    _TxtDef(
                        bui.Lstr(resource='goldPass.desc2NoAdsText'),
                        pos=(bwidthwide * 0.5, pos1 + 6 - 13 * 1),
                        color=(1.1, 1.05, 1.0),
                        scale=0.4,
                        maxwidth=bwidthwide * 0.8,
                    ),
                    _TxtDef(
                        bui.Lstr(resource='goldPass.desc3ForeverText'),
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
        self._textcolor = (0.92, 0.92, 2.0)

        self._query_in_flight = False
        self._last_query_time = -1.0
        self._last_query_response: bacommon.cloud.StoreQueryResponse | None = (
            None
        )

        uiscale = bui.app.ui_v1.uiscale
        self._width = 1200.0 if uiscale is bui.UIScale.SMALL else 1070.0
        self._height = 800 if uiscale is bui.UIScale.SMALL else 520.0

        self._r = 'getTokensWindow'

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            1.5
            if uiscale is bui.UIScale.SMALL
            else 1.1 if uiscale is bui.UIScale.MEDIUM else 0.95
        )
        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        target_width = min(self._width - 60, screensize[0] / scale)
        target_height = min(self._height - 70, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        self._yoffs = 0.5 * self._height + 0.5 * target_height + 20.0

        self._scroll_width = target_width

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                color=(0.3, 0.23, 0.36),
                scale=scale,
                toolbar_visibility=(
                    'get_tokens'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
            self._back_button = bui.get_special_widget('back_button')
        else:
            self._back_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(60, self._yoffs - 90),
                size=((60, 60)),
                scale=1.0,
                autoselect=True,
                label=(bui.charstr(bui.SpecialChar.BACK)),
                button_type=('backSmall'),
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )

        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._yoffs - 42),
            size=(0, 0),
            color=self._textcolor,
            flatness=0.0,
            shadow=1.0,
            scale=1.2,
            h_align='center',
            v_align='center',
            text=bui.Lstr(resource='tokens.getTokensText'),
            maxwidth=260,
        )

        self._status_text = bui.textwidget(
            parent=self._root_widget,
            size=(0, 0),
            position=(self._width * 0.5, self._height * 0.5),
            h_align='center',
            v_align='center',
            color=(0.6, 0.6, 0.6),
            scale=0.75,
            text='',
        )
        # Create a spinner - it will get cleared when state changes from
        # LOADING.
        bui.spinnerwidget(
            parent=self._root_widget,
            size=60,
            position=(self._width * 0.5, self._height * 0.5),
            style='bomb',
        )

        self._core_widgets = [
            self._back_button,
            self._title_text,
            self._status_text,
        ]

        # Get all textures used by our buttons preloading so hopefully
        # they'll be in place by the time we show them.
        for bdef in self._buttondefs:
            for bimg in bdef.imgdefs:
                bui.gettexture(bimg.tex)

        self._state = self.State.LOADING

        self._update_timer = bui.AppTimer(
            0.789, bui.WeakCall(self._update), repeat=True
        )
        self._update()

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

    def _update(self) -> None:
        # No-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        plus = bui.app.plus

        if plus is None or plus.accounts.primary is None:
            self._update_state(self.State.NOT_SIGNED_IN)
            return

        # Poll for relevant changes to the store or our account.
        now = time.monotonic()
        if not self._query_in_flight and now - self._last_query_time > 2.0:
            self._last_query_time = now
            self._query_in_flight = True
            with plus.accounts.primary:
                plus.cloud.send_message_cb(
                    bacommon.cloud.StoreQueryMessage(),
                    on_response=bui.WeakCall(self._on_store_query_response),
                )

        # Can't do much until we get a store state.
        if self._last_query_response is None:
            return

        # If we've got a gold-pass, just show that. No need to offer any
        # other purchases.
        if self._last_query_response.gold_pass:
            self._update_state(self.State.HAVE_GOLD_PASS)
            return

        # Ok we seem to be signed in and have store stuff we can show.
        # Do that.
        self._update_state(self.State.SHOWING_STORE)

    def _update_state(self, state: State) -> None:

        # We don't do much when state is unchanged.
        if state is self._state:
            # Update a few things in store mode though, such as token
            # count.
            if state is self.State.SHOWING_STORE:
                self._update_store_state()
            return

        # Ok, state is changing. Start by resetting to a blank slate.
        # self._token_count_widget = None
        for widget in self._root_widget.get_children():
            if widget not in self._core_widgets:
                widget.delete()

        # Build up new state.
        if state is self.State.NOT_SIGNED_IN:
            bui.textwidget(
                edit=self._status_text,
                color=(1, 0, 0),
                text=bui.Lstr(resource='notSignedInErrorText'),
            )
        elif state is self.State.LOADING:
            raise RuntimeError('Should never return to loading state.')
        elif state is self.State.HAVE_GOLD_PASS:
            bui.textwidget(
                edit=self._status_text,
                color=(0, 1, 0),
                text=bui.Lstr(resource='tokens.youHaveGoldPassText'),
            )
        elif state is self.State.SHOWING_STORE:
            assert self._last_query_response is not None
            bui.textwidget(edit=self._status_text, text='')
            self._build_store_for_response(self._last_query_response)
        else:
            # Make sure we handle all cases.
            assert_never(state)

        self._state = state

    def _on_load_error(self) -> None:
        bui.textwidget(
            edit=self._status_text,
            text=bui.Lstr(resource='internal.unavailableNoConnectionText'),
            color=(1, 0, 0),
        )

    def _on_store_query_response(
        self, response: bacommon.cloud.StoreQueryResponse | Exception
    ) -> None:
        self._query_in_flight = False
        if isinstance(response, bacommon.cloud.StoreQueryResponse):
            self._last_query_response = response
            # Hurry along any effects of this response.
            self._update()

    def _build_store_for_response(
        self, response: bacommon.cloud.StoreQueryResponse
    ) -> None:
        # pylint: disable=too-many-locals
        plus = bui.app.plus
        classic = bui.app.classic

        uiscale = bui.app.ui_v1.uiscale

        bui.textwidget(edit=self._status_text, text='')

        scrollheight = 280
        buttonpadding = -5

        yoffs = 5

        available_purchases = {
            p.purchaseid for p in response.available_purchases
        }
        buttondefs_shown = [
            b for b in self._buttondefs if b.itemid in available_purchases
        ]

        # Fail if something errored server-side or they didn't send us
        # anything we can show.
        if (
            response.result is not response.Result.SUCCESS
            or not buttondefs_shown
        ):
            self._on_load_error()
            return

        sidepad = 10.0
        xfudge = 6.0
        total_button_width = (
            sum(b.width + b.prepad for b in buttondefs_shown)
            + buttonpadding * (len(buttondefs_shown) - 1)
            + 2 * sidepad
        )

        h_scroll = bui.hscrollwidget(
            parent=self._root_widget,
            size=(self._scroll_width, scrollheight),
            position=(
                self._width * 0.5 - 0.5 * self._scroll_width,
                self._height * 0.5 - 0.5 * scrollheight - 40,
            ),
            claims_left_right=True,
            highlight=False,
            border_opacity=0.0,
            center_small_content=True,
        )
        subcontainer = bui.containerwidget(
            parent=h_scroll,
            background=False,
            size=(total_button_width, scrollheight),
        )
        tinfobtn = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            label=bui.Lstr(resource='learnMoreText'),
            text_scale=0.7,
            position=(
                self._width * 0.5 - 75,
                self._yoffs - 100,
            ),
            size=(180, 40),
            scale=0.8,
            color=(0.4, 0.25, 0.5),
            textcolor=self._textcolor,
            on_activate_call=partial(
                self._on_learn_more_press, response.token_info_url
            ),
        )
        if uiscale is bui.UIScale.SMALL:
            bui.widget(
                edit=tinfobtn,
                left_widget=bui.get_special_widget('back_button'),
                up_widget=bui.get_special_widget('back_button'),
            )

        bui.widget(
            edit=tinfobtn,
            right_widget=bui.get_special_widget('tokens_meter'),
        )

        x = sidepad + xfudge
        bwidgets: list[bui.Widget] = []
        for i, buttondef in enumerate(buttondefs_shown):

            price = None if plus is None else plus.get_price(buttondef.itemid)

            x += buttondef.prepad
            tdelay = 0.3 - i / len(buttondefs_shown) * 0.25
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

            if i == 0:
                bui.widget(edit=btn, left_widget=self._back_button)

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

        if bool(False):
            _tinfotxt = bui.textwidget(
                parent=self._root_widget,
                position=(
                    self._width * 0.5,
                    self._yoffs - 70,
                ),
                color=self._textcolor,
                shadow=1.0,
                scale=0.7,
                size=(0, 0),
                h_align='center',
                v_align='center',
                text=bui.Lstr(resource='tokens.shinyNewCurrencyText'),
            )

        has_removed_ads = classic is not None and (
            classic.gold_pass
            or classic.remove_ads
            or classic.accounts.have_pro()
        )
        if (
            plus is not None
            and plus.ads.has_video_ads()
            and not has_removed_ads
        ):
            _tinfotxt = bui.textwidget(
                parent=self._root_widget,
                position=(
                    self._width * 0.5,
                    self._yoffs - 120,
                ),
                color=(0.4, 1.0, 0.4),
                shadow=1.0,
                scale=0.5,
                size=(0, 0),
                h_align='center',
                v_align='center',
                maxwidth=self._scroll_width * 0.9,
                text=bui.Lstr(resource='removeInGameAdsTokenPurchaseText'),
            )

    def _purchase_press(self, itemid: str) -> None:
        plus = bui.app.plus

        price = None if plus is None else plus.get_price(itemid)

        if price is None:
            if plus is not None and plus.supports_purchases():
                # Looks like internet is down or something temporary.
                errmsg = bui.Lstr(resource='purchaseNotAvailableText')
            else:
                # Looks like purchases will never work here.
                errmsg = bui.Lstr(resource='purchaseNeverAvailableText')

            bui.screenmessage(errmsg, color=(1, 0.5, 0))
            bui.getsound('error').play()
            return

        assert plus is not None
        plus.purchase(itemid)

    def _update_store_state(self) -> None:
        """Called to make minor updates to an already shown store."""
        assert self._last_query_response is not None

    def _on_learn_more_press(self, url: str) -> None:
        bui.open_url(url)


def show_get_tokens_prompt() -> None:
    """Show a 'not enough tokens' prompt with an option to purchase more.

    Note that the purchase option may not always be available
    depending on the build of the game.
    """
    from bauiv1lib.confirm import ConfirmWindow

    assert bui.app.classic is not None

    # Currently always allowing token purchases.
    if bool(True):
        ConfirmWindow(
            bui.Lstr(resource='tokens.notEnoughTokensText'),
            show_get_tokens_window,
            ok_text=bui.Lstr(resource='tokens.getTokensText'),
            width=460,
            height=130,
        )
    else:
        ConfirmWindow(
            bui.Lstr(resource='tokens.notEnoughTokensText'),
            cancel_button=False,
            width=460,
            height=130,
        )


def show_get_tokens_window(origin_widget: bui.Widget | None = None) -> None:
    """Transition to the get-tokens main-window from anywhere."""

    # NOTE TO USERS: The code below is not the proper way to do things;
    # whenever possible one should use a MainWindow's
    # main_window_replace() or main_window_back() methods. We just need
    # to do things a bit more manually in this particular case.

    prev_main_window = bui.app.ui_v1.get_main_window()

    # Special-case: If it seems we're already in the window, do nothing.
    if isinstance(prev_main_window, GetTokensWindow):
        return

    # Set our new main window.
    bui.app.ui_v1.set_main_window(
        GetTokensWindow(origin_widget=origin_widget),
        from_window=False,
        is_auxiliary=True,
        suppress_warning=True,
    )

    # Transition out any previous main window.
    if prev_main_window is not None:
        prev_main_window.main_window_close()
