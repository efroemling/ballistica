# Released under the MIT License. See LICENSE for details.
#
# pylint: disable=too-many-lines
"""Provides a popup window to view achievements."""

from __future__ import annotations

import weakref
from functools import partial
from dataclasses import dataclass
from typing import override, assert_never, TYPE_CHECKING

from efro.util import strict_partial, pairs_from_flat
from efro.error import CommunicationError
import bacommon.bs
import bauiv1 as bui

if TYPE_CHECKING:
    import datetime
    from typing import Callable


class _Section:
    def get_height(self) -> float:
        """Return section height."""
        raise NotImplementedError()

    def get_button_row(self) -> list[bui.Widget]:
        """Return rows of selectable controls."""
        return []

    def emit(self, subcontainer: bui.Widget, y: float) -> None:
        """Emit the section."""


class _TextSection(_Section):

    def __init__(
        self,
        *,
        sub_width: float,
        text: bui.Lstr | str,
        spacing_top: float = 0.0,
        spacing_bottom: float = 0.0,
        scale: float = 0.6,
        color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
    ) -> None:
        self.sub_width = sub_width
        self.spacing_top = spacing_top
        self.spacing_bottom = spacing_bottom
        self.color = color

        # We need to bake this down since we plug its final size into
        # our math.
        self.textbaked = text.evaluate() if isinstance(text, bui.Lstr) else text

        # Calc scale to fit width and then see what height we need at
        # that scale.
        t_width = max(
            10.0,
            bui.get_string_width(self.textbaked, suppress_warning=True) * scale,
        )
        self.text_scale = scale * min(1.0, (sub_width * 0.9) / t_width)

        self.text_height = (
            0.0
            if not self.textbaked
            else bui.get_string_height(self.textbaked, suppress_warning=True)
        ) * self.text_scale

        self.full_height = self.text_height + spacing_top + spacing_bottom

    @override
    def get_height(self) -> float:
        return self.full_height

    @override
    def emit(self, subcontainer: bui.Widget, y: float) -> None:
        bui.textwidget(
            parent=subcontainer,
            position=(
                self.sub_width * 0.5,
                y - self.spacing_top - self.text_height * 0.5,
            ),
            color=self.color,
            scale=self.text_scale,
            flatness=1.0,
            shadow=1.0,
            text=self.textbaked,
            size=(0, 0),
            h_align='center',
            v_align='center',
        )


class _ButtonSection(_Section):

    def __init__(
        self,
        *,
        sub_width: float,
        label: bui.Lstr | str,
        color: tuple[float, float, float],
        label_color: tuple[float, float, float],
        call: Callable[[_ButtonSection], None],
        spacing_top: float = 0.0,
        spacing_bottom: float = 0.0,
    ) -> None:
        self.sub_width = sub_width
        self.spacing_top = spacing_top
        self.spacing_bottom = spacing_bottom
        self.color = color
        self.label_color = label_color
        self.button: bui.Widget | None = None
        self.call = call
        self.labelfin = label
        self.button_width = 130
        self.button_height = 30
        self.full_height = self.button_height + spacing_top + spacing_bottom

    @override
    def get_height(self) -> float:
        return self.full_height

    @staticmethod
    def weak_call(section: weakref.ref[_ButtonSection]) -> None:
        """Call button section call if section still exists."""
        section_strong = section()
        if section_strong is None:
            return

        section_strong.call(section_strong)

    @override
    def emit(self, subcontainer: bui.Widget, y: float) -> None:
        self.button = bui.buttonwidget(
            parent=subcontainer,
            position=(
                self.sub_width * 0.5 - self.button_width * 0.5,
                y - self.spacing_top - self.button_height,
            ),
            autoselect=True,
            label=self.labelfin,
            textcolor=self.label_color,
            text_scale=0.55,
            size=(self.button_width, self.button_height),
            color=self.color,
            on_activate_call=strict_partial(self.weak_call, weakref.ref(self)),
        )
        bui.widget(edit=self.button, depth_range=(0.1, 1.0))

    @override
    def get_button_row(self) -> list[bui.Widget]:
        """Return rows of selectable controls."""
        assert self.button is not None
        return [self.button]


