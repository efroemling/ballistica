# Released under the MIT License. See LICENSE for details.
#
# pylint: disable=too-many-lines
"""Provides chest related ui."""

from __future__ import annotations

import math
import random
from typing import override, TYPE_CHECKING

from efro.util import strict_partial
import bacommon.bs
import bauiv1 as bui

if TYPE_CHECKING:
    import datetime

    import baclassic

_g_open_voices: list[tuple[float, str, float]] = []


class ChestWindow(bui.MainWindow):
    """Allows viewing and performing operations on a chest."""

    _HIGHLIGHT_TOKEN_PURCHASES_CONFIG_KEY = (
        'Highlight Potential Token Purchases'
    )

    def __init__(
        self,
        index: int,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-statements
        self._index = index

        # Get this loading before we need it.
        self._quote_bubble_tex = bui.gettexture('quoteBubble')

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._width = 1200 if uiscale is bui.UIScale.SMALL else 750
        self._height = 800 if uiscale is bui.UIScale.SMALL else 450
        self._action_in_flight = False
        self._open_now_button: bui.Widget | None = None
        self._open_now_spinner: bui.Widget | None = None
        self._open_now_texts: list[bui.Widget] = []
        self._open_now_images: list[bui.Widget] = []
        self._watch_ad_button: bui.Widget | None = None
        self._open_me_backing: bui.Widget | None = None
        self._open_me_widgets: list[bui.Widget] = []
        self._time_string_timer: bui.AppTimer | None = None
        self._time_string_text: bui.Widget | None = None
        self._open_me_flash_timer: bui.AppTimer | None = None
        self._prizesets: list[bacommon.bs.ChestInfoResponse.Chest.PrizeSet] = []
        self._prizeindex = -1
        self._prizesettxts: dict[int, list[bui.Widget]] = {}
        self._prizesetimgs: dict[int, list[bui.Widget]] = {}
        self._chestdisplayinfo: baclassic.ChestAppearanceDisplayInfo | None = (
            None
        )
        self._suppressing_window_auto_recreates = False

        self._chest_action_ui_pause: bui.RootUIUpdatePause | None = None

        self._recreate_suppress: bui.MainWindowAutoRecreateSuppress | None = (
            None
        )

        # The set of widgets we keep when doing a clear.
        self._core_widgets: list[bui.Widget] = []

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            1.6
            if uiscale is bui.UIScale.SMALL
            else 1.1 if uiscale is bui.UIScale.MEDIUM else 0.9
        )
        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        target_height = min(self._height - 120, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        self._yoffstop = 0.5 * self._height + 0.5 * target_height + 18

        # Offset for stuff we want centered.
        self._yoffs = 0.5 * self._height + (
            220 if uiscale is bui.UIScale.SMALL else 190
        )

        self._chest_yoffs = self._yoffs - 223

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                toolbar_visibility='menu_full',
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5,
                self._yoffstop - (36 if uiscale is bui.UIScale.SMALL else 10),
            ),
            size=(0, 0),
            text=bui.Lstr(
                resource='chests.slotText',
                subs=[('${NUM}', str(index + 1))],
            ),
            color=bui.app.ui_v1.title_color,
            maxwidth=110.0 if uiscale is bui.UIScale.SMALL else 200,
            scale=0.9 if uiscale is bui.UIScale.SMALL else 1.1,
            h_align='center',
            v_align='center',
        )
        self._core_widgets.append(self._title_text)

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(50, self._yoffs - 44),
                size=(60, 55),
                scale=0.8,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                extra_touch_border_scale=2.0,
                autoselect=True,
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)
            self._core_widgets.append(btn)

        # Note: Don't need to explicitly clean this up. Just not adding
        # it to core_widgets so it will go away on next reset.
        self._loadingspinner = bui.spinnerwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.5),
            size=48,
            style='bomb',
        )

        self._infotext = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._yoffs - 200),
            size=(0, 0),
            text='',
            maxwidth=700,
            scale=0.8,
            color=(0.6, 0.5, 0.6),
            h_align='center',
            v_align='center',
        )
        self._core_widgets.append(self._infotext)

        plus = bui.app.plus
        if plus is None:
            self._error('Plus feature-set is not present.')
            return

        if plus.accounts.primary is None:
            self._error(bui.Lstr(resource='notSignedInText'))
            return

        # Start by showing info/options for our target chest. Note that
        # we always ask the server for these values even though we may
        # have them through our appmode subscription which updates the
        # chest UI. This is because the wait_for_connectivity()
        # mechanism will often bring our window up a split second before
        # the chest subscription receives its first values which would
        # lead us to incorrectly think there is no chest there. If we
        # want to optimize this in the future we could perhaps use local
        # values only if there is a chest present in them.
        assert not self._action_in_flight
        self._action_in_flight = True
        with plus.accounts.primary:
            plus.cloud.send_message_cb(
                bacommon.bs.ChestInfoMessage(chest_id=str(self._index)),
                on_response=bui.WeakCall(self._on_chest_info_response),
            )

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        # Pull anything we need from self out here; if we do it in the
        # lambda we keep self alive which is bad.
        index = self._index

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                index=index, transition=transition, origin_widget=origin_widget
            )
        )

    def _update_time_display(self, unlock_time: datetime.datetime) -> None:
        # Once our target text widget disappears, kill our timer.
        if not self._time_string_text:
            self._time_string_timer = None
            return
        now = bui.utc_now_cloud()
        secs_till_open = max(0.0, (unlock_time - now).total_seconds())
        tstr = (
            bui.timestring(secs_till_open, centi=False)
            if secs_till_open > 0
            else ''
        )
        bui.textwidget(edit=self._time_string_text, text=tstr)

    def _on_chest_info_response(
        self, response: bacommon.bs.ChestInfoResponse | Exception
    ) -> None:
        assert self._action_in_flight  # Should be us.
        self._action_in_flight = False

        if isinstance(response, Exception):
            self._error(
                bui.Lstr(resource='internal.unableToCompleteTryAgainText'),
                minor=True,
            )
            return

        if response.chest is None:
            self._show_about_chest_slots()
            return

        assert response.user_tokens is not None
        self._show_chest_actions(response.user_tokens, response.chest)

    def _on_chest_action_response(
        self, response: bacommon.bs.ChestActionResponse | Exception
    ) -> None:
        assert self._action_in_flight  # Should be us.
        self._action_in_flight = False

        # Allow the root ui to resume its normal automatic value display
        # as soon as any animations we kick off here complete.
        self._chest_action_ui_pause = None

        # Communication/local error:
        if isinstance(response, Exception):
            self._error(
                bui.Lstr(resource='internal.unableToCompleteTryAgainText'),
                minor=True,
            )
            return

        # Server-side error:
        if response.error is not None:
            self._error(bui.Lstr(translate=('serverResponses', response.error)))
            return

        toffs = 0.0
        # If there's contents listed in the response, show them.
        if response.contents is not None:
            toffs = self._show_chest_contents(response)
        else:
            # Otherwise we're done here; just close out our UI.
            self.main_window_back()

        # Lastly, run any bundled effects.
        assert bui.app.classic is not None
        bui.app.classic.run_bs_client_effects(response.effects, delay=toffs)

    def _show_chest_actions(
        self, user_tokens: int, chest: bacommon.bs.ChestInfoResponse.Chest
    ) -> None:
        """Show state for our chest."""
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import
        from baclassic import (
            ClassicAppMode,
            CHEST_APPEARANCE_DISPLAY_INFOS,
            CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT,
        )

        plus = bui.app.plus
        assert plus is not None

        # We expect to be run under classic app mode.
        mode = bui.app.mode
        if not isinstance(mode, ClassicAppMode):
            self._error('Classic app mode not active.')
            return

        self._reset()

        self._chestdisplayinfo = CHEST_APPEARANCE_DISPLAY_INFOS.get(
            chest.appearance, CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT
        )

        bui.textwidget(
            edit=self._title_text,
            text=bui.Lstr(
                translate=('displayItemNames', chest.appearance.pretty_name)
            ),
        )

        imgsize = 145
        bui.imagewidget(
            parent=self._root_widget,
            position=(self._width * 0.5 - imgsize * 0.5, self._chest_yoffs),
            color=self._chestdisplayinfo.color,
            size=(imgsize, imgsize),
            texture=bui.gettexture(self._chestdisplayinfo.texclosed),
            tint_texture=bui.gettexture(self._chestdisplayinfo.texclosedtint),
            tint_color=self._chestdisplayinfo.tint,
            tint2_color=self._chestdisplayinfo.tint2,
        )

        # Store the prize-sets so we can display odds/etc. Sort them
        # with largest weights first.
        self._prizesets = sorted(
            chest.prizesets, key=lambda s: s.weight, reverse=True
        )

        if chest.unlock_tokens > 0:
            lsize = 30
            bui.imagewidget(
                parent=self._root_widget,
                position=(
                    self._width * 0.5 - imgsize * 0.4 - lsize * 0.5,
                    self._chest_yoffs + 27.0,
                ),
                size=(lsize, lsize),
                texture=bui.gettexture('lock'),
            )

        # Time string.
        if chest.unlock_tokens != 0:
            self._time_string_text = bui.textwidget(
                parent=self._root_widget,
                position=(self._width * 0.5, self._yoffs - 85),
                size=(0, 0),
                text='',
                maxwidth=700,
                scale=0.6,
                color=(0.7, 0.7, 0.83),
                h_align='center',
                v_align='center',
            )
            bui.textwidget(
                parent=self._root_widget,
                position=(self._width * 0.5, self._yoffs - 85 + 18),
                size=(0, 0),
                text=bui.Lstr(resource='chests.unlocksInText'),
                maxwidth=700,
                scale=0.4,
                color=(0.7, 0.65, 1, 0.55),
                h_align='center',
                v_align='center',
                flatness=1.0,
                shadow=1.0,
            )
            self._update_time_display(chest.unlock_time)
            self._time_string_timer = bui.AppTimer(
                1.0,
                repeat=True,
                call=bui.WeakCall(self._update_time_display, chest.unlock_time),
            )

        # Allow watching an ad IF the server tells us we can AND we have
        # an ad ready to show.
        show_ad_button = (
            chest.unlock_tokens > 0
            and chest.ad_allow
            and plus.ads.have_incentivized_ad()
        )

        bwidth = 130
        bheight = 90
        bposy = -330 if chest.unlock_tokens == 0 else -340
        hspace = 20
        boffsx = (hspace * -0.5 - bwidth * 0.5) if show_ad_button else 0.0

        self._open_now_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5 - bwidth * 0.5 + boffsx,
                self._yoffs + bposy,
            ),
            size=(bwidth, bheight),
            label='',
            button_type='square',
            autoselect=True,
            on_activate_call=bui.WeakCall(
                self._open_press, user_tokens, chest.unlock_tokens
            ),
            enable_sound=False,
        )
        bui.containerwidget(
            edit=self._root_widget, selected_child=self._open_now_button
        )
        self._open_now_images = []
        self._open_now_texts = []

        iconsize = 50
        if chest.unlock_tokens == 0:
            self._open_now_texts.append(
                bui.textwidget(
                    parent=self._root_widget,
                    text=bui.Lstr(resource='openText'),
                    position=(
                        self._width * 0.5 + boffsx,
                        self._yoffs + bposy + bheight * 0.5,
                    ),
                    color=(0, 1, 0),
                    draw_controller=self._open_now_button,
                    scale=0.7,
                    maxwidth=bwidth * 0.8,
                    size=(0, 0),
                    h_align='center',
                    v_align='center',
                )
            )
        else:
            self._open_now_texts.append(
                bui.textwidget(
                    parent=self._root_widget,
                    text=bui.Lstr(resource='openNowText'),
                    position=(
                        self._width * 0.5 + boffsx,
                        self._yoffs + bposy + bheight * 1.15,
                    ),
                    maxwidth=bwidth * 0.8,
                    scale=0.7,
                    color=(0.7, 1, 0.7),
                    size=(0, 0),
                    h_align='center',
                    v_align='center',
                )
            )
            self._open_now_images.append(
                bui.imagewidget(
                    parent=self._root_widget,
                    size=(iconsize, iconsize),
                    position=(
                        self._width * 0.5 - iconsize * 0.5 + boffsx,
                        self._yoffs + bposy + bheight * 0.35,
                    ),
                    draw_controller=self._open_now_button,
                    texture=bui.gettexture('coin'),
                )
            )
            self._open_now_texts.append(
                bui.textwidget(
                    parent=self._root_widget,
                    text=bui.Lstr(
                        resource='tokens.numTokensText',
                        subs=[('${COUNT}', str(chest.unlock_tokens))],
                    ),
                    position=(
                        self._width * 0.5 + boffsx,
                        self._yoffs + bposy + bheight * 0.25,
                    ),
                    scale=0.65,
                    color=(0, 1, 0),
                    draw_controller=self._open_now_button,
                    maxwidth=bwidth * 0.8,
                    size=(0, 0),
                    h_align='center',
                    v_align='center',
                )
            )
        self._open_now_spinner = bui.spinnerwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5 + boffsx,
                self._yoffs + bposy + 0.5 * bheight,
            ),
            visible=False,
        )

        if show_ad_button:
            bui.textwidget(
                parent=self._root_widget,
                text=bui.Lstr(resource='chests.reduceWaitText'),
                position=(
                    self._width * 0.5 + hspace * 0.5 + bwidth * 0.5,
                    self._yoffs + bposy + bheight * 1.15,
                ),
                maxwidth=bwidth * 0.8,
                scale=0.7,
                color=(0.7, 1, 0.7),
                size=(0, 0),
                h_align='center',
                v_align='center',
            )
            self._watch_ad_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(
                    self._width * 0.5 + hspace * 0.5,
                    self._yoffs + bposy,
                ),
                size=(bwidth, bheight),
                label='',
                button_type='square',
                autoselect=True,
                on_activate_call=bui.WeakCall(self._watch_ad_press),
                enable_sound=False,
            )
            bui.imagewidget(
                parent=self._root_widget,
                size=(iconsize, iconsize),
                position=(
                    self._width * 0.5
                    + hspace * 0.5
                    + bwidth * 0.5
                    - iconsize * 0.5,
                    self._yoffs + bposy + bheight * 0.35,
                ),
                draw_controller=self._watch_ad_button,
                color=(1.5, 1.0, 2.0),
                texture=bui.gettexture('tv'),
            )
            # Note to self: AdMob requires rewarded ad usage
            # specifically says 'Ad' in it.
            bui.textwidget(
                parent=self._root_widget,
                text=bui.Lstr(resource='watchAnAdText'),
                position=(
                    self._width * 0.5 + hspace * 0.5 + bwidth * 0.5,
                    self._yoffs + bposy + bheight * 0.25,
                ),
                scale=0.65,
                color=(0, 1, 0),
                draw_controller=self._watch_ad_button,
                maxwidth=bwidth * 0.8,
                size=(0, 0),
                h_align='center',
                v_align='center',
            )

        self._show_odds(initial_highlighted_row=-1)

        # Show 'open me' tip IF we don't have a gold pass but do have
        # enough tokens to open the chest now and have not suppressed
        # the tip.
        classic = bui.app.classic
        assert classic is not None
        if (
            not classic.gold_pass
            and chest.unlock_tokens > 0
            and user_tokens >= chest.unlock_tokens
            and bui.app.config.resolve(
                self._HIGHLIGHT_TOKEN_PURCHASES_CONFIG_KEY
            )
        ):

            open_me_x = self._width * 0.5 - 210
            open_me_y = self._yoffs - 60
            self._open_me_backing = bui.imagewidget(
                parent=self._root_widget,
                position=(open_me_x - 125, open_me_y - 226),
                color=(0, 1.0, 0.3),
                opacity=0.3,
                size=(270, 270),
                texture=self._quote_bubble_tex,
            )
            self._open_me_flash_timer = bui.AppTimer(
                0.05,
                repeat=True,
                call=bui.WeakCall(self._open_me_backing_update),
            )
            self._open_me_widgets.clear()
            self._open_me_widgets.append(self._open_me_backing)
            self._open_me_widgets.append(
                bui.textwidget(
                    parent=self._root_widget,
                    position=(open_me_x, open_me_y - 40),
                    size=(0, 0),
                    text=bui.Lstr(
                        value='*${A}',
                        subs=[('${A}', bui.Lstr(resource='openMeText'))],
                    ),
                    # text=bui.Lstr(resource='openMeText'),
                    maxwidth=175,
                    scale=0.7,
                    color=(0, 1.0, 0.7, 1),
                    h_align='center',
                    v_align='center',
                    flatness=0.8,
                    shadow=0.2,
                )
            )
            self._open_me_widgets.append(
                bui.textwidget(
                    parent=self._root_widget,
                    position=(open_me_x, open_me_y - 79),
                    size=(0, 0),
                    text=bui.Lstr(resource='tokens.openNowDescriptionText'),
                    maxwidth=175,
                    max_height=55,
                    scale=0.55,
                    color=(0, 1.0, 0.7, 1),
                    h_align='center',
                    v_align='center',
                    flatness=1.0,
                    shadow=0.2,
                )
            )
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(open_me_x - 70, open_me_y - 140),
                label=bui.Lstr(resource='stopRemindingMeText'),
                size=(140, 30),
                textcolor=(0.0, 1.0, 0.7),
                text_scale=0.5,
                color=(0.0, 0.8, 0.5),
                autoselect=True,
                text_flatness=1.0,
                on_activate_call=bui.WeakCall(self._stop_showing_open_me_press),
            )
            # Avoid depth issues with the quote-bubble image.
            bui.widget(edit=btn, depth_range=(0.1, 1.0))
            self._open_me_widgets.append(btn)

    def _open_me_backing_update(self) -> None:
        # Once our target widget disappears, kill our timer.
        if not self._open_me_backing:
            self._open_me_flash_timer = None
            return

        mult = 1.0 + 0.06 * math.sin(bui.apptime() * 16.0)
        bui.imagewidget(
            edit=self._open_me_backing,
            color=(0, mult, 0.4 * mult),
        )

    def _stop_showing_open_me_press(self) -> None:
        for widget in self._open_me_widgets:
            widget.delete(ignore_missing=True)

        bui.app.config[self._HIGHLIGHT_TOKEN_PURCHASES_CONFIG_KEY] = False
        bui.app.config.apply_and_commit()

    def _highlight_odds_row(self, row: int, extra: bool = False) -> None:

        for rindex, imgs in self._prizesetimgs.items():
            opacity = (
                (0.9 if extra else 0.75)
                if rindex == row
                else (0.4 if extra else 0.5)
            )
            for img in imgs:
                if img:
                    bui.imagewidget(edit=img, opacity=opacity)

        for rindex, txts in self._prizesettxts.items():
            opacity = (
                (0.9 if extra else 0.75)
                if rindex == row
                else (0.4 if extra else 0.5)
            )
            for txt in txts:
                if txt:
                    bui.textwidget(edit=txt, color=(0.7, 0.65, 1, opacity))

    def _show_odds(
        self,
        *,
        initial_highlighted_row: int,
        initial_highlighted_extra: bool = False,
    ) -> None:
        # pylint: disable=too-many-locals
        xoffs = 110

        totalweight = max(0.001, sum(t.weight for t in self._prizesets))

        rowheight = 25
        totalheight = (len(self._prizesets) + 1) * rowheight
        x = self._width * 0.5 + xoffs
        y = self._yoffs - 150.0 + totalheight * 0.5

        # Title.
        bui.textwidget(
            parent=self._root_widget,
            text=bui.Lstr(resource='chests.prizeOddsText'),
            color=(0.7, 0.65, 1, 0.5),
            flatness=1.0,
            shadow=1.0,
            position=(x, y),
            scale=0.55,
            size=(0, 0),
            h_align='left',
            v_align='center',
        )
        y -= 5.0

        prizesettxts: list[bui.Widget]
        prizesetimgs: list[bui.Widget]

        def _mkicon(img: str) -> None:
            iconsize = 20.0
            nonlocal x
            nonlocal prizesetimgs
            prizesetimgs.append(
                bui.imagewidget(
                    parent=self._root_widget,
                    size=(iconsize, iconsize),
                    position=(x, y - iconsize * 0.5),
                    texture=bui.gettexture(img),
                    opacity=0.4,
                )
            )
            x += iconsize

        def _mktxt(txt: str, advance: bool = True) -> None:
            tscale = 0.45
            nonlocal x
            nonlocal prizesettxts
            prizesettxts.append(
                bui.textwidget(
                    parent=self._root_widget,
                    text=txt,
                    flatness=1.0,
                    shadow=1.0,
                    position=(x, y),
                    scale=tscale,
                    size=(0, 0),
                    h_align='left',
                    v_align='center',
                )
            )
            if advance:
                x += (bui.get_string_width(txt, suppress_warning=True)) * tscale

        self._prizesettxts = {}
        self._prizesetimgs = {}

        for i, p in enumerate(self._prizesets):
            prizesettxts = self._prizesettxts.setdefault(i, [])
            prizesetimgs = self._prizesetimgs.setdefault(i, [])
            x = self._width * 0.5 + xoffs
            y -= rowheight
            percent = 100.0 * p.weight / totalweight

            # Show decimals only if we get very small percentages (looks
            # better than rounding as '0%').
            percenttxt = (
                f'{percent:.2f}%:'
                if percent < 0.095
                else (
                    f'{percent:.1f}%:'
                    if percent < 0.95
                    else f'{round(percent)}%:'
                )
            )

            # We advance manually here to keep values lined up
            # (otherwise single digit percent rows don't line up with
            # double digit ones).
            _mktxt(percenttxt, advance=False)
            x += 35.0

            for item in p.contents:
                x += 5.0
                if isinstance(item.item, bacommon.bs.TicketsDisplayItem):
                    _mktxt(str(item.item.count))
                    _mkicon('tickets')
                elif isinstance(item.item, bacommon.bs.TokensDisplayItem):
                    _mktxt(str(item.item.count))
                    _mkicon('coin')
                else:
                    # For other cases just fall back on text desc.
                    #
                    # Translate the wrapper description and apply any subs.
                    descfin = bui.Lstr(
                        translate=('serverResponses', item.description)
                    ).evaluate()
                    subs = (
                        []
                        if item.description_subs is None
                        else item.description_subs
                    )
                    assert len(subs) % 2 == 0  # Should always be even.
                    for j in range(0, len(subs) - 1, 2):
                        descfin = descfin.replace(subs[j], subs[j + 1])
                    _mktxt(descfin)
        self._highlight_odds_row(
            initial_highlighted_row, extra=initial_highlighted_extra
        )

    def _open_press(self, user_tokens: int, token_payment: int) -> None:
        from bauiv1lib.gettokens import show_get_tokens_prompt

        bui.getsound('click01').play()

        # Allow only one in-flight action at once.
        if self._action_in_flight:
            bui.screenmessage(
                bui.Lstr(resource='pleaseWaitText'), color=(1, 0, 0)
            )
            bui.getsound('error').play()
            return

        plus = bui.app.plus
        assert plus is not None

        if plus.accounts.primary is None:
            self._error(bui.Lstr(resource='notSignedInText'))
            return

        # Offer to purchase tokens if they don't have enough.
        if user_tokens < token_payment:
            # Hack: We disable normal swish for the open button and it
            # seems weird without a swish here, so explicitly do one.
            bui.getsound('swish').play()
            show_get_tokens_prompt()
            return

        self._action_in_flight = True

        # Pause implicit root-ui updates at least until we're done with
        # this message, as we might want to explicitly animate stuff from
        # the results and don't want live values to jump the gun.
        self._chest_action_ui_pause = bui.RootUIUpdatePause()

        with plus.accounts.primary:
            plus.cloud.send_message_cb(
                bacommon.bs.ChestActionMessage(
                    chest_id=str(self._index),
                    action=bacommon.bs.ChestActionMessage.Action.UNLOCK,
                    token_payment=token_payment,
                ),
                on_response=bui.WeakCall(self._on_chest_action_response),
            )

        # Convey that something is in progress.
        if self._open_now_button:
            bui.spinnerwidget(edit=self._open_now_spinner, visible=True)
            for twidget in self._open_now_texts:
                bui.textwidget(edit=twidget, color=(1, 1, 1, 0.2))
            for iwidget in self._open_now_images:
                bui.imagewidget(edit=iwidget, opacity=0.2)

    def _watch_ad_press(self) -> None:

        bui.getsound('click01').play()

        # Allow only one in-flight action at once.
        if self._action_in_flight:
            bui.screenmessage(
                bui.Lstr(resource='pleaseWaitText'), color=(1, 0, 0)
            )
            bui.getsound('error').play()
            return

        assert bui.app.plus is not None

        # If we watch an ad, suppress window auto-recreates until our
        # window goes away. It is possible for ad viewing to do things
        # like show/hide system toolbars which can cause our app window
        # to resize, and we don't want that to result in our chest
        # window being recreated which effectively cancels the ad view
        # flow.
        self._recreate_suppress = bui.MainWindowAutoRecreateSuppress()

        self._action_in_flight = True
        bui.app.plus.ads.show_ad_2(
            'reduce_chest_wait',
            on_completion_call=bui.WeakCall(self._watch_ad_complete),
        )

        # Convey that something is in progress.
        if self._watch_ad_button:
            bui.buttonwidget(edit=self._watch_ad_button, color=(0.4, 0.4, 0.4))

    def _watch_ad_complete(self, actually_showed: bool) -> None:

        assert self._action_in_flight  # Should be ad view.
        self._action_in_flight = False

        if not actually_showed:
            return

        # Allow only one in-flight action at once.
        if self._action_in_flight:
            bui.screenmessage(
                bui.Lstr(resource='pleaseWaitText'), color=(1, 0, 0)
            )
            bui.getsound('error').play()
            return

        plus = bui.app.plus
        assert plus is not None

        if plus.accounts.primary is None:
            self._error(bui.Lstr(resource='notSignedInText'))
            return

        self._action_in_flight = True

        # Pause implicit root-ui updates at least until we're done with
        # this message, as we might want to explicitly animate stuff from
        # the results and don't want live values to jump the gun.
        self._chest_action_ui_pause = bui.RootUIUpdatePause()

        with plus.accounts.primary:
            plus.cloud.send_message_cb(
                bacommon.bs.ChestActionMessage(
                    chest_id=str(self._index),
                    action=bacommon.bs.ChestActionMessage.Action.AD,
                    token_payment=0,
                ),
                on_response=bui.WeakCall(self._on_chest_action_response),
            )

    def _reset(self) -> None:
        """Clear all non-permanent widgets and clear infotext."""
        for widget in self._root_widget.get_children():
            if widget not in self._core_widgets:
                widget.delete()
        bui.textwidget(edit=self._infotext, text='', color=(1, 1, 1))

    def _error(self, msg: str | bui.Lstr, minor: bool = False) -> None:
        """Put ourself in an error state with a visible error message."""
        self._reset()
        bui.textwidget(
            edit=self._infotext,
            text=msg,
            color=(1, 0.5, 0.5) if minor else (1, 0, 0),
        )

    def _show_about_chest_slots(self) -> None:
        # No-op if our ui is dead.
        if not self._root_widget:
            return

        self._reset()
        bui.textwidget(
            edit=self._infotext,
            text=bui.Lstr(resource='chests.slotDescriptionText'),
            color=(1, 1, 1),
        )

    def _show_chest_contents(
        self, response: bacommon.bs.ChestActionResponse
    ) -> float:
        # pylint: disable=too-many-locals

        from baclassic import show_display_item

        # No-op if our ui is dead.
        if not self._root_widget:
            return 0.0

        assert response.contents is not None

        # Insert test items for testing.
        if bool(False):
            response.contents += [
                bacommon.bs.DisplayItemWrapper.for_display_item(
                    bacommon.bs.TestDisplayItem()
                )
            ]

        tincr = 0.4
        tendoffs = tincr * 4.0
        toffs = 0.0

        bui.getsound('revUp').play(volume=2.0)

        # Show nothing but the chest icon and animate it shaking.
        self._reset()
        imgsize = 145
        assert self._chestdisplayinfo is not None
        img = bui.imagewidget(
            parent=self._root_widget,
            color=self._chestdisplayinfo.color,
            texture=bui.gettexture(self._chestdisplayinfo.texclosed),
            tint_texture=bui.gettexture(self._chestdisplayinfo.texclosedtint),
            tint_color=self._chestdisplayinfo.tint,
            tint2_color=self._chestdisplayinfo.tint2,
        )

        def _set_img(x: float, scale: float) -> None:
            if not img:
                return
            bui.imagewidget(
                edit=img,
                position=(
                    self._width * 0.5 - imgsize * scale * 0.5 + x,
                    self._yoffs - 223 + imgsize * 0.5 - imgsize * scale * 0.5,
                ),
                size=(imgsize * scale, imgsize * scale),
            )

        # Set initial place.
        _set_img(0.0, 1.0)

        sign = 1.0
        while toffs < tendoffs:
            toffs += 0.03 * random.uniform(0.5, 1.5)
            sign = -sign
            bui.apptimer(
                toffs,
                bui.Call(
                    _set_img,
                    x=(
                        20.0
                        * random.uniform(0.3, 1.0)
                        * math.pow(toffs / tendoffs, 2.0)
                        * sign
                    ),
                    scale=1.0 - 0.2 * math.pow(toffs / tendoffs, 2.0),
                ),
            )

        xspacing = 100
        xoffs = -0.5 * (len(response.contents) - 1) * xspacing
        bui.apptimer(
            toffs - 0.2, lambda: bui.getsound('corkPop2').play(volume=4.0)
        )
        # Play a variety of voice sounds.

        # We keep a global list of voice options which we randomly pull
        # from and refill when empty. This ensures everything gets
        # played somewhat frequently and minimizes annoying repeats.
        global _g_open_voices  # pylint: disable=global-statement
        if not _g_open_voices:
            _g_open_voices = [
                (0.3, 'woo3', 2.5),
                (0.1, 'gasp', 1.3),
                (0.2, 'woo2', 2.0),
                (0.2, 'wow', 2.0),
                (0.2, 'kronk2', 2.0),
                (0.2, 'mel03', 2.0),
                (0.2, 'aww', 2.0),
                (0.4, 'nice', 2.0),
                (0.3, 'yeah', 1.5),
                (0.2, 'woo', 1.0),
                (0.5, 'ooh', 0.8),
            ]

        voicetimeoffs, voicename, volume = _g_open_voices.pop(
            random.randrange(len(_g_open_voices))
        )
        bui.apptimer(
            toffs + voicetimeoffs,
            lambda: bui.getsound(voicename).play(volume=volume),
        )

        toffsopen = toffs
        bui.apptimer(toffs, bui.WeakCall(self._show_chest_opening))
        toffs += tincr * 1.0
        width = xspacing * 0.95

        for item in response.contents:
            toffs += tincr
            bui.apptimer(
                toffs - 0.1, lambda: bui.getsound('cashRegister').play()
            )
            bui.apptimer(
                toffs,
                strict_partial(
                    show_display_item,
                    item,
                    self._root_widget,
                    pos=(
                        self._width * 0.5 + xoffs,
                        self._yoffs - 250.0,
                    ),
                    width=width,
                ),
            )
            xoffs += xspacing
        toffs += tincr
        bui.apptimer(toffs, bui.WeakCall(self._show_done_button))

        self._show_odds(initial_highlighted_row=-1)

        # Store this for later
        self._prizeindex = response.prizeindex

        # The final result was already randomly selected on the server,
        # but we want to give the illusion of randomness here, so cycle
        # through highlighting our options and stop on the winner when
        # the chest opens. To do this, we start at the end at the prize
        # and work backwards setting timers.
        if self._prizesets:
            toffs2 = toffsopen - 0.01
            amt = 0.02
            i = self._prizeindex
            while toffs2 > 0.0:
                bui.apptimer(
                    toffs2,
                    bui.WeakCall(self._highlight_odds_row, i),
                )
                toffs2 -= amt
                amt *= 1.05 * random.uniform(0.9, 1.1)
                i = (i - 1) % len(self._prizesets)

        # Let the caller know how long we'll take in case they want to
        # schedule stuff after.
        return toffs + tincr

    def _show_chest_opening(self) -> None:

        # No-op if our ui is dead.
        if not self._root_widget:
            return

        self._reset()
        imgsize = 145
        bui.getsound('hiss').play()
        assert self._chestdisplayinfo is not None
        img = bui.imagewidget(
            parent=self._root_widget,
            color=self._chestdisplayinfo.color,
            texture=bui.gettexture(self._chestdisplayinfo.texopen),
            tint_texture=bui.gettexture(self._chestdisplayinfo.texopentint),
            tint_color=self._chestdisplayinfo.tint,
            tint2_color=self._chestdisplayinfo.tint2,
        )
        tincr = 0.8
        tendoffs = tincr * 2.0
        toffs = 0.0

        def _set_img(x: float, scale: float) -> None:
            if not img:
                return
            bui.imagewidget(
                edit=img,
                position=(
                    self._width * 0.5 - imgsize * scale * 0.5 + x,
                    self._yoffs - 223 + imgsize * 0.5 - imgsize * scale * 0.5,
                ),
                size=(imgsize * scale, imgsize * scale),
            )

        # Set initial place.
        _set_img(0.0, 1.0)

        sign = 1.0
        while toffs < tendoffs:
            toffs += 0.03 * random.uniform(0.5, 1.5)
            sign = -sign
            # Note: we speed x along here (multing toffs) so position
            # comes to rest before scale.
            bui.apptimer(
                toffs,
                bui.Call(
                    _set_img,
                    x=(
                        1.0
                        * random.uniform(0.3, 1.0)
                        * (
                            1.0
                            - math.pow(min(1.0, 3.0 * toffs / tendoffs), 2.0)
                        )
                        * sign
                    ),
                    scale=1.0 - 0.1 * math.pow(toffs / tendoffs, 0.5),
                ),
            )

        self._show_odds(
            initial_highlighted_row=self._prizeindex,
            initial_highlighted_extra=True,
        )

    def _show_done_button(self) -> None:
        # No-op if our ui is dead.
        if not self._root_widget:
            return

        bwidth = 200
        bheight = 60

        btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5 - bwidth * 0.5,
                self._yoffs - 350,
            ),
            size=(bwidth, bheight),
            label=bui.Lstr(resource='doneText'),
            autoselect=True,
            on_activate_call=self.main_window_back,
        )
        bui.containerwidget(
            edit=self._root_widget, selected_child=btn, start_button=btn
        )


# Slight hack: we define window different classes for our different
# chest slots so that the default UI behavior is to replace each other
# when different ones are pressed. If they are all the same window class
# then the default behavior for such presses is to toggle the existing
# one back off.


class ChestWindow0(ChestWindow):
    """Child class of ChestWindow for slighty hackish reasons."""


class ChestWindow1(ChestWindow):
    """Child class of ChestWindow for slighty hackish reasons."""


class ChestWindow2(ChestWindow):
    """Child class of ChestWindow for slighty hackish reasons."""


class ChestWindow3(ChestWindow):
    """Child class of ChestWindow for slighty hackish reasons."""
