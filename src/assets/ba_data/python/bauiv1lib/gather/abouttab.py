# Released under the MIT License. See LICENSE for details.
#
"""Defines the about tab in the gather UI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from bauiv1lib.gather import GatherTab
import bauiv1 as bui

if TYPE_CHECKING:
    from bauiv1lib.gather import GatherWindow


class AboutGatherTab(GatherTab):
    """The about tab in the gather UI"""

    def __init__(self, window: GatherWindow) -> None:
        super().__init__(window)
        self._container: bui.Widget | None = None

    def on_activate(
        self,
        parent_widget: bui.Widget,
        tab_button: bui.Widget,
        region_width: float,
        region_height: float,
        region_left: float,
        region_bottom: float,
    ) -> bui.Widget:
        plus = bui.app.plus
        assert plus is not None

        party_button_label = bui.charstr(bui.SpecialChar.TOP_BUTTON)
        message = bui.Lstr(
            resource='gatherWindow.aboutDescriptionText',
            subs=[
                ('${PARTY}', bui.charstr(bui.SpecialChar.PARTY_ICON)),
                ('${BUTTON}', party_button_label),
            ],
        )

        # Let's not talk about sharing in vr-mode; its tricky to fit more
        # than one head in a VR-headset ;-)
        if not bui.app.env.vr:
            message = bui.Lstr(
                value='${A}\n\n${B}',
                subs=[
                    ('${A}', message),
                    (
                        '${B}',
                        bui.Lstr(
                            resource='gatherWindow.'
                            'aboutDescriptionLocalMultiplayerExtraText'
                        ),
                    ),
                ],
            )
        string_height = 400
        include_invite = True
        msc_scale = 1.1
        c_height_2 = min(region_height, string_height * msc_scale + 100)
        try_tickets = plus.get_v1_account_misc_read_val(
            'friendTryTickets', None
        )
        if try_tickets is None:
            include_invite = False
        self._container = bui.containerwidget(
            parent=parent_widget,
            position=(
                region_left,
                region_bottom + (region_height - c_height_2) * 0.5,
            ),
            size=(region_width, c_height_2),
            background=False,
            selectable=include_invite,
        )
        bui.widget(edit=self._container, up_widget=tab_button)

        bui.textwidget(
            parent=self._container,
            position=(
                region_width * 0.5,
                c_height_2 * (0.58 if include_invite else 0.5),
            ),
            color=(0.6, 1.0, 0.6),
            scale=msc_scale,
            size=(0, 0),
            maxwidth=region_width * 0.9,
            max_height=c_height_2 * (0.7 if include_invite else 0.9),
            h_align='center',
            v_align='center',
            text=message,
        )

        if include_invite:
            bui.textwidget(
                parent=self._container,
                position=(region_width * 0.57, 35),
                color=(0, 1, 0),
                scale=0.6,
                size=(0, 0),
                maxwidth=region_width * 0.5,
                h_align='right',
                v_align='center',
                flatness=1.0,
                text=bui.Lstr(
                    resource='gatherWindow.inviteAFriendText',
                    subs=[('${COUNT}', str(try_tickets))],
                ),
            )
            bui.buttonwidget(
                parent=self._container,
                position=(region_width * 0.59, 10),
                size=(230, 50),
                color=(0.54, 0.42, 0.56),
                textcolor=(0, 1, 0),
                label=bui.Lstr(
                    resource='gatherWindow.inviteFriendsText',
                    fallback_resource='gatherWindow.getFriendInviteCodeText',
                ),
                autoselect=True,
                on_activate_call=bui.WeakCall(self._invite_to_try_press),
                up_widget=tab_button,
            )
        return self._container

    def _invite_to_try_press(self) -> None:
        from bauiv1lib.account import show_sign_in_prompt
        from bauiv1lib.appinvite import handle_app_invites_press

        plus = bui.app.plus
        assert plus is not None

        if plus.get_v1_account_state() != 'signed_in':
            show_sign_in_prompt()
            return
        handle_app_invites_press()