class _DisplayItemsSection(_Section):

    def __init__(
        self,
        *,
        sub_width: float,
        items: list[bacommon.bs.DisplayItemWrapper],
        width: float = 100.0,
        spacing_top: float = 0.0,
        spacing_bottom: float = 0.0,
    ) -> None:
        self.display_item_width = width

        # FIXME - ask for this somewhere in case it changes.
        self.display_item_height = self.display_item_width * 0.666
        self.items = items
        self.sub_width = sub_width
        self.spacing_top = spacing_top
        self.spacing_bottom = spacing_bottom
        self.full_height = (
            self.display_item_height + spacing_top + spacing_bottom
        )

    @override
    def get_height(self) -> float:
        return self.full_height

    @override
    def emit(self, subcontainer: bui.Widget, y: float) -> None:
        # pylint: disable=cyclic-import
        from baclassic import show_display_item

        xspacing = 1.1 * self.display_item_width
        total_width = (
            0 if not self.items else ((len(self.items) - 1) * xspacing)
        )
        x = -0.5 * total_width
        for item in self.items:
            show_display_item(
                item,
                subcontainer,
                pos=(
                    self.sub_width * 0.5 + x,
                    y - self.spacing_top - self.display_item_height * 0.5,
                ),
                width=self.display_item_width,
            )
            x += xspacing


class _ExpireTimeSection(_Section):

    def __init__(
        self,
        *,
        sub_width: float,
        time: datetime.datetime,
        spacing_top: float = 0.0,
        spacing_bottom: float = 0.0,
    ) -> None:
        self.time = time
        self.sub_width = sub_width
        self.spacing_top = spacing_top
        self.spacing_bottom = spacing_bottom
        self.color = (1.0, 0.0, 1.0)
        self._timer: bui.AppTimer | None = None
        self._widget: bui.Widget | None = None
        self.text_scale = 0.4
        self.text_height = 30.0 * self.text_scale
        self.full_height = self.text_height + spacing_top + spacing_bottom

    @override
    def get_height(self) -> float:
        return self.full_height

    def _update(self) -> None:
        if not self._widget:
            return

        now = bui.utc_now_cloud()

        val: bui.Lstr
        if now < self.time:
            color = (1.0, 1.0, 1.0, 0.3)
            val = bui.Lstr(
                resource='expiresInText',
                subs=[
                    (
                        '${T}',
                        bui.timestring(
                            (self.time - now).total_seconds(), centi=False
                        ),
                    ),
                ],
            )
        else:
            color = (1.0, 0.3, 0.3, 0.5)
            val = bui.Lstr(
                resource='expiredAgoText',
                subs=[
                    (
                        '${T}',
                        bui.timestring(
                            (now - self.time).total_seconds(), centi=False
                        ),
                    ),
                ],
            )
        bui.textwidget(edit=self._widget, text=val, color=color)

    @override
    def emit(self, subcontainer: bui.Widget, y: float) -> None:
        self._widget = bui.textwidget(
            parent=subcontainer,
            position=(
                self.sub_width * 0.5,
                y - self.spacing_top - self.text_height * 0.5,
            ),
            color=self.color,
            scale=self.text_scale,
            flatness=1.0,
            shadow=1.0,
            text='',
            maxwidth=self.sub_width * 0.7,
            size=(0, 0),
            h_align='center',
            v_align='center',
        )
        self._timer = bui.AppTimer(1.0, bui.WeakCall(self._update), repeat=True)
        self._update()


