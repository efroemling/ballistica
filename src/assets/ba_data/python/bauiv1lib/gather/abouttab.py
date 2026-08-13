# Released under the MIT License. See LICENSE for details.
#
"""Defines the about tab in the gather UI."""

from typing import TYPE_CHECKING, override

from bauiv1lib.gather import GatherTab
import bauiv1 as bui
from bauiv1 import classicassets

if TYPE_CHECKING:
    from bauiv1lib.gather import GatherWindow


class AboutGatherTab(GatherTab):
    """The about tab in the gather UI"""

    @override
    def on_activate(
        self,
        parent_widget: bui.Widget,
        tab_button: bui.Widget,
        region_width: float,
        region_height: float,
        region_left: float,
        region_bottom: float,
    ) -> bui.Widget:
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-positional-arguments

        plus = bui.app.plus
        assert plus is not None

        idprefix = f'{self.window.main_window_id_prefix}|about'

        try_tickets = plus.get_v1_account_misc_read_val(
            'friendTryTickets', None
        )

        show_message = True
        uiscale = bui.app.ui_v1.uiscale
        # Overall squish on the message blocks to fit things at small
        # ui-scale.
        msquish = 0.75 if uiscale is bui.UIScale.SMALL else 1.0
        msc_scale = 1.1 * msquish
        # Let's not talk about sharing in vr-mode; its tricky to fit more
        # than one head in a VR-headset.
        show_message_extra = not bui.app.env.vr
        show_invite = try_tickets is not None
        invite_height = 80
        show_discord = True
        discord_height = 80

        # Each paragraph is its own string drawn as its own block:
        # definition-time wrap pins only apply to top-level strings
        # (nested fragments never wrap themselves), and paragraph gaps
        # come from the block heights here.
        message_blocks: list[tuple[bui.LangStr, float]] = [
            (classicassets.strings.gather.about_intro, 75 * msquish),
            (classicassets.strings.gather.about_parties_info, 110 * msquish),
            (
                classicassets.strings.gather.about_party_button(
                    party=bui.charstr(bui.SpecialChar.PARTY_ICON),
                    button=bui.charstr(bui.SpecialChar.TOP_BUTTON),
                ),
                145 * msquish,
            ),
        ]
        if show_message_extra:
            message_blocks.append(
                (
                    classicassets.strings.gather.about_local_multiplayer_extra,
                    105 * msquish,
                )
            )

        c_height = 0.0
        if show_message:
            c_height += sum(height for _, height in message_blocks)
        if show_invite:
            c_height += invite_height
        if show_discord:
            c_height += discord_height

        scroll_widget = bui.scrollwidget(
            parent=parent_widget,
            position=(region_left, region_bottom),
            size=(region_width, region_height),
            highlight=False,
            border_opacity=0,
        )

        container = bui.containerwidget(
            parent=scroll_widget,
            position=(
                region_left,
                region_bottom + (region_height - c_height) * 0.5,
            ),
            size=(region_width, c_height),
            background=False,
            selectable=show_invite or show_discord,
        )
        # Allows escaping if we select the container somehow (though
        # shouldn't be possible when buttons are present).
        bui.widget(edit=container, up_widget=tab_button)

        y = c_height - 30
        if show_message:
            for block_text, block_height in message_blocks:
                bui.textwidget(
                    parent=container,
                    position=(region_width * 0.5, y),
                    color=(0.6, 1.0, 0.6),
                    scale=msc_scale,
                    size=(0, 0),
                    maxwidth=region_width * 0.9,
                    max_height=block_height,
                    h_align='center',
                    v_align='top',
                    text=block_text,
                )
                y -= block_height

        if show_invite:
            bui.textwidget(
                parent=container,
                position=(region_width * 0.57, y),
                color=(0, 1, 0),
                scale=0.6,
                size=(0, 0),
                maxwidth=region_width * 0.5,
                h_align='right',
                v_align='center',
                flatness=1.0,
                text=classicassets.strings.gather.invite_a_friend(
                    count=str(try_tickets)
                ),
            )
            invite_button = bui.buttonwidget(
                parent=container,
                id=f'{idprefix}|invitefriend',
                position=(region_width * 0.59, y - 25),
                size=(230, 50),
                color=(0.54, 0.42, 0.56),
                textcolor=(0, 1, 0),
                label=classicassets.strings.gather.invite_friends,
                autoselect=True,
                on_activate_call=bui.WeakCallStrict(self._invite_to_try_press),
                up_widget=tab_button,
                show_buffer_top=500,
            )
            y -= invite_height
        else:
            invite_button = None

        if show_discord:
            bui.textwidget(
                parent=container,
                position=(region_width * 0.57, y),
                color=(0.6, 0.6, 1),
                scale=0.6,
                size=(0, 0),
                maxwidth=region_width * 0.5,
                h_align='right',
                v_align='center',
                flatness=1.0,
                text=classicassets.strings.gather.discord_friends,
            )
            discord_button = bui.buttonwidget(
                parent=container,
                id=f'{idprefix}|discordjoin',
                position=(region_width * 0.59, y - 25),
                size=(230, 50),
                color=(0.54, 0.42, 0.56),
                textcolor=(0.6, 0.6, 1),
                label=classicassets.strings.gather.discord_join,
                autoselect=True,
                on_activate_call=bui.WeakCallStrict(
                    self._join_the_discord_press
                ),
                up_widget=(
                    invite_button if invite_button is not None else tab_button
                ),
            )
            y -= discord_height
        else:
            discord_button = None

        if discord_button is not None:
            pass

        return scroll_widget

    def _invite_to_try_press(self) -> None:
        from bauiv1lib.account.signin import show_sign_in_prompt
        from bauiv1lib.appinvite import handle_app_invites_press

        plus = bui.app.plus
        assert plus is not None

        if plus.get_v1_account_state() != 'signed_in':
            show_sign_in_prompt()
            return
        handle_app_invites_press()

    def _join_the_discord_press(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.discord import DiscordWindow

        assert bui.app.classic is not None
        DiscordWindow().get_root_widget()
