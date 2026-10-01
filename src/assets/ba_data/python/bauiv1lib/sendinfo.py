# Released under the MIT License. See LICENSE for details.
#
"""UI for sending info (codes and such) to the developer.

The send-info page (Advanced settings' 'Send Info') is a client-local
doc-ui domain: whatever gets typed goes to the master server, which
handles promo codes itself and passes others (old-style codes, share
codes) along to the v1 server. The legacy modal window here is only a
base for the playlist-import window.
"""

import time
import logging
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs
import bacommon.docui.v2 as dui2
from bacommon.docui.presets import SectionButtonSize, section_button
from bacommon.docui.routes import (
    DocUIRoute,
    DocUILocalActionBase,
    DocUIState,
    family_members,
)
import bauiv1 as bui
from bauiv1 import _commonassets, _classicassets
from bauiv1 import _builtinassets
from bauiv1lib.docui import TypedDocUIController

if TYPE_CHECKING:
    from typing import Any, Literal

    from bacommon.docui import DocUIResponse

    from bauiv1lib.docui import DocUILocalAction


class SendInfoRoute(DocUIRoute):
    """Family class for the send-info routes."""

    @override
    @classmethod
    def get_route_types(cls) -> tuple[type[DocUIRoute], ...]:
        return family_members(AnySendInfoRoute)

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        # A text field and a button.
        return dui2.WindowLayout.SMALL


@ioprepped
@dataclass
class Root(SendInfoRoute, path='/'):
    """The send-info page."""


AnySendInfoRoute = Root


@ioprepped
@dataclass
class SendInfoState(DocUIState, state_id='sendinfo'):
    """What's been typed."""

    description: Annotated[str, IOAttrs('d')] = ''


class SendInfoLocalAction(DocUILocalActionBase):
    """Family class for the send-info local-actions."""

    @override
    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        return family_members(AnySendInfoLocalAction)


@ioprepped
@dataclass
class Submit(SendInfoLocalAction, name='submit'):
    """Send what's been typed, going back as it goes out."""


AnySendInfoLocalAction = Submit


class SendInfoController(
    TypedDocUIController[AnySendInfoRoute, AnySendInfoLocalAction]
):
    """Doc-ui controller for the send-info page."""

    @override
    @classmethod
    def get_route_type(cls) -> type[SendInfoRoute]:
        return SendInfoRoute

    @override
    @classmethod
    def get_local_action_type(cls) -> type[SendInfoLocalAction]:
        return SendInfoLocalAction

    @override
    def get_window_toolbar_visibility(
        self,
    ) -> Literal['menu_full', 'menu_minimal']:
        # As the other settings windows: minimal mid-game.
        return 'menu_full' if bui.in_main_menu() else 'menu_minimal'

    @override
    def fulfill_route(self, route: AnySendInfoRoute) -> DocUIResponse:
        match route:
            case Root():
                return _page()
            case _:
                assert_never(route)

    @override
    def run_local_action(
        self, action: AnySendInfoLocalAction, context: DocUILocalAction
    ) -> None:
        match action:
            case Submit():
                _submit(context)
            case _:
                assert_never(action)


def _page() -> dui2.Response:
    """Build the page (called in a background thread)."""
    sistrs = _classicassets.strings.send_info
    submit = Submit().local()
    field = replace(
        SendInfoState.text_input_row(
            lambda s: s.description,
            label=_commonassets.strings.values.description.spec,
            description=_commonassets.strings.values.description.spec,
            max_chars=64,
            # Typing and hitting return sends, as the button does.
            on_submit=submit,
        ),
        # What this is all about, above the field.
        header_height=80.0,
        header_decorations_center=[
            dui2.Text(
                text=sistrs.send_info_description.spec,
                position=(0, 0),
                size=(560, 60),
                scale=0.8,
                color=(0.7, 0.7, 0.7, 1.0),
            )
        ],
    )
    rows: list[dui2.Row] = [field]
    # A lone, deliberately narrow button centered under the field (a
    # fill row would stretch it across the column).
    rows.append(
        dui2.ButtonRow(
            center_content=True,
            spacing_top=10.0,
            padding_top=8.0,
            padding_bottom=6.0,
            buttons=[
                replace(
                    section_button(
                        _commonassets.strings.actions.submit.spec,
                        submit,
                        size=SectionButtonSize.MEDIUM,
                    ),
                    # (A controller's start button presses it.)
                    default=True,
                )
            ],
        )
    )
    return dui2.Response(
        page=dui2.Page(
            title=_classicassets.strings.settings.advanced.send_info.spec,
            rows=rows,
            state=SendInfoState().encode(),
            center_vertically=True,
        )
    )


def _submit(context: DocUILocalAction) -> None:
    state = context.state(SendInfoState)
    if state is None:
        return
    window = context.window

    # No-op if we're not in control.
    if not window.main_window_has_control():
        return
    window.main_window_back()
    bui.app.create_async_task(_send_info(state.description))


