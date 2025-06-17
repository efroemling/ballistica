# Released under the MIT License. See LICENSE for details.
#
"""Provides party related UI."""

from __future__ import annotations

import math
import logging
from typing import TYPE_CHECKING, cast

import bauiv1 as bui
import bascenev1 as bs
from bauiv1lib.popup import PopupMenuWindow

if TYPE_CHECKING:
    from typing import Sequence, Any

    from bauiv1lib.popup import PopupWindow


class PartyWindow(bui.Window):
    """Party list/chat window."""

    def __del__(self) -> None:
        bui.set_party_window_open(False)

    def __init__(self, origin: Sequence[float] = (0, 0)):
        bui.set_party_window_open(True)
        self._r = 'partyWindow'
        self._popup_type: str | None = None
        self._popup_party_member_client_id: int | None = None
        self._popup_party_member_is_host: bool | None = None
        self._width = 500
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._height = (
            365
            if uiscale is bui.UIScale.SMALL
            else 480 if uiscale is bui.UIScale.MEDIUM else 600
        )
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
            ),
            # We exist in the overlay stack so main-windows being
            # recreated doesn't affect us.
            prevent_main_window_auto_recreate=False,
        )

        self._cancel_button = bui.buttonwidget(
            parent=self._root_widget,
            scale=0.7,
            position=(30, self._height - 47),
            size=(50, 50),
            label='',
            on_activate_call=self.close,
            autoselect=True,
            color=(0.45, 0.63, 0.15),
            icon=bui.gettexture('crossOut'),
            iconscale=1.2,
        )
        bui.containerwidget(
            edit=self._root_widget, cancel_button=self._cancel_button
        )

        self._menu_button = bui.buttonwidget(
            parent=self._root_widget,
            scale=0.7,
            position=(self._width - 60, self._height - 47),
            size=(50, 50),
            label='...',
            autoselect=True,
            button_type='square',
            on_activate_call=bui.WeakCall(self._on_menu_button_press),
            color=(0.55, 0.73, 0.25),
            iconscale=1.2,
        )

        info = bs.get_connection_to_host_info_2()

        if info is not None and info.name != '':
            title = bui.Lstr(value=info.name)
        else:
            title = bui.Lstr(resource=f'{self._r}.titleText')

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
            size=(self._scroll_width, self._height - 200),
            position=(30, 80),
            color=(0.4, 0.6, 0.3),
            border_opacity=0.6,
        )
        self._columnwidget = bui.columnwidget(
            parent=self._scrollwidget, border=2, left_border=-200, margin=0
        )
        bui.widget(edit=self._menu_button, down_widget=self._columnwidget)

        self._muted_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.5),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text=bui.Lstr(resource='chatMutedText'),
        )
        self._chat_texts: list[bui.Widget] = []

        self._text_field = txt = bui.textwidget(
            parent=self._root_widget,
            editable=True,
            size=(530, 40),
            position=(44, 39),
            text='',
            maxwidth=494,
            shadow=0.3,
            flatness=1.0,
            description=bui.Lstr(resource=f'{self._r}.chatMessageText'),
            autoselect=True,
            v_align='center',
            corner_scale=0.7,
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
            size=(50, 35),
            label=bui.Lstr(resource=f'{self._r}.sendText'),
            button_type='square',
            autoselect=True,
            position=(self._width - 70, 35),
            on_activate_call=self._send_chat_message,
        )

        bui.textwidget(edit=txt, on_return_press_call=btn.activate)
        bui.widget(edit=txt, down_widget=btn)
        self._name_widgets: list[bui.Widget] = []
        self._roster: list[dict[str, Any]] | None = None
        self._update_timer = bui.AppTimer(
            1.0, bui.WeakCall(self._update), repeat=True
        )
        self._update()

    def on_chat_message(self, msg: str) -> None:
        """Called when a new chat message comes through."""
        if not bui.app.config.resolve('Chat Muted'):
            self._add_msg(msg)

    def _add_msg(self, msg: str) -> None:
        txt = bui.textwidget(
            parent=self._columnwidget,
            h_align='left',
            v_align='center',
            scale=0.55,
            size=(900, 13),
            text=msg,
            autoselect=True,
            maxwidth=self._scroll_width * 0.94,
            shadow=0.3,
            flatness=1.0,
            on_activate_call=bui.Call(self._copy_msg, msg),
            selectable=True,
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
                bui.Lstr(resource='copyConfirmText'), color=(0, 1, 0)
            )

    def _on_menu_button_press(self) -> None:
        is_muted = bui.app.config.resolve('Chat Muted')
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale

        choices: list[str] = ['unmute' if is_muted else 'mute']
        choices_display: list[bui.Lstr] = [
            bui.Lstr(resource='chatUnMuteText' if is_muted else 'chatMuteText')
        ]

        # Allow the 'Add to Favorites' option only if we're actually
        # connected to a party and if it doesn't seem to be a private
        # party (those are dynamically assigned addresses and ports so
        # it makes no sense to save them).
        server_info = bs.get_connection_to_host_info_2()
        if server_info is not None and not server_info.name.startswith(
            'Private Party '
        ):
            choices.append('add_to_favorites')
            choices_display.append(bui.Lstr(resource='addToFavoritesText'))

        PopupMenuWindow(
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
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-nested-blocks

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
                for msg in msgs:
                    self._add_msg(msg)
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
                    text=bui.Lstr(resource=f'{self._r}.emptyText'),
                )
                bui.textwidget(
                    edit=self._empty_str_2,
                    text=bui.Lstr(resource='gatherWindow.descriptionShortText'),
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
                            t_scale = 0.65
                            pos = (
                                self._width * 0.53
                                - c_width_total * 0.5
                                + c_width * x
                                - 23,
                                self._height - 65 - c_height * y - 15,
                            )

                            # if there are players present for this client, use
                            # their names as a display string instead of the
                            # client spec-string
                            try:
                                if self._roster[index]['players']:
                                    # if there's just one, use the full name;
                                    # otherwise combine short names
                                    if len(self._roster[index]['players']) == 1:
                                        p_str = self._roster[index]['players'][
                                            0
                                        ]['name_full']
                                    else:
                                        p_str = '/'.join(
                                            [
                                                entry['name']
                                                for entry in self._roster[
                                                    index
                                                ]['players']
                                            ]
                                        )
                                        if len(p_str) > 25:
                                            p_str = p_str[:25] + '...'
                                else:
                                    p_str = self._roster[index][
                                        'display_string'
                                    ]
                            except Exception:
                                logging.exception(
                                    'Error calcing client name str.'
                                )
                                p_str = '???'

                            widget = bui.textwidget(
                                parent=self._root_widget,
                                position=(pos[0], pos[1]),
                                scale=t_scale,
                                size=(c_width * 0.85, 30),
                                maxwidth=c_width * 0.85,
                                color=(1, 1, 1) if index == 0 else (1, 1, 1),
                                selectable=True,
                                autoselect=True,
                                click_activate=True,
                                text=bui.Lstr(value=p_str),
                                h_align='left',
                                v_align='center',
                            )
                            self._name_widgets.append(widget)

                            # in newer versions client_id will be present and
                            # we can use that to determine who the host is.
                            # in older versions we assume the first client is
                            # host
                            if self._roster[index]['client_id'] is not None:
                                is_host = self._roster[index]['client_id'] == -1
                            else:
                                is_host = index == 0

                            # FIXME: Should pass client_id to these sort of
                            #  calls; not spec-string (perhaps should wait till
                            #  client_id is more readily available though).
                            bui.textwidget(
                                edit=widget,
                                on_activate_call=bui.Call(
                                    self._on_party_member_press,
                                    self._roster[index]['client_id'],
                                    is_host,
                                    widget,
                                ),
                            )
                            pos = (
                                self._width * 0.53
                                - c_width_total * 0.5
                                + c_width * x,
                                self._height - 65 - c_height * y,
                            )

                            # Make the assumption that the first roster
                            # entry is the server.
                            # FIXME: Shouldn't do this.
                            if is_host:
                                twd = min(
                                    c_width * 0.85,
                                    bui.get_string_width(
                                        p_str, suppress_warning=True
                                    )
                                    * t_scale,
                                )
                                self._name_widgets.append(
                                    bui.textwidget(
                                        parent=self._root_widget,
                                        position=(
                                            pos[0] + twd + 1,
                                            pos[1] - 0.5,
                                        ),
                                        size=(0, 0),
                                        h_align='left',
                                        v_align='center',
                                        maxwidth=c_width * 0.96 - twd,
                                        color=(0.1, 1, 0.1, 0.5),
                                        text=bui.Lstr(
                                            resource=f'{self._r}.hostText'
                                        ),
                                        scale=0.4,
                                        shadow=0.1,
                                        flatness=1.0,
                                    )
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
        del popup_window  # unused
        if self._popup_type == 'partyMemberPress':
            if self._popup_party_member_is_host:
                bui.getsound('error').play()
                bui.screenmessage(
                    bui.Lstr(resource='internal.cantKickHostError'),
                    color=(1, 0, 0),
                )
            else:
                assert self._popup_party_member_client_id is not None

                # Ban for 5 minutes.
                result = bs.disconnect_client(
                    self._popup_party_member_client_id, ban_time=5 * 60
                )
                if not result:
                    bui.getsound('error').play()
                    bui.screenmessage(
                        bui.Lstr(resource='getTicketsWindow.unavailableText'),
                        color=(1, 0, 0),
                    )
        elif self._popup_type == 'menu':
            if choice in ('mute', 'unmute'):
                cfg = bui.app.config
                cfg['Chat Muted'] = choice == 'mute'
                cfg.apply_and_commit()
                self._display_old_msgs = True
                self._update()
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
                        bui.Lstr(resource='errorText'), color=(1, 0, 0)
                    )
                    bui.getsound('error').play()
        else:
            print(f'unhandled popup type: {self._popup_type}')

    def _add_to_favorites(
        self, name: str, address: str | None, port_num: int | None
    ) -> None:
        addr = address
        if addr == '':
            bui.screenmessage(
                bui.Lstr(resource='internal.invalidAddressErrorText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return
        port = port_num if port_num is not None else -1
        if port > 65535 or port < 0:
            bui.screenmessage(
                bui.Lstr(resource='internal.invalidPortErrorText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
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
            bui.getsound('gunCocking').play()
            bui.screenmessage(
                bui.Lstr(
                    resource='addedToFavoritesText', subs=[('${NAME}', name)]
                ),
                color=(0, 1, 0),
            )
        else:
            bui.screenmessage(
                bui.Lstr(resource='internal.invalidAddressErrorText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()

    def popup_menu_closing(self, popup_window: PopupWindow) -> None:
        """Called when the popup is closing."""

    def _on_party_member_press(
        self, client_id: int, is_host: bool, widget: bui.Widget
    ) -> None:
        # if we're the host, pop up 'kick' options for all non-host members
        if bs.get_foreground_host_session() is not None:
            kick_str = bui.Lstr(resource='kickText')
        else:
            # kick-votes appeared in build 14248
            info = bs.get_connection_to_host_info_2()
            if info is None or info.build_number < 14248:
                return
            kick_str = bui.Lstr(resource='kickVoteText')
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        PopupMenuWindow(
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

    def _send_chat_message(self) -> None:
        text = cast(str, bui.textwidget(query=self._text_field)).strip()
        if text != '':
            bs.chatmessage(text)
            bui.textwidget(edit=self._text_field, text='')

    def close(self) -> None:
        """Close the window."""
        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        bui.containerwidget(edit=self._root_widget, transition='out_scale')

    def close_with_sound(self) -> None:
        """Close the window and make a lovely sound."""
        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        bui.getsound('swish').play()
        self.close()
