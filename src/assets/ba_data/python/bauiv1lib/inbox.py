# Released under the MIT License. See LICENSE for details.
#
"""Provides a popup window to view achievements."""

from __future__ import annotations

import weakref
from dataclasses import dataclass
from typing import override, assert_never

from efro.error import CommunicationError
import bacommon.bs
import bauiv1 as bui


class _Section:
    def get_height(self) -> float:
        """Return section height."""
        raise NotImplementedError()

    def draw(self, subcontainer: bui.Widget, y: float) -> None:
        """Draw the section."""


class _TextSection(_Section):

    def __init__(
        self,
        sub_width: float,
        text: str,
        *,
        subs: list[str],
        spacing_top: float = 0.0,
        spacing_bottom: float = 0.0,
        scale: float = 0.6,
        color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
    ) -> None:
        self.sub_width = sub_width
        self.spacing_top = spacing_top
        self.spacing_bottom = spacing_bottom
        self.color = color

        self.textfin = bui.Lstr(translate=('serverResponses', text)).evaluate()
        assert len(subs) % 2 == 0  # Should always be even.
        for j in range(0, len(subs) - 1, 2):
            self.textfin = self.textfin.replace(subs[j], subs[j + 1])

        # Calc scale to fit width and then see what height we need at
        # that scale.
        t_width = max(
            10.0,
            bui.get_string_width(self.textfin, suppress_warning=True) * scale,
        )
        self.text_scale = scale * min(1.0, (sub_width * 0.9) / t_width)

        self.text_height = (
            0.0
            if not self.textfin
            else bui.get_string_height(self.textfin, suppress_warning=True)
        ) * self.text_scale

        self.full_height = self.text_height + spacing_top + spacing_bottom

    @override
    def get_height(self) -> float:
        return self.full_height

    @override
    def draw(self, subcontainer: bui.Widget, y: float) -> None:
        bui.textwidget(
            parent=subcontainer,
            position=(
                self.sub_width * 0.5,
                y - self.spacing_top - self.text_height * 0.5,
                # y - self.height * 0.5 - 23.0,
            ),
            color=self.color,
            scale=self.text_scale,
            flatness=1.0,
            shadow=0.0,
            text=self.textfin,
            size=(0, 0),
            h_align='center',
            v_align='center',
        )


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
    # message_text: bui.Widget | None = None
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

        self._entry_displays: list[_EntryDisplay] = []

        self._width = 800 if uiscale is bui.UIScale.SMALL else 500
        self._height = (
            455
            if uiscale is bui.UIScale.SMALL
            else 370 if uiscale is bui.UIScale.MEDIUM else 450
        )
        yoffs = -42 if uiscale is bui.UIScale.SMALL else 0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                toolbar_visibility=(
                    'menu_full' if uiscale is bui.UIScale.SMALL else 'menu_full'
                ),
                scale=(
                    1.7
                    if uiscale is bui.UIScale.SMALL
                    else 1.5 if uiscale is bui.UIScale.MEDIUM else 1.15
                ),
                stack_offset=(
                    (0, 0)
                    if uiscale is bui.UIScale.SMALL
                    else (0, 0) if uiscale is bui.UIScale.MEDIUM else (0, 0)
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
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
                position=(50, self._height - 38 + yoffs),
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
                self._height
                - (24 if uiscale is bui.UIScale.SMALL else 20)
                + yoffs,
            ),
            size=(0, 0),
            h_align='center',
            v_align='center',
            scale=0.6,
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
        )
        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            size=(
                self._width - 60,
                self._height - (170 if uiscale is bui.UIScale.SMALL else 70),
            ),
            position=(
                30,
                (133 if uiscale is bui.UIScale.SMALL else 30) + yoffs,
            ),
            capture_arrows=True,
            simple_culling_v=200,
            claims_left_right=True,
            claims_up_down=True,
            center_small_content_horizontally=True,
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

        bui.spinnerwidget(edit=self._loading_spinner, visible=False)
        bui.textwidget(edit=self._infotext, text='')

        # Even though our window size varies with uiscale, we want
        # notifications to target a fixed width.
        sub_width = 400.0
        sub_height = 0.0

        # Construct entries for everything we'll display.
        for i, wrapper in enumerate(response.wrappers):

            # We need to flatten text here so we can measure it.
            # textfin: str
            color: tuple[float, float, float]

            interaction_style: bacommon.bs.BasicClientUI.InteractionStyle
            button_label_positive: bacommon.bs.BasicClientUI.ButtonLabel
            button_label_negative: bacommon.bs.BasicClientUI.ButtonLabel

            sections: list[_Section] = []
            total_height = 90.0

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
                    if ctypeid is idcls.TEXT:
                        assert isinstance(
                            component, bacommon.bs.BasicClientUIComponentText
                        )
                        section = _TextSection(
                            sub_width=sub_width,
                            text=component.text,
                            subs=component.subs,
                            color=component.color,
                            scale=component.scale,
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
                    text='You must update the app to view this.',
                    subs=[],
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
            sub_height += total_height

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
        y = sub_height
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
                sec.draw(subcontainer, ysection)
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

            y -= entry_display.total_height

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
                    down_widget=(
                        button if below_widget is None else below_widget
                    ),
                    right_widget=buttons[max(j - 1, 0)],
                    left_widget=buttons[min(j + 1, len(buttons) - 1)],
                )

            above_widget = buttons[0]