class SendInfoWindowLegacyModal(bui.Window):
    """Window for sending info to the developer."""

    def __init__(
        self,
        transition: str | None = 'in_scale',
        origin_widget: bui.Widget | None = None,
    ):

        # Need to wrangle our own transition-out in modal mode.
        if origin_widget is not None:
            self._transition_out = 'out_scale'
        else:
            self._transition_out = 'out_right'

        uiscale = bui.app.ui_v1.uiscale

        width = 450
        height = 200

        self._r = 'promoCodeWindow'

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            2.0
            if uiscale is bui.UIScale.SMALL
            else 1.5 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        # target_width = min(width - 80, screensize[0] / scale)
        target_height = min(height - 80, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * height + 0.5 * target_height + 20.0

        scale_origin = (
            None
            if origin_widget is None
            else origin_widget.get_screen_space_center()
        )

        assert bui.app.classic is not None
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=('menu_minimal_no_back'),
                transition=transition,
                scale_origin_stack_offset=scale_origin,
                scale=scale,
                darken_behind=True,
            ),
        )

        close_button = bui.buttonwidget(
            parent=self._root_widget,
            scale=0.5,
            position=(30, yoffs - 30),
            size=(60, 60),
            on_activate_call=self._do_back,
            autoselect=True,
            color=(0.55, 0.5, 0.6),
            label=bui.charstr(bui.SpecialChar.CLOSE),
            textcolor=(1, 1, 1),
        )

        v = yoffs - 74

        txoffs = -200
        bui.textwidget(
            parent=self._root_widget,
            text=_commonassets.strings.values.code,
            position=(width * 0.5 + txoffs + 22, v),
            color=(0.8, 0.8, 0.8, 1.0),
            size=(90, 30),
            h_align='right',
            maxwidth=100,
        )
        v -= 8

        self._text_field = bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.5 + txoffs + 125, v),
            size=(280, 46),
            text='',
            h_align='left',
            v_align='center',
            max_chars=64,
            color=(0.9, 0.9, 0.9, 1.0),
            description=_commonassets.strings.values.code,
            editable=True,
            autoselect=True,
            padding=4,
            on_submit_call=self._activate_enter_button,
        )
        if close_button is not None:
            bui.widget(edit=close_button, down_widget=self._text_field)

        v -= 79
        b_width = 200
        self._enter_button = btn2 = bui.buttonwidget(
            parent=self._root_widget,
            position=(width * 0.5 - b_width * 0.5, v),
            size=(b_width, 60),
            scale=1.0,
            label=_commonassets.strings.actions.submit,
            on_activate_call=self._do_enter,
            autoselect=True,
        )
        bui.containerwidget(
            edit=self._root_widget,
            start_button=btn2,
            selected_child=self._text_field,
        )
        if close_button is not None:
            bui.containerwidget(
                edit=self._root_widget,
                cancel_button=close_button,
            )

    def _do_back(self) -> None:
        # pylint: disable=cyclic-import

        # Handle modal case:

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        bui.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )

    def _activate_enter_button(self) -> None:
        self._enter_button.activate()

    def _do_enter(self) -> None:
        # pylint: disable=cyclic-import
        # from bauiv1lib.settings.advanced import AdvancedSettingsWindow

        plus = bui.app.plus
        assert plus is not None

        description: Any = bui.textwidget(query=self._text_field)
        assert isinstance(description, str)

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return
        bui.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )

        # Used for things like unlocking shared playlists or linking
        # accounts: talk directly to V1 server via transactions.
        if plus.get_v1_account_state() != 'signed_in':
            bui.screenmessage(
                _classicassets.strings.account.not_signed_in, color=(1, 0, 0)
            )
            _builtinassets.audio.error.get().play()
        else:
            plus.add_v1_account_transaction(
                {
                    'type': 'PROMO_CODE',
                    'expire_time': time.time() + 5,
                    'code': description,
                }
            )
            plus.run_v1_account_transactions()


async def _send_info(description: str) -> None:
    from bacommon.classic import SendInfoMessage

    plus = bui.app.plus
    assert plus is not None

    classic = bui.app.classic
    assert classic is not None

    ui_pause: bui.RootUIUpdatePause | None = None  # pylint: disable=W0612

    try:
        # Don't allow *anything* if our V2 transport connection isn't up.
        if not plus.cloud.connected:
            bui.screenmessage(
                _commonassets.strings.status.unavailable_no_connection,
                color=(1, 0, 0),
            )
            _builtinassets.audio.error.get().play()
            return

        # Pause root ui updates so stuff like token counts don't change
        # automatically until we've run any client-effect animations
        # resulting from this message.
        ui_pause = bui.RootUIUpdatePause()

        # Ship to V2 server, with or without account info.
        if plus.accounts.primary is not None:
            with plus.accounts.primary:
                response = await plus.cloud.send_message_async(
                    SendInfoMessage(description)
                )
        else:
            response = await plus.cloud.send_message_async(
                SendInfoMessage(description)
            )

        # Support simple message printing from v2 server. (Current
        # servers only populate this for old builds -- new ones get
        # client-effects -- so treat anything arriving as literal
        # display text rather than legacy-translating it.)
        if response.message is not None:
            bui.screenmessage(
                bui.langstr_value(response.message),
                color=(0, 1, 0),
            )
        # As of newer builds we support client-effects too.
        if response.effects:
            classic.run_bs_client_effects(response.effects)

        # If V2 handled it, we're done.
        if response.handled:
            return

        # Ok; V2 didn't handle it. Try V1 if we're signed in there.
        if plus.get_v1_account_state() != 'signed_in':
            bui.screenmessage(
                _classicassets.strings.account.not_signed_in, color=(1, 0, 0)
            )
            _builtinassets.audio.error.get().play()
            return

        # Push it along to v1 as an old style code. Allow v2 response to
        # sub in its own code.
        plus.add_v1_account_transaction(
            {
                'type': 'PROMO_CODE',
                'expire_time': time.time() + 5,
                'code': (
                    description
                    if response.legacy_code is None
                    else response.legacy_code
                ),
            }
        )
        plus.run_v1_account_transactions()
    except Exception:
        logging.exception('Error sending promo code.')
        bui.screenmessage('Error sending code (see log).', color=(1, 0, 0))
        _builtinassets.audio.error.get().play()
    finally:
        # Make sure ui-pause is dead even if something is holding
        # on to this stack frame.
        ui_pause = None