@dataclass
class _EntryDisplay:
    interaction_style: bacommon.bs.BasicClientUI.InteractionStyle
    button_label_positive: bacommon.bs.BasicClientUI.ButtonLabel
    button_label_negative: bacommon.bs.BasicClientUI.ButtonLabel
    sections: list[_Section]
    id: str
    total_height: float
    color: tuple[float, float, float]
    backing: bui.Widget | None = None
    button_positive: bui.Widget | None = None
    button_spinner_positive: bui.Widget | None = None
    button_negative: bui.Widget | None = None
    button_spinner_negative: bui.Widget | None = None
    processing_complete: bool = False


class InboxWindow(bui.MainWindow):
    """Popup window to show account messages."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale

        self._action_ui_pause: bui.RootUIUpdatePause | None = None

        self._entry_displays: list[_EntryDisplay] = []

        self._width = 900 if uiscale is bui.UIScale.SMALL else 500
        self._height = (
            600
            if uiscale is bui.UIScale.SMALL
            else 460 if uiscale is bui.UIScale.MEDIUM else 600
        )

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            1.9
            if uiscale is bui.UIScale.SMALL
            else 1.3 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        target_width = min(self._width - 60, screensize[0] / scale)
        target_height = min(self._height - 70, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and offset
        # by half the width/height of our target area.
        yoffs = 0.5 * self._height + 0.5 * target_height + 30.0

        scroll_width = target_width
        scroll_height = target_height - 31
        scroll_bottom = yoffs - 59 - scroll_height

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                toolbar_visibility=(
                    'menu_full' if uiscale is bui.UIScale.SMALL else 'menu_full'
                ),
                scale=scale,
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
            self._back_button = None
        else:
            self._back_button = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                position=(50, yoffs - 48),
                size=(60, 60),
                scale=0.6,
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
                yoffs - (45 if uiscale is bui.UIScale.SMALL else 30),
            ),
            size=(0, 0),
            h_align='center',
            v_align='center',
            scale=0.6 if uiscale is bui.UIScale.SMALL else 0.8,
            text=bui.Lstr(resource='inboxText'),
            maxwidth=200,
            color=bui.app.ui_v1.title_color,
        )

        # Shows 'loading', 'no messages', etc.
        self._infotext = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.5),
            maxwidth=self._width * 0.7,
            scale=0.5,
            flatness=1.0,
            color=(0.4, 0.4, 0.5),
            shadow=0.0,
            text='',
            size=(0, 0),
            h_align='center',
            v_align='center',
        )
        self._loading_spinner = bui.spinnerwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.5),
            style='bomb',
            size=48,
        )
        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            size=(scroll_width, scroll_height),
            position=(self._width * 0.5 - scroll_width * 0.5, scroll_bottom),
            capture_arrows=True,
            simple_culling_v=200,
            claims_left_right=True,
            claims_up_down=True,
            # Centering messages vertically looks natural with
            # fullscreen backing but weird in a window.
            center_small_content=uiscale is bui.UIScale.SMALL,
            center_small_content_horizontally=True,
            border_opacity=0.4,
        )
        bui.widget(edit=self._scrollwidget, autoselect=True)
        if uiscale is bui.UIScale.SMALL:
            bui.widget(
                edit=self._scrollwidget,
                left_widget=bui.get_special_widget('back_button'),
            )

        bui.containerwidget(
            edit=self._root_widget,
            cancel_button=self._back_button,
            single_depth=True,
        )

        # Kick off request.
        plus = bui.app.plus
        if plus is None or plus.accounts.primary is None:
            self._error(bui.Lstr(resource='notSignedInText'))
            return

        with plus.accounts.primary:
            plus.cloud.send_message_cb(
                bacommon.bs.InboxRequestMessage(),
                on_response=bui.WeakCall(self._on_inbox_request_response),
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

    def _error(self, errmsg: bui.Lstr | str) -> None:
        """Put ourself in a permanent error state."""
        bui.spinnerwidget(edit=self._loading_spinner, visible=False)
        bui.textwidget(
            edit=self._infotext,
            color=(1, 0, 0),
            text=errmsg,
        )

    def _on_entry_display_press(
        self,
        display_weak: weakref.ReferenceType[_EntryDisplay],
        action: bacommon.bs.ClientUIAction,
    ) -> None:
        display = display_weak()
        if display is None:
            return

        bui.getsound('click01').play()

        self._neuter_entry_display(display)

        # We currently only recognize basic entries and their possible
        # interaction types.
        if (
            display.interaction_style
            is bacommon.bs.BasicClientUI.InteractionStyle.UNKNOWN
        ):
            display.processing_complete = True
            self._close_soon_if_all_processed()
            return

        # Error if we're somehow signed out now.
        plus = bui.app.plus
        if plus is None or plus.accounts.primary is None:
            bui.screenmessage(
                bui.Lstr(resource='notSignedInText'), color=(1, 0, 0)
            )
            bui.getsound('error').play()
            return

        # Pause the root ui so stuff like token counts don't change
        # automatically, allowing the action to animate them.
        self._action_ui_pause = bui.RootUIUpdatePause()

        # Ask the master-server to run our action.
        with plus.accounts.primary:
            plus.cloud.send_message_cb(
                bacommon.bs.ClientUIActionMessage(display.id, action),
                on_response=bui.WeakCall(
                    self._on_client_ui_action_response,
                    display_weak,
                    action,
                ),
            )

        # Tweak the UI to show that things are in motion.
        button = (
            display.button_positive
            if action is bacommon.bs.ClientUIAction.BUTTON_PRESS_POSITIVE
            else display.button_negative
        )
        button_spinner = (
            display.button_spinner_positive
            if action is bacommon.bs.ClientUIAction.BUTTON_PRESS_POSITIVE
            else display.button_spinner_negative
        )
        if button is not None:
            bui.buttonwidget(edit=button, label='')
        if button_spinner is not None:
            bui.spinnerwidget(edit=button_spinner, visible=True)

    def _close_soon_if_all_processed(self) -> None:
        bui.apptimer(0.25, bui.WeakCall(self._close_if_all_processed))

    def _close_if_all_processed(self) -> None:
        if not all(m.processing_complete for m in self._entry_displays):
            return

        self.main_window_back()

    def _neuter_entry_display(self, entry: _EntryDisplay) -> None:
        errsound = bui.getsound('error')
        if entry.button_positive is not None:
            bui.buttonwidget(
                edit=entry.button_positive,
                color=(0.5, 0.5, 0.5),
                textcolor=(0.4, 0.4, 0.4),
                on_activate_call=errsound.play,
            )
        if entry.button_negative is not None:
            bui.buttonwidget(
                edit=entry.button_negative,
                color=(0.5, 0.5, 0.5),
                textcolor=(0.4, 0.4, 0.4),
                on_activate_call=errsound.play,
            )
        if entry.backing is not None:
            bui.imagewidget(edit=entry.backing, color=(0.4, 0.4, 0.4))

    def _on_client_ui_action_response(
        self,
        display_weak: weakref.ReferenceType[_EntryDisplay],
        action: bacommon.bs.ClientUIAction,
        response: bacommon.bs.ClientUIActionResponse | Exception,
    ) -> None:
        # pylint: disable=too-many-branches

        # Let the UI auto-update again after any animations we may apply
        # here.
        self._action_ui_pause = None

        display = display_weak()
        if display is None:
            return

        assert not display.processing_complete
        display.processing_complete = True
        self._close_soon_if_all_processed()

        # No-op if our UI is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        # Tweak the button to show results.
        button = (
            display.button_positive
            if action is bacommon.bs.ClientUIAction.BUTTON_PRESS_POSITIVE
            else display.button_negative
        )
        button_spinner = (
            display.button_spinner_positive
            if action is bacommon.bs.ClientUIAction.BUTTON_PRESS_POSITIVE
            else display.button_spinner_negative
        )
        # Always hide spinner at this point.
        if button_spinner is not None:
            bui.spinnerwidget(edit=button_spinner, visible=False)

        # See if we should show an error message.
        if isinstance(response, Exception):
            if isinstance(response, CommunicationError):
                error_message = bui.Lstr(
                    resource='internal.unavailableNoConnectionText'
                )
            else:
                error_message = bui.Lstr(resource='errorText')
        elif response.error_type is not None:
            # If error_type is set, error should be also.
            assert response.error_message is not None
            error_message = bui.Lstr(
                translate=('serverResponses', response.error_message)
            )
        else:
            error_message = None

        # Show error message if so.
        if error_message is not None:
            bui.screenmessage(error_message, color=(1, 0, 0))
            bui.getsound('error').play()
            if button is not None:
                bui.buttonwidget(
                    edit=button, label=bui.Lstr(resource='errorText')
                )
            return

        # Success!
        assert not isinstance(response, Exception)

        # Run any bundled effects.
        assert bui.app.classic is not None
        bui.app.classic.run_bs_client_effects(response.effects)

        # Whee; no error. Mark as done.
        if button is not None:
            # If we have full unicode, just show a checkmark in all cases.
            label: str | bui.Lstr
            if bui.supports_unicode_display():
                label = '✓'
            else:
                label = bui.Lstr(resource='doneText')
            bui.buttonwidget(edit=button, label=label)

    def _on_inbox_request_response(
        self, response: bacommon.bs.InboxRequestResponse | Exception
    ) -> None:
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches

        # No-op if our UI is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        errmsg: str | bui.Lstr
        if isinstance(response, Exception):
            errmsg = bui.Lstr(resource='internal.unavailableNoConnectionText')
            is_error = True
        else:
            is_error = response.error is not None
            errmsg = (
                ''
                if response.error is None
                else bui.Lstr(translate=('serverResponses', response.error))
            )

        if is_error:
            self._error(errmsg)
            return

        assert isinstance(response, bacommon.bs.InboxRequestResponse)

        # If we got no messages, don't touch anything. This keeps
        # keyboard control working in the empty case.
        if not response.wrappers:
            bui.spinnerwidget(edit=self._loading_spinner, visible=False)
            bui.textwidget(
                edit=self._infotext,
                color=(0.4, 0.4, 0.5),
                text=bui.Lstr(resource='noMessagesText'),
            )
            return

        bui.scrollwidget(edit=self._scrollwidget, highlight=False)

        bui.spinnerwidget(edit=self._loading_spinner, visible=False)
        bui.textwidget(edit=self._infotext, text='')

        uiscale = bui.app.ui_v1.uiscale

        margin_top = 0.0 if uiscale is bui.UIScale.SMALL else 10.0
        margin_v = 0.0 if uiscale is bui.UIScale.SMALL else 5.0

        # Need this to avoid the dock blocking access to buttons on our
        # bottom message.
        margin_bottom = 60.0 if uiscale is bui.UIScale.SMALL else 10.0

        # Even though our window size varies with uiscale, we want
        # notifications to target a fixed width.
        sub_width = 400.0
        sub_height = margin_top

        # Construct entries for everything we'll display.
        for i, wrapper in enumerate(response.wrappers):

            # We need to flatten text here so we can measure it.
            # textfin: str
            color: tuple[float, float, float]

            interaction_style: bacommon.bs.BasicClientUI.InteractionStyle
            button_label_positive: bacommon.bs.BasicClientUI.ButtonLabel
            button_label_negative: bacommon.bs.BasicClientUI.ButtonLabel

            sections: list[_Section] = []
            total_height = 80.0

            # Display only entries where we recognize all style/label
            # values and ui component types.
            if (
                isinstance(wrapper.ui, bacommon.bs.BasicClientUI)
                and not wrapper.ui.contains_unknown_elements()
            ):
                color = (0.55, 0.5, 0.7)
                interaction_style = wrapper.ui.interaction_style
                button_label_positive = wrapper.ui.button_label_positive
                button_label_negative = wrapper.ui.button_label_negative

                idcls = bacommon.bs.BasicClientUIComponentTypeID
                for component in wrapper.ui.components:
                    ctypeid = component.get_type_id()
                    section: _Section

                    if ctypeid is idcls.TEXT:
                        assert isinstance(
                            component, bacommon.bs.BasicClientUIComponentText
                        )
                        section = _TextSection(
                            sub_width=sub_width,
                            text=bui.Lstr(
                                translate=('serverResponses', component.text),
                                subs=pairs_from_flat(component.subs),
                            ),
                            color=component.color,
                            scale=component.scale,
                            spacing_top=component.spacing_top,
                            spacing_bottom=component.spacing_bottom,
                        )
                        total_height += section.get_height()
                        sections.append(section)

                    elif ctypeid is idcls.LINK:
                        assert isinstance(
                            component, bacommon.bs.BasicClientUIComponentLink
                        )

                        def _do_open_url(url: str, sec: _ButtonSection) -> None:
                            del sec  # Unused.
                            bui.open_url(url)

                        section = _ButtonSection(
                            sub_width=sub_width,
                            label=bui.Lstr(
                                translate=('serverResponses', component.label),
                                subs=pairs_from_flat(component.subs),
                            ),
                            color=color,
                            call=partial(_do_open_url, component.url),
                            label_color=(0.5, 0.7, 0.6),
                            spacing_top=component.spacing_top,
                            spacing_bottom=component.spacing_bottom,
                        )
                        total_height += section.get_height()
                        sections.append(section)

                    elif ctypeid is idcls.DISPLAY_ITEMS:
                        assert isinstance(
                            component,
                            bacommon.bs.BasicClientUIDisplayItems,
                        )
                        section = _DisplayItemsSection(
                            sub_width=sub_width,
                            items=component.items,
                            width=component.width,
                            spacing_top=component.spacing_top,
                            spacing_bottom=component.spacing_bottom,
                        )
                        total_height += section.get_height()
                        sections.append(section)

                    elif ctypeid is idcls.BS_CLASSIC_TOURNEY_RESULT:
                        from bascenev1 import get_trophy_string

                        assert isinstance(
                            component,
                            bacommon.bs.BasicClientUIBsClassicTourneyResult,
                        )
                        campaignname, levelname = component.game.split(':')
                        assert bui.app.classic is not None
                        campaign = bui.app.classic.getcampaign(campaignname)

                        tourney_name = bui.Lstr(
                            value='${A} ${B}',
                            subs=[
                                (
                                    '${A}',
                                    campaign.getlevel(levelname).displayname,
                                ),
                                (
                                    '${B}',
                                    bui.Lstr(
                                        resource='playerCountAbbreviatedText',
                                        subs=[
                                            ('${COUNT}', str(component.players))
                                        ],
                                    ),
                                ),
                            ],
                        )

                        if component.trophy is not None:
                            trophy_prefix = (
                                get_trophy_string(component.trophy) + ' '
                            )
                        else:
                            trophy_prefix = ''

                        section = _TextSection(
                            sub_width=sub_width,
                            text=bui.Lstr(
                                value='${P}${V}',
                                subs=[
                                    ('${P}', trophy_prefix),
                                    (
                                        '${V}',
                                        bui.Lstr(
                                            translate=(
                                                'serverResponses',
                                                'You placed #${RANK}'
                                                ' in a tournament!',
                                            ),
                                            subs=[
                                                ('${RANK}', str(component.rank))
                                            ],
                                        ),
                                    ),
                                ],
                            ),
                            color=(1.0, 1.0, 1.0, 1.0),
                            scale=0.6,
                        )
                        total_height += section.get_height()
                        sections.append(section)

                        section = _TextSection(
                            sub_width=sub_width,
                            text=tourney_name,
                            spacing_top=5,
                            color=(0.7, 0.7, 1.0, 1.0),
                            scale=0.7,
                        )
                        total_height += section.get_height()
                        sections.append(section)

                        def _do_tourney_scores(
                            tournament_id: str, sec: _ButtonSection
                        ) -> None:
                            from bauiv1lib.tournamentscores import (
                                TournamentScoresWindow,
                            )

                            assert sec.button is not None
                            _ = (
                                TournamentScoresWindow(
                                    tournament_id=tournament_id,
                                    position=(
                                        sec.button
                                    ).get_screen_space_center(),
                                ),
                            )

                        section = _ButtonSection(
                            sub_width=sub_width,
                            label=bui.Lstr(
                                resource='tournamentFinalStandingsText'
                            ),
                            color=color,
                            call=partial(
                                _do_tourney_scores, component.tournament_id
                            ),
                            label_color=(0.5, 0.7, 0.6),
                            spacing_top=7.0,
                            spacing_bottom=0.0 if component.prizes else 7.0,
                        )
                        total_height += section.get_height()
                        sections.append(section)

                        if component.prizes:
                            section = _TextSection(
                                sub_width=sub_width,
                                text=bui.Lstr(resource='yourPrizeText'),
                                spacing_top=6,
                                color=(1.0, 1.0, 1.0, 0.4),
                                scale=0.35,
                            )
                            total_height += section.get_height()
                            sections.append(section)

                            section = _DisplayItemsSection(
                                sub_width=sub_width,
                                items=component.prizes,
                                width=70.0,
                                spacing_top=0.0,
                                spacing_bottom=0.0,
                            )
                            total_height += section.get_height()
                            sections.append(section)

                    elif ctypeid is idcls.EXPIRE_TIME:
                        assert isinstance(
                            component, bacommon.bs.BasicClientUIExpireTime
                        )
                        section = _ExpireTimeSection(
                            sub_width=sub_width,
                            time=component.time,
                            spacing_top=component.spacing_top,
                            spacing_bottom=component.spacing_bottom,
                        )
                        total_height += section.get_height()
                        sections.append(section)

                    elif ctypeid is idcls.UNKNOWN:
                        raise RuntimeError('Should not get here.')

                    else:
                        # Make sure we handle all types.
                        assert_never(ctypeid)
            else:

                # Display anything with unknown components as an
                # 'upgrade your app to see this' message.
                color = (0.6, 0.6, 0.6)
                interaction_style = (
                    bacommon.bs.BasicClientUI.InteractionStyle.UNKNOWN
                )
                button_label_positive = bacommon.bs.BasicClientUI.ButtonLabel.OK
                button_label_negative = (
                    bacommon.bs.BasicClientUI.ButtonLabel.CANCEL
                )

                section = _TextSection(
                    sub_width=sub_width,
                    text=bui.Lstr(
                        value='You must update the app to view this.'
                    ),
                )
                total_height += section.get_height()
                sections.append(section)

            self._entry_displays.append(
                _EntryDisplay(
                    interaction_style=interaction_style,
                    button_label_positive=button_label_positive,
                    button_label_negative=button_label_negative,
                    id=wrapper.id,
                    sections=sections,
                    total_height=total_height,
                    color=color,
                )
            )
            sub_height += margin_v + total_height

        sub_height += margin_bottom

        subcontainer = bui.containerwidget(
            id='inboxsub',
            parent=self._scrollwidget,
            size=(sub_width, sub_height),
            background=False,
            single_depth=True,
            claims_left_right=True,
            claims_up_down=True,
        )

        backing_tex = bui.gettexture('buttonSquareWide')

        assert bui.app.classic is not None

        buttonrows: list[list[bui.Widget]] = []
        y = sub_height - margin_top
        for i, _wrapper in enumerate(response.wrappers):
            entry_display = self._entry_displays[i]
            entry_display_weak = weakref.ref(entry_display)
            bwidth = 140
            bheight = 40

            ysection = y - 23.0

            # Backing.
            entry_display.backing = img = bui.imagewidget(
                parent=subcontainer,
                position=(
                    -0.022 * sub_width,
                    y - entry_display.total_height * 1.09,
                ),
                texture=backing_tex,
                size=(sub_width * 1.07, entry_display.total_height * 1.15),
                color=entry_display.color,
                opacity=0.9,
            )
            bui.widget(edit=img, depth_range=(0, 0.1))

            # Section contents.
            for sec in entry_display.sections:
                sec.emit(subcontainer, ysection)
                # Wire up any widgets created by this section.
                sec_button_row = sec.get_button_row()
                if sec_button_row:
                    buttonrows.append(sec_button_row)
                ysection -= sec.get_height()

            buttonrow: list[bui.Widget] = []
            have_negative_button = (
                entry_display.interaction_style
                is (
                    bacommon.bs.BasicClientUI
                ).InteractionStyle.BUTTON_POSITIVE_NEGATIVE
            )

            bpos = (
                (
                    (sub_width - bwidth - 25)
                    if have_negative_button
                    else ((sub_width - bwidth) * 0.5)
                ),
                y - entry_display.total_height + 15.0,
            )
            entry_display.button_positive = btn = bui.buttonwidget(
                parent=subcontainer,
                position=bpos,
                autoselect=True,
                size=(bwidth, bheight),
                label=bui.app.classic.basic_client_ui_button_label_str(
                    entry_display.button_label_positive
                ),
                color=entry_display.color,
                textcolor=(0, 1, 0),
                on_activate_call=bui.WeakCall(
                    self._on_entry_display_press,
                    entry_display_weak,
                    bacommon.bs.ClientUIAction.BUTTON_PRESS_POSITIVE,
                ),
                enable_sound=False,
            )
            bui.widget(edit=btn, depth_range=(0.1, 1.0))
            buttonrow.append(btn)
            spinner = entry_display.button_spinner_positive = bui.spinnerwidget(
                parent=subcontainer,
                position=(
                    bpos[0] + 0.5 * bwidth,
                    bpos[1] + 0.5 * bheight,
                ),
                visible=False,
            )
            bui.widget(edit=spinner, depth_range=(0.1, 1.0))

            if have_negative_button:
                bpos = (25, y - entry_display.total_height + 15.0)
                entry_display.button_negative = btn2 = bui.buttonwidget(
                    parent=subcontainer,
                    position=bpos,
                    autoselect=True,
                    size=(bwidth, bheight),
                    label=bui.app.classic.basic_client_ui_button_label_str(
                        entry_display.button_label_negative
                    ),
                    color=(0.85, 0.5, 0.7),
                    textcolor=(1, 0.4, 0.4),
                    on_activate_call=bui.WeakCall(
                        self._on_entry_display_press,
                        entry_display_weak,
                        (bacommon.bs.ClientUIAction).BUTTON_PRESS_NEGATIVE,
                    ),
                    enable_sound=False,
                )
                bui.widget(edit=btn2, depth_range=(0.1, 1.0))
                buttonrow.append(btn2)
                spinner = entry_display.button_spinner_negative = (
                    bui.spinnerwidget(
                        parent=subcontainer,
                        position=(
                            bpos[0] + 0.5 * bwidth,
                            bpos[1] + 0.5 * bheight,
                        ),
                        visible=False,
                    )
                )
                bui.widget(edit=spinner, depth_range=(0.1, 1.0))

            buttonrows.append(buttonrow)

            y -= margin_v + entry_display.total_height

        uiscale = bui.app.ui_v1.uiscale
        above_widget = (
            bui.get_special_widget('back_button')
            if uiscale is bui.UIScale.SMALL
            else self._back_button
        )
        assert above_widget is not None
        for i, buttons in enumerate(buttonrows):
            if i < len(buttonrows) - 1:
                below_widget = buttonrows[i + 1][0]
            else:
                below_widget = None

            assert buttons  # We should never have an empty row.
            for j, button in enumerate(buttons):
                bui.widget(
                    edit=button,
                    up_widget=above_widget,
                    down_widget=below_widget,
                    right_widget=buttons[max(j - 1, 0)],
                    left_widget=buttons[min(j + 1, len(buttons) - 1)],
                )

            above_widget = buttons[0]


def _get_bs_classic_tourney_results_sections() -> list[_Section]:
    return []
