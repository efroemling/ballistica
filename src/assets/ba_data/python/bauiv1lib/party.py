# Released under the MIT License. See LICENSE for details.
#
"""Provides party related UI."""

import math
import logging
from typing import TYPE_CHECKING, cast

from efro.dataclassio import dataclass_to_json
import bacommon.depiction as bdep
import bacommon.docui.v2 as dui2
import bacommon.hostui as hui
from bacommon.hostui import HOST_UI_MIN_BUILD
from bacommon.langstr import LangStrSpecValue
import bauiv1 as bui
from bauiv1 import _commonassets, _classicassets
from bauiv1 import _builtinassets
import bascenev1 as bs
from bauiv1lib.popup import PopupMenuWindow
from bauiv1lib.hostdocui import (
    show_host_docui_page,
    show_host_docui_window,
    button_label,
)

if TYPE_CHECKING:
    from typing import Sequence, Any

    import bacommon.docui.v2

    from bauiv1lib.popup import PopupWindow


class PartyWindow(bui.Window):
    """Party list/chat window."""

    def __init__(self, origin: Sequence[float] = (0, 0)):

        self._uiopenstate = bui.UIOpenState('classicparty')
        self._popup_type: str | None = None
        self._popup_party_member_client_id: int | None = None
        self._popup_party_member_is_host: bool | None = None
        self._popup_chat_msg: str | None = None
        self._popup_chat_browse: bacommon.docui.v2.Browse | None = None
        self._width = 500
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._height = (
            365
            if uiscale is bui.UIScale.SMALL
            else 480 if uiscale is bui.UIScale.MEDIUM else 600
        )
        self._idprefix = bui.app.ui_v1.new_id_prefix('party')
        self._display_old_msgs = True
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                transition='in_scale',
                color=(0.40, 0.55, 0.20),
                parent=bui.get_special_widget('overlay_stack'),
                on_outside_click_call=self.close_with_sound,
                scale_origin_stack_offset=origin,
                scale=(
                    1.8
                    if uiscale is bui.UIScale.SMALL
                    else 1.3 if uiscale is bui.UIScale.MEDIUM else 0.9
                ),
                stack_offset=(
                    (200, -10)
                    if uiscale is bui.UIScale.SMALL
                    else (
                        (260, 0) if uiscale is bui.UIScale.MEDIUM else (370, 60)
                    )
                ),
                darken_behind=True,
            ),
            # We exist in the overlay stack so main-windows being
            # recreated doesn't affect us.
            prevent_main_window_auto_recreate=False,
        )

        self._cancel_button = bui.buttonwidget(
            parent=self._root_widget,
            id=f'{self._idprefix}|cancel',
            scale=0.7,
            position=(30, self._height - 47),
            size=(50, 50),
            on_activate_call=self.close,
            autoselect=True,
            color=(0.45, 0.63, 0.15),
            label=bui.SpecialChar.CLOSE.value,
        )
        bui.containerwidget(
            edit=self._root_widget, cancel_button=self._cancel_button
        )

        self._menu_button = bui.buttonwidget(
            parent=self._root_widget,
            id=f'{self._idprefix}|menu',
            scale=0.7,
            position=(self._width - 60, self._height - 47),
            size=(50, 50),
            label='...',
            autoselect=True,
            button_type='square',
            on_activate_call=bui.WeakCallStrict(self._on_menu_button_press),
            color=(0.55, 0.73, 0.25),
            iconscale=1.2,
        )
        self._menu_popup: PopupMenuWindow | None = None
        self._menu_host_buttons: list[hui.Button] = []

        # Flash the '...' button while our host wants it to.
        self._menu_flash_timer = bui.AppTimer(
            0.05, bui.WeakCallStrict(self._update_menu_flash), repeat=True
        )
        self._menu_flashing = False

        info = bs.get_connection_to_host_info_2()

        if info is not None and info.name != '':
            title = bui.LangStr.from_text(info.name)
        else:
            title = _classicassets.strings.party.title

        self._title_text = bui.textwidget(
            parent=self._root_widget,
            scale=0.9,
            color=(0.5, 0.7, 0.5),
            text=title,
            size=(0, 0),
            position=(self._width * 0.5, self._height - 29),
            maxwidth=self._width * 0.7,
            h_align='center',
            v_align='center',
        )

        self._empty_str = bui.textwidget(
            parent=self._root_widget,
            scale=0.6,
            size=(0, 0),
            # color=(0.5, 1.0, 0.5),
            shadow=0.3,
            position=(self._width * 0.5, self._height - 57),
            maxwidth=self._width * 0.85,
            h_align='center',
            v_align='center',
        )
        self._empty_str_2 = bui.textwidget(
            parent=self._root_widget,
            scale=0.5,
            size=(0, 0),
            color=(0.5, 1.0, 0.5),
            shadow=0.1,
            position=(self._width * 0.5, self._height - 75),
            maxwidth=self._width * 0.85,
            h_align='center',
            v_align='center',
        )

        self._scroll_width = self._width - 50
        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            id=f'{self._idprefix}|scroll',
            size=(self._scroll_width, self._height - 200),
            position=(30, 80),
            color=(0.4, 0.6, 0.3),
            border_opacity=0.6,
        )
        self._columnwidget = bui.columnwidget(
            parent=self._scrollwidget,
            id=f'{self._idprefix}|column',
            border=2,
            left_border=-200,
            margin=0,
        )
        bui.widget(edit=self._menu_button, down_widget=self._columnwidget)

        self._muted_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.5),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text=_classicassets.strings.party.chat_muted,
        )
        self._chat_texts: list[bui.Widget] = []

        self._text_field = txt = bui.textwidget(
            parent=self._root_widget,
            id=f'{self._idprefix}|messagetext',
            editable=True,
            size=(530, 40),
            position=(44, 39),
            text='',
            maxwidth=494,
            shadow=0.3,
            flatness=1.0,
            description=_classicassets.strings.party.chat_message,
            autoselect=True,
            v_align='center',
            corner_scale=0.7,
            string_edit_kind=bui.StringEditKind.CHAT.value,
        )

        bui.widget(
            edit=self._scrollwidget,
            autoselect=True,
            left_widget=self._cancel_button,
            up_widget=self._cancel_button,
            down_widget=self._text_field,
        )
        bui.widget(
            edit=self._columnwidget,
            autoselect=True,
            up_widget=self._cancel_button,
            down_widget=self._text_field,
        )
        bui.containerwidget(edit=self._root_widget, selected_child=txt)

        btn = bui.buttonwidget(
            parent=self._root_widget,
            id=f'{self._idprefix}|send',
            size=(50, 35),
            label=_commonassets.strings.actions.send,
            button_type='square',
            autoselect=True,
            position=(self._width - 70, 35),
            on_activate_call=self._send_chat_message,
        )

        bui.textwidget(edit=txt, on_submit_call=btn.activate)
        bui.widget(edit=txt, down_widget=btn)
        self._name_widgets: list[bui.Widget] = []
        self._roster: list[dict[str, Any]] | None = None
        self._update_timer = bui.AppTimer(
            1.0, bui.WeakCallStrict(self._update), repeat=True
        )
        self._update()

    def _update_menu_flash(self) -> None:
        classic = bui.app.classic
        assert classic is not None
        now = bui.apptime()
        start, end = classic.host_ui.get_party_menu_flash_times()
        if now < end:
            # A quick flash for a moment, then a slower pulse (as the
            # party icon does).
            elapsed = now - start
            freq = 4.0 if elapsed < 1.5 else 1.0
            mult = 1.0 + abs(1.5 * math.sin(freq * math.pi * elapsed))
            self._menu_flashing = True
        elif self._menu_flashing:
            mult = 1.0
            self._menu_flashing = False
        else:
            return
        bui.buttonwidget(
            edit=self._menu_button,
            color=(0.55 * mult, 0.73 * mult, 0.25 * mult),
        )

    def on_chat_message(self, msg: str) -> None:
        """Called when a new chat message comes through."""
        if not bui.app.config.resolve('Chat Muted'):
            # (It's the newest message the engine holds; so is its
            # sender.)
            senders = bs.get_chat_message_senders()
            self._add_msg(msg, senders[-1] if senders else None)

    def _add_msg(self, msg: str, sender: str | None) -> None:
        txt = bui.textwidget(
            parent=self._columnwidget,
            h_align='left',
            v_align='center',
            scale=0.55,
            size=(900, 13),
            text=msg,
            # Peer-supplied text; never compile it as a resource string.
            literal=True,
            autoselect=True,
            maxwidth=self._scroll_width * 0.94,
            shadow=0.3,
            flatness=1.0,
            selectable=True,
        )
        bui.textwidget(
            edit=txt,
            on_activate_call=bui.CallStrict(
                self._on_chat_msg_press, msg, sender, txt
            ),
        )

        self._chat_texts.append(txt)
        while len(self._chat_texts) > 40:
            self._chat_texts.pop(0).delete()
        bui.containerwidget(edit=self._columnwidget, visible_child=txt)

    def _copy_msg(self, msg: str) -> None:
        if bui.clipboard_is_supported():
            # Extract content after the first colon
            if ':' in msg:
                content = msg.split(':', 1)[1].strip()
            else:
                # Just a safe check
                content = msg

            bui.clipboard_set_text(content)
            bui.screenmessage(
                _commonassets.strings.status.copied_to_clipboard,
                color=(0, 1, 0),
            )

    def _on_menu_button_press(self) -> None:
        is_muted = bui.app.config.resolve('Chat Muted')
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale

        choices: list[str] = ['unmute' if is_muted else 'mute']
        choices_display: list[bui.Lstr | bui.LangStr] = [
            (
                _classicassets.strings.party.unmute_chat
                if is_muted
                else _classicassets.strings.party.mute_chat
            )
        ]

        # Then anything our host (or we, when hosting) defined.
        host_buttons = bui.app.classic.host_ui.get_shown_buttons(
            hui.ButtonPlacement.PARTY_MENU
        )
        for i, button in enumerate(host_buttons):
            choices.append(f'host{i}')
            choices_display.append(button_label(button))
        self._menu_host_buttons = host_buttons

        # Allow 'Add to Favorites' only if we're connected to a host
        # that allows it (hosts whose address won't stay the same, such
        # as our cloud-hosted games, turn it off).
        server_info = bs.get_connection_to_host_info_2()
        if server_info is not None and server_info.allow_favorites:
            choices.append('add_to_favorites')
            choices_display.append(
                _classicassets.strings.party.add_to_favorites
            )

        self._menu_popup = PopupMenuWindow(
            position=self._menu_button.get_screen_space_center(),
            scale=(
                2.3
                if uiscale is bui.UIScale.SMALL
                else 1.65 if uiscale is bui.UIScale.MEDIUM else 1.23
            ),
            choices=choices,
            choices_display=choices_display,
            current_choice='unmute' if is_muted else 'mute',
            delegate=self,
        )
        self._popup_type = 'menu'

    def _update(self) -> None:
        # update muted state
        if bui.app.config.resolve('Chat Muted'):
            bui.textwidget(edit=self._muted_text, color=(1, 1, 1, 0.3))
            # clear any chat texts we're showing
            if self._chat_texts:
                while self._chat_texts:
                    first = self._chat_texts.pop()
                    first.delete()
        else:
            bui.textwidget(edit=self._muted_text, color=(1, 1, 1, 0.0))
            # add all existing messages if chat is not muted
            if self._display_old_msgs:
                msgs = bs.get_chat_messages()
                senders = bs.get_chat_message_senders()
                for i, msg in enumerate(msgs):
                    self._add_msg(
                        msg,
                        senders[i] if len(senders) == len(msgs) else None,
                    )
                self._display_old_msgs = False

        # update roster section
        roster = bs.get_game_roster()
        if roster != self._roster:
            self._roster = roster

            # clear out old
            for widget in self._name_widgets:
                widget.delete()
            self._name_widgets = []
            if not self._roster:
                top_section_height = 60
                bui.textwidget(
                    edit=self._empty_str,
                    text=_classicassets.strings.party.empty,
                )
                bui.textwidget(
                    edit=self._empty_str_2,
                    text=_classicassets.strings.gather.description_short,
                )
                bui.scrollwidget(
                    edit=self._scrollwidget,
                    size=(
                        self._width - 50,
                        self._height - top_section_height - 110,
                    ),
                    position=(30, 80),
                )
            else:
                columns = (
                    1
                    if len(self._roster) == 1
                    else 2 if len(self._roster) == 2 else 3
                )
                rows = int(math.ceil(float(len(self._roster)) / columns))
                c_width = (self._width * 0.9) / max(3, columns)
                c_width_total = c_width * columns
                c_height = 24
                c_height_total = c_height * rows
                for y in range(rows):
                    for x in range(columns):
                        index = y * columns + x
                        if index < len(self._roster):
                            self._add_roster_entry(
                                index,
                                pos=(
                                    self._width * 0.5
                                    - c_width_total * 0.5
                                    + c_width * x,
                                    self._height - 65 - c_height * y,
                                ),
                                c_width=c_width,
                            )
                bui.textwidget(edit=self._empty_str, text='')
                bui.textwidget(edit=self._empty_str_2, text='')
                bui.scrollwidget(
                    edit=self._scrollwidget,
                    size=(
                        self._width - 50,
                        max(100, self._height - 139 - c_height_total),
                    ),
                    position=(30, 80),
                )

    def popup_menu_selected_choice(
        self, popup_window: PopupMenuWindow, choice: str
    ) -> None:
        """Called when a choice is selected in the popup."""
        if self._popup_type == 'chatMessagePress':
            self._on_chat_popup_choice(
                choice, popup_window.get_choice_widget(choice)
            )
        elif self._popup_type == 'partyMemberPress':
            if self._popup_party_member_is_host:
                _builtinassets.audio.error.get().play()
                bui.screenmessage(
                    _classicassets.strings.party.cant_kick_host,
                    color=(1, 0, 0),
                )
            elif (
                kick_request := self._kick_request(
                    self._popup_party_member_client_id
                )
            ) is not None:
                # Our host has a page for this; open it.
                self.close()
                show_host_docui_window(
                    hui.Button(
                        label=LangStrSpecValue.literal(''),
                        placement=hui.ButtonPlacement.PARTY_MENU,
                        request=kick_request,
                        layout=dui2.WindowLayout.WIDE,
                    )
                )
            else:
                assert self._popup_party_member_client_id is not None

                # Ban for 5 minutes.
                result = bs.disconnect_client(
                    self._popup_party_member_client_id, ban_time=5 * 60
                )
                if not result:
                    _builtinassets.audio.error.get().play()
                    bui.screenmessage(
                        _commonassets.strings.status.not_available,
                        color=(1, 0, 0),
                    )
        elif self._popup_type == 'menu':
            if choice in ('mute', 'unmute'):
                cfg = bui.app.config
                cfg['Chat Muted'] = choice == 'mute'
                cfg.apply_and_commit()
                self._display_old_msgs = True
                self._update()
            if choice.startswith('host'):
                try:
                    button = self._menu_host_buttons[int(choice[4:])]
                except ValueError, IndexError:
                    button = None
                if button is not None:
                    # Party window lives in the overlay stack; get it out
                    # of the way of the page.
                    self.close()
                    show_host_docui_window(button)
            if choice == 'add_to_favorites':
                info = bs.get_connection_to_host_info_2()
                if info is not None:
                    self._add_to_favorites(
                        name=info.name,
                        address=info.address,
                        port_num=info.port,
                    )
                else:
                    # We should not allow the user to see this option
                    # if they aren't in a server; this is our bad.
                    bui.screenmessage(
                        _commonassets.strings.values.error, color=(1, 0, 0)
                    )
                    _builtinassets.audio.error.get().play()
        else:
            print(f'unhandled popup type: {self._popup_type}')

    def _add_to_favorites(
        self, name: str, address: str | None, port_num: int | None
    ) -> None:
        addr = address
        if addr == '':
            bui.screenmessage(
                _classicassets.strings.gather.invalid_address_error,
                color=(1, 0, 0),
            )
            _builtinassets.audio.error.get().play()
            return
        port = port_num if port_num is not None else -1
        if port > 65535 or port < 0:
            bui.screenmessage(
                _classicassets.strings.gather.invalid_port_error,
                color=(1, 0, 0),
            )
            _builtinassets.audio.error.get().play()
            return

        # Avoid empty names.
        if not name:
            name = f'{addr}@{port}'

        config = bui.app.config

        if addr:
            if not isinstance(config.get('Saved Servers'), dict):
                config['Saved Servers'] = {}
            config['Saved Servers'][f'{addr}@{port}'] = {
                'addr': addr,
                'port': port,
                'name': name,
            }
            config.commit()
            _commonassets.audio.gun_cocking.get().play()
            bui.screenmessage(
                _classicassets.strings.gather.added_to_favorites(name=name),
                color=(0, 1, 0),
            )
        else:
            bui.screenmessage(
                _classicassets.strings.gather.invalid_address_error,
                color=(1, 0, 0),
            )
            _builtinassets.audio.error.get().play()

    def popup_menu_closing(self, _popup_window: PopupWindow) -> None:
        """Called when the popup is closing."""
        self._menu_popup = None

    def _add_roster_entry(
        self, index: int, *, pos: tuple[float, float], c_width: float
    ) -> None:
        """Add one client's name to the roster section.

        ``pos`` is its column's left edge (vertically centered); the
        name is centered in the column.
        """
        entry = self._roster[index] if self._roster is not None else None
        assert entry is not None

        # In newer versions client_id will be present and we can use
        # that to determine who the host is. In older versions we assume
        # the first client is host.
        client_id = entry['client_id']
        is_host = client_id == -1 if client_id is not None else index == 0

        # Each client shows as a name depiction. The host sends one for
        # accounts it can vouch for (its own and v2-authed clients');
        # for anything else, which is only what the client says it is,
        # we make a plain-text one with no icons (an icon could pass
        # for an account it doesn't own).
        depiction = entry.get('account_name_depiction')
        if not isinstance(depiction, str):
            try:
                # (Repeated names get numbered, so members can be told
                # apart; host pages number them the same way.)
                p_str = bui.app.lang.remove_custom_unicode_chars(
                    bs.get_party_member_names().get(
                        client_id, entry['display_string']
                    )
                )
            except Exception:
                logging.exception('Error calcing client name str.')
                p_str = '???'
            depiction = dataclass_to_json(
                bdep.NameDepiction(bs.plain_name_json(p_str))
            )

        # The depiction is the button's whole look, so selection
        # brightens and pulses the name itself. (No "(host)" marker: the
        # host is always listed first, and its page says so.)
        height = 22.0
        width = c_width * 0.85
        widget = bui.buttonwidget(
            parent=self._root_widget,
            # (Centered in the column, as is the name within it.)
            position=(pos[0] + (c_width - width) * 0.5, pos[1] - height * 0.5),
            size=(width, height),
            label='',
            autoselect=True,
            depiction=depiction,
            depiction_h_align='center',
            depiction_hit_area=True,
        )
        bui.buttonwidget(
            edit=widget,
            on_activate_call=bui.CallStrict(
                self._on_party_member_press, client_id, is_host, widget
            ),
        )
        self._name_widgets.append(widget)

    def _on_party_member_press(
        self, client_id: int, is_host: bool, widget: bui.Widget
    ) -> None:
        # Hosts with a page for party members (our own hosting
        # included) get it opened; it's the place for everything
        # about them, kicking included.
        browse = self._client_page_browse(client_id)
        if browse is not None:
            # (Open it before closing ourself so it can scale in from
            # the pressed button while that still exists.)
            show_host_docui_page(browse, origin_widget=widget)
            self.close()
            return

        # Otherwise, if we're the host, pop up 'kick' options for all
        # non-host members.
        if bs.get_foreground_host_session() is not None:
            kick_str = _classicassets.strings.ui.kick
        else:
            info = bs.get_connection_to_host_info_2()
            # Kick votes appeared in build 14248.
            if info is None or info.build_number < 14248:
                return
            # Hosts with host-ui offer kicking only where their kick
            # page says so (see HostUISubsystem.set_kick_page); older
            # ones run the engine's own kick votes.
            if (
                info.build_number >= HOST_UI_MIN_BUILD
                and self._kick_request(client_id) is None
            ):
                return
            kick_str = _classicassets.strings.party.kick_vote
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._menu_popup = PopupMenuWindow(
            position=widget.get_screen_space_center(),
            scale=(
                2.3
                if uiscale is bui.UIScale.SMALL
                else 1.65 if uiscale is bui.UIScale.MEDIUM else 1.23
            ),
            choices=['kick'],
            choices_display=[kick_str],
            current_choice='kick',
            delegate=self,
        )
        self._popup_type = 'partyMemberPress'
        self._popup_party_member_client_id = client_id
        self._popup_party_member_is_host = is_host

    def _on_chat_msg_press(
        self, msg: str, sender: str | None, widget: bui.Widget
    ) -> None:
        """Copy a message, or offer its sender's page too if there is one."""
        client_id = None if sender is None else _sender_client_id(sender)
        browse = (
            None if client_id is None else self._client_page_browse(client_id)
        )
        if client_id is None or browse is None:
            self._copy_msg(msg)
            return
        # (Named as the party list shows them, which is what the page
        # opens on.)
        name = bs.get_party_member_names().get(client_id, sender)
        uiscale = bui.app.ui_v1.uiscale
        self._menu_popup = PopupMenuWindow(
            position=widget.get_screen_space_center(),
            scale=(
                2.3
                if uiscale is bui.UIScale.SMALL
                else 1.65 if uiscale is bui.UIScale.MEDIUM else 1.23
            ),
            choices=['copy', 'view'],
            choices_display=[
                _commonassets.strings.actions.copy,
                _classicassets.strings.party.view_member(name=name or '?'),
            ],
            current_choice='view',
            delegate=self,
        )
        self._popup_type = 'chatMessagePress'
        self._popup_chat_msg = msg
        self._popup_chat_browse = browse

    def _on_chat_popup_choice(
        self, choice: str, choice_widget: bui.Widget | None
    ) -> None:
        if choice == 'copy' and self._popup_chat_msg is not None:
            self._copy_msg(self._popup_chat_msg)
        elif choice == 'view' and self._popup_chat_browse is not None:
            # (The page scales in from the View item, which still
            # exists while the menu transitions out; open it before
            # closing ourself.)
            show_host_docui_page(
                self._popup_chat_browse, origin_widget=choice_widget
            )
            self.close()

    def _client_page_browse(
        self, client_id: int | None
    ) -> bacommon.docui.v2.Browse | None:
        """Our host's page for a party member (if it offers one)."""
        classic = bui.app.classic
        if client_id is None or classic is None:
            return None
        return classic.host_ui.get_client_page_browse(client_id)

    def _kick_request(
        self, client_id: int | None
    ) -> bacommon.docui.v2.Request | None:
        """Our host's page for kicking a client (if it offers one)."""
        classic = bui.app.classic
        if client_id is None or classic is None:
            return None
        return classic.host_ui.get_kick_request(client_id)

    def _send_chat_message(self) -> None:
        text = cast(str, bui.textwidget(query=self._text_field)).strip()
        if text != '':
            bs.chatmessage(text)
            bui.textwidget(edit=self._text_field, text='')

    def close(self) -> None:
        """Close the window."""
        # exit our menu widget if it's up (likely from a hotkey press)
        if self._menu_popup is not None:
            self._menu_popup.on_popup_cancel()

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        bui.containerwidget(edit=self._root_widget, transition='out_scale')

    def close_with_sound(self) -> None:
        """Close the window and make a lovely sound."""
        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        bui.play_swish()
        self.close()


def _sender_client_id(sender: str) -> int | None:
    """Which party member a chat message's sender name is (if clear).

    Hosts (that offer party member pages) name chat senders by their one
    player's name if they have exactly one in the game, else by the
    name the party list shows for them; match that against the roster.
    None if no one, or more than one, matches.
    """
    matches: set[int] = set()
    for entry in bs.get_game_roster():
        client_id = entry['client_id']
        if not isinstance(client_id, int):
            continue
        names = [p['name'] for p in entry['players']]
        if sender == (names[0] if len(names) == 1 else entry['display_string']):
            matches.add(client_id)
    return next(iter(matches)) if len(matches) == 1 else None
