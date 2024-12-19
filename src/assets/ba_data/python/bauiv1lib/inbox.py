# Released under the MIT License. See LICENSE for details.
#
"""Provides a popup window to view achievements."""

from __future__ import annotations

import weakref
from dataclasses import dataclass
from typing import override

from efro.error import CommunicationError
import bacommon.cloud
import bauiv1 as bui

# Messages with format versions higher than this will show up as
# 'app needs to be updated to view this'
SUPPORTED_INBOX_MESSAGE_FORMAT_VERSION = 1


@dataclass
class _MessageEntry:
    type: bacommon.cloud.BSInboxEntryType
    id: str
    height: float
    text_height: float
    scale: float
    text: str
    color: tuple[float, float, float]
    backing: bui.Widget | None = None
    button_positive: bui.Widget | None = None
    button_negative: bui.Widget | None = None
    message_text: bui.Widget | None = None
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

        self._message_entries: list[_MessageEntry] = []

        self._width = 600 if uiscale is bui.UIScale.SMALL else 450
        self._height = (
            380
            if uiscale is bui.UIScale.SMALL
            else 370 if uiscale is bui.UIScale.MEDIUM else 450
        )
        yoffs = -45 if uiscale is bui.UIScale.SMALL else 0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                toolbar_visibility=(
                    'menu_full' if uiscale is bui.UIScale.SMALL else 'menu_full'
                ),
                scale=(
                    2.3
                    if uiscale is bui.UIScale.SMALL
                    else 1.65 if uiscale is bui.UIScale.MEDIUM else 1.23
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
                - (27 if uiscale is bui.UIScale.SMALL else 20)
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
            text=bui.Lstr(resource='loadingText'),
            size=(0, 0),
            h_align='center',
            v_align='center',
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
                bacommon.cloud.BSInboxRequestMessage(),
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
        bui.textwidget(
            edit=self._infotext,
            color=(1, 0, 0),
            text=errmsg,
        )

    def _on_message_entry_press(
        self,
        entry_weak: weakref.ReferenceType[_MessageEntry],
        process_type: bacommon.cloud.BSInboxEntryProcessType,
    ) -> None:
        entry = entry_weak()
        if entry is None:
            return

        self._neuter_message_entry(entry)

        # We don't do anything for invalid messages.
        if entry.type is bacommon.cloud.BSInboxEntryType.UNKNOWN:
            entry.processing_complete = True
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

        # Message the master-server to process the entry.
        with plus.accounts.primary:
            plus.cloud.send_message_cb(
                bacommon.cloud.BSInboxEntryProcessMessage(
                    entry.id, process_type
                ),
                on_response=bui.WeakCall(
                    self._on_inbox_entry_process_response,
                    entry_weak,
                    process_type,
                ),
            )

        # Tweak the button to show this is in progress.
        button = (
            entry.button_positive
            if process_type is bacommon.cloud.BSInboxEntryProcessType.POSITIVE
            else entry.button_negative
        )
        if button is not None:
            bui.buttonwidget(edit=button, label='...')

    def _close_soon_if_all_processed(self) -> None:
        bui.apptimer(0.25, bui.WeakCall(self._close_if_all_processed))

    def _close_if_all_processed(self) -> None:
        if not all(m.processing_complete for m in self._message_entries):
            return

        self.main_window_back()

    def _neuter_message_entry(self, entry: _MessageEntry) -> None:
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
        if entry.message_text is not None:
            bui.textwidget(edit=entry.message_text, color=(0.5, 0.5, 0.5, 0.5))

    def _on_inbox_entry_process_response(
        self,
        entry_weak: weakref.ReferenceType[_MessageEntry],
        process_type: bacommon.cloud.BSInboxEntryProcessType,
        response: bacommon.cloud.BSInboxEntryProcessResponse | Exception,
    ) -> None:
        # pylint: disable=too-many-branches
        entry = entry_weak()
        if entry is None:
            return

        assert not entry.processing_complete
        entry.processing_complete = True
        self._close_soon_if_all_processed()

        # No-op if our UI is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        # Tweak the button to show results.
        button = (
            entry.button_positive
            if process_type is bacommon.cloud.BSInboxEntryProcessType.POSITIVE
            else entry.button_negative
        )

        # See if we should show an error message.
        if isinstance(response, Exception):
            if isinstance(response, CommunicationError):
                error_message = bui.Lstr(
                    resource='internal.unavailableNoConnectionText'
                )
            else:
                error_message = bui.Lstr(resource='errorText')
        elif response.error is not None:
            error_message = bui.Lstr(
                translate=('serverResponses', response.error)
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

        # Whee; no error. Mark as done.
        if button is not None:
            # If we have full unicode, just show a checkmark in all cases.
            label: str | bui.Lstr
            if bui.supports_unicode_display():
                label = '✓'
            else:
                # For positive claim buttons, say 'success'.
                # Otherwise default to 'done.'
                if (
                    entry.type
                    in {
                        bacommon.cloud.BSInboxEntryType.CLAIM,
                        bacommon.cloud.BSInboxEntryType.CLAIM_DISCARD,
                    }
                    and process_type
                    is bacommon.cloud.BSInboxEntryProcessType.POSITIVE
                ):
                    label = bui.Lstr(resource='successText')
                else:
                    label = bui.Lstr(resource='doneText')
            bui.buttonwidget(edit=button, label=label)

    def _on_inbox_request_response(
        self, response: bacommon.cloud.BSInboxRequestResponse | Exception
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

        assert isinstance(response, bacommon.cloud.BSInboxRequestResponse)

        # If we got no messages, don't touch anything. This keeps
        # keyboard control working in the empty case.
        if not response.entries:
            bui.textwidget(
                edit=self._infotext,
                color=(0.4, 0.4, 0.5),
                text=bui.Lstr(resource='noMessagesText'),
            )
            return

        bui.textwidget(edit=self._infotext, text='')

        sub_width = self._width - 90
        sub_height = 0.0

        # Run the math on row heights/etc.
        for i, entry in enumerate(response.entries):
            # We need to flatten text here so we can measure it.
            textfin: str
            color: tuple[float, float, float]

            # Messages with either newer formatting or unrecognized
            # types show up as 'upgrade your app to see this'.
            if (
                entry.format_version > SUPPORTED_INBOX_MESSAGE_FORMAT_VERSION
                or entry.type is bacommon.cloud.BSInboxEntryType.UNKNOWN
            ):
                textfin = bui.Lstr(
                    translate=(
                        'serverResponses',
                        'You must update the app to view this.',
                    )
                ).evaluate()
                color = (0.6, 0.6, 0.6)
            else:
                # Translate raw response and apply any replacements.
                textfin = bui.Lstr(
                    translate=('serverResponses', entry.message)
                ).evaluate()
                assert len(entry.subs) % 2 == 0  # Should always be even.
                for j in range(0, len(entry.subs) - 1, 2):
                    textfin = textfin.replace(entry.subs[j], entry.subs[j + 1])
                color = (0.55, 0.5, 0.7)

            # Calc scale to fit width and then see what height we need
            # at that scale.
            t_width = max(
                10.0, bui.get_string_width(textfin, suppress_warning=True)
            )
            scale = min(0.6, (sub_width * 0.9) / t_width)
            t_height = (
                max(10.0, bui.get_string_height(textfin, suppress_warning=True))
                * scale
            )
            entry_height = 90.0 + t_height
            self._message_entries.append(
                _MessageEntry(
                    type=entry.type,
                    id=entry.id,
                    height=entry_height,
                    text_height=t_height,
                    scale=scale,
                    text=textfin,
                    color=color,
                )
            )
            sub_height += entry_height

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

        buttonrows: list[list[bui.Widget]] = []
        y = sub_height
        for i, _entry in enumerate(response.entries):
            message_entry = self._message_entries[i]
            message_entry_weak = weakref.ref(message_entry)
            bwidth = 140
            bheight = 40

            # Backing.
            message_entry.backing = img = bui.imagewidget(
                parent=subcontainer,
                position=(-0.022 * sub_width, y - message_entry.height * 1.09),
                texture=backing_tex,
                size=(sub_width * 1.07, message_entry.height * 1.15),
                color=message_entry.color,
                opacity=0.9,
            )
            bui.widget(edit=img, depth_range=(0, 0.1))

            buttonrow: list[bui.Widget] = []
            have_negative_button = (
                message_entry.type
                is bacommon.cloud.BSInboxEntryType.CLAIM_DISCARD
            )

            message_entry.button_positive = btn = bui.buttonwidget(
                parent=subcontainer,
                position=(
                    (
                        (sub_width - bwidth - 25)
                        if have_negative_button
                        else ((sub_width - bwidth) * 0.5)
                    ),
                    y - message_entry.height + 15.0,
                ),
                size=(bwidth, bheight),
                label=bui.Lstr(
                    resource=(
                        'claimText'
                        if message_entry.type
                        in {
                            bacommon.cloud.BSInboxEntryType.CLAIM,
                            bacommon.cloud.BSInboxEntryType.CLAIM_DISCARD,
                        }
                        else 'okText'
                    )
                ),
                color=message_entry.color,
                textcolor=(0, 1, 0),
                on_activate_call=bui.WeakCall(
                    self._on_message_entry_press,
                    message_entry_weak,
                    bacommon.cloud.BSInboxEntryProcessType.POSITIVE,
                ),
            )
            bui.widget(edit=btn, depth_range=(0.1, 1.0))
            buttonrow.append(btn)

            if have_negative_button:
                message_entry.button_negative = btn2 = bui.buttonwidget(
                    parent=subcontainer,
                    position=(25, y - message_entry.height + 15.0),
                    size=(bwidth, bheight),
                    label=bui.Lstr(resource='discardText'),
                    color=(0.85, 0.5, 0.7),
                    textcolor=(1, 0.4, 0.4),
                    on_activate_call=bui.WeakCall(
                        self._on_message_entry_press,
                        message_entry_weak,
                        bacommon.cloud.BSInboxEntryProcessType.NEGATIVE,
                    ),
                )
                bui.widget(edit=btn2, depth_range=(0.1, 1.0))
                buttonrow.append(btn2)

            buttonrows.append(buttonrow)

            message_entry.message_text = bui.textwidget(
                parent=subcontainer,
                position=(
                    sub_width * 0.5,
                    y - message_entry.text_height * 0.5 - 23.0,
                ),
                scale=message_entry.scale,
                flatness=1.0,
                shadow=0.0,
                text=message_entry.text,
                size=(0, 0),
                h_align='center',
                v_align='center',
            )
            y -= message_entry.height

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
