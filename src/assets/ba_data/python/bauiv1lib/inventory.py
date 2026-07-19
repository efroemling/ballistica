# Released under the MIT License. See LICENSE for details.
#
"""Provides help related ui."""

import random

from typing import override, TYPE_CHECKING

from efro.util import asserttype
import bacommon.docui.v2 as dui2
from bacommon.assetref import TextureRef
from bacommon.langstr import LangStrValue
import bauiv1 as bui
from bauiv1 import builtinassets
from bauiv1 import stdassets

from bauiv1lib.docui import DocUIController

if TYPE_CHECKING:
    from typing import Any

    from bacommon.docui import DocUIRequest, DocUIResponse

    from bauiv1lib.docui import DocUILocalAction, DocUIWindow


def _tex_from_qualified(qualified: str) -> TextureRef:
    """Typed ref for a qualified ``<apverid>:<name>`` texture string.

    (Appearance texture fields carry qualified strings; docui v2 wants
    typed refs.)
    """
    apverid, _, name = qualified.partition(':')
    return TextureRef(apverid, name)


class InventoryUIController(DocUIController):
    """DocUI setup for inventory."""

    def __init__(self, player_profiles_only: bool = False) -> None:
        self._next_selected_profile: str | None = None
        self._player_profiles_only = player_profiles_only

    @override
    def fulfill_request(self, request: DocUIRequest) -> DocUIResponse:
        # All local authoring here uses strings from BUNDLED packages
        # (bastdassets/builtin) so these pages keep working offline.
        invstrs = stdassets.strings.inventory
        profstrs = stdassets.strings.profiles

        response: DocUIResponse

        # If we only want player profiles, we can skip the whole cloud
        # request bit.
        if self._player_profiles_only:
            response = dui2.Response(
                page=dui2.Page(
                    title=invstrs.title,
                    rows=[],
                )
            )
        else:
            # *Most* of our inventory comes from the cloud - we just supply
            # profiles ourself so it works offline.
            cloudresponse = self.fulfill_request_cloud(
                request, 'classicinventory'
            )

            assert isinstance(request, dui2.Request)
            if not isinstance(cloudresponse, dui2.Response):
                # A server that doesn't speak v2 for us; show its
                # response as-is (no local additions).
                return cloudresponse
            response = cloudresponse

            if request.path != '/':
                return response

            signed_in = (
                bui.app.plus is not None
                and bui.app.plus.accounts.primary is not None
            )

            # If anything went wrong, replace the error page they sent us with
            # a minimal 'most stuff is only available online' page.
            if response.status is not dui2.ResponseStatus.SUCCESS:
                response = dui2.Response(
                    page=dui2.Page(
                        title=invstrs.title,
                        rows=[
                            dui2.ButtonRow(
                                center_content=True,
                                buttons=[
                                    dui2.Button(
                                        (
                                            invstrs.only_available_signed_in
                                            if not signed_in
                                            else invstrs.only_available_online
                                        ),
                                        texture=builtinassets.textures.white,
                                        size=(600, 100),
                                        color=(1, 1, 1, 0.0),
                                        label_scale=0.7,
                                        label_color=(1, 0.4, 0.4, 0.8),
                                    )
                                ],
                            ),
                        ],
                    ),
                )

        # Wire spawn-bot actions onto any buttons the server marked
        # (structured ids; no display-text sniffing).
        for row in response.page.rows:
            if isinstance(row, dui2.ButtonRow):
                for button in row.buttons:
                    wid = button.widget_id
                    if wid is not None and wid.startswith('spawn_char:'):
                        button.action = dui2.Local(
                            immediate_local_action='spawn_bot',
                            immediate_local_action_args={
                                'name': wid.removeprefix('spawn_char:')
                            },
                        )

        # Now add in our profiles, which we handle locally so it is
        # available offline.
        response.page.rows = [
            dui2.ButtonRow(
                title=profstrs.title,
                subtitle=profstrs.explanation,
                button_spacing=15,
                buttons=self._get_profile_buttons(),
            ),
            dui2.ButtonRow(
                spacing_top=-15,
                spacing_bottom=15,
                padding_left=13,
                buttons=[
                    dui2.Button(
                        profstrs.new_profile,
                        action=dui2.Local(
                            default_sound=False,
                            immediate_local_action='new_profile',
                        ),
                        icon=stdassets.textures.plus_button,
                        icon_scale=1.3,
                        icon_color=(0.7, 0.6, 0.9, 1),
                        style=dui2.ButtonStyle.MEDIUM,
                        size=(210, 60),
                        scale=0.8,
                        color=(0.6, 0.5, 0.8, 1.0),
                        label_color=(1, 1, 1, 1),
                    ),
                ],
            ),
        ] + response.page.rows

        return response

    @override
    def local_action(self, action: DocUILocalAction) -> None:
        if action.name == 'new_profile':
            self._new_profile(action)
        elif action.name == 'edit_profile':
            self._edit_profile(action)
        elif action.name == 'spawn_bot':
            self._spawn_bot(action)
        else:
            bui.screenmessage(
                f'Invalid local-action "{action.name}".', color=(1, 0, 0)
            )
            builtinassets.audio.error.get().play()

    @override
    def restore_window_shared_state(
        self, window: DocUIWindow, state: dict
    ) -> None:
        """Called when a window shared state is being restored."""

        if not isinstance(window.request, dui2.Request):
            return

        # If desired, set the profile button that will be selected in
        # the new window. We do this when coming back from creating a
        # new profile/etc.
        if (
            window.request.path == '/'
            and self._next_selected_profile is not None
        ):
            state['selection'] = f'$(WIN)|profile.{self._next_selected_profile}'

            # Only do this once (return to normal selection save/restore
            # after).
            self._next_selected_profile = None

    def _on_profile_save(self, name: str) -> None:
        # An editor we launched tells us it saved a profile.

        # Have this one selected when we go back to the listing.
        self._next_selected_profile = name
        bui.pushcall(self._notify_profiles_changed)

    def _on_profile_delete(self, name: str) -> None:
        # An editor we launched tells us it deleted a profile.

        # Ask the inventory list to select/show the profile right before
        # the one we're deleting.
        profiles = bui.app.config.get('Player Profiles', {})
        items = list(profiles.items())
        items.sort(key=lambda x: asserttype(x[0], str).lower())

        namelower = name.lower()

        prevname = items[0][0] if items else None
        for item in items:
            if item[0].lower() < namelower:
                prevname = item[0]
            else:
                break

        if prevname is not None:
            self._next_selected_profile = prevname

        self._notify_profiles_changed()

    def _notify_profiles_changed(self) -> None:
        import bascenev1 as bs

        # If there's a team-chooser in existence, tell it the profile-list
        # has probably changed.
        session = bs.get_foreground_host_session()
        if session is not None:
            session.handlemessage(bs.PlayerProfilesChangedMessage())

    def _get_profile_buttons(self) -> list[dui2.Button]:

        plus = bui.app.plus
        assert plus is not None
        classic = bui.app.classic
        assert classic is not None

        buttons: list[dui2.Button] = []

        profiles = bui.app.config.get('Player Profiles', {})
        items = list(profiles.items())
        items.sort(key=lambda x: asserttype(x[0], str).lower())

        account_name: str | None
        if plus.get_v1_account_state() == 'signed_in':
            account_name = plus.get_v1_account_display_string()
        else:
            account_name = None

        spaz_appearances = classic.spaz_appearances
        spaz_appearance_default = spaz_appearances['Spaz']

        for p_name, p_info in items:
            if p_name == '__account__' and account_name is None:
                continue
            color, highlight = classic.get_player_profile_colors(p_name)
            tval = (
                account_name
                if p_name == '__account__'
                else classic.get_player_profile_icon(p_name) + p_name
            )
            assert tval is not None

            tcolor: Any = bui.safecolor(color, 0.4) + (1.0,)
            assert len(tcolor) == 4

            appearance = spaz_appearances.get(p_info['character'])
            if appearance is None:
                appearance = spaz_appearance_default

            buttons.append(
                dui2.Button(
                    texture=builtinassets.textures.white,
                    size=(145, 175),
                    action=dui2.Local(
                        default_sound=False,
                        immediate_local_action='edit_profile',
                        immediate_local_action_args={'profile': p_name},
                    ),
                    # color=(0.6, 0.5, 0.7, 1.0),
                    color=(1, 1, 1, 0.0),
                    widget_id=f'profile.{p_name}',
                    decorations=[
                        dui2.Image(
                            _tex_from_qualified(appearance.icon_texture),
                            position=(0, 15),
                            size=(140, 140),
                            mask_texture=(
                                builtinassets.textures.character_icon_mask
                            ),
                            tint_texture=_tex_from_qualified(
                                appearance.icon_mask_texture
                            ),
                            tint_color=color,
                            tint2_color=highlight,
                        ),
                        dui2.Text(
                            # Raw profile name (+icon glyph); verbatim.
                            LangStrValue(tval),
                            position=(0, -75),
                            size=(130, 40),
                            flatness=1.0,
                            shadow=1.0,
                            color=tcolor,
                        ),
                    ],
                )
            )

        return buttons

    def _new_profile(self, action: DocUILocalAction) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.profile.edit import EditProfileWindow

        builtinassets.audio.swish.get().play()

        plus = bui.app.plus
        assert plus is not None

        # Clamp at 100 profiles (otherwise the server will and that's less
        # elegant looking).
        profiles = bui.app.config.get('Player Profiles', {})
        if len(profiles) > 100:
            bui.screenmessage(
                bui.Lstr(
                    translate=(
                        'serverResponses',
                        'Max number of profiles reached.',
                    )
                ),
                color=(1, 0, 0),
            )
            builtinassets.audio.error.get().play()
            return

        action.window.main_window_replace(
            lambda: EditProfileWindow(
                existing_profile=None,
                on_profile_save=bui.WeakCallPartial(self._on_profile_save),
                on_profile_delete=bui.WeakCallPartial(self._on_profile_delete),
            )
        )

    def _edit_profile(self, action: DocUILocalAction) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.profile.edit import EditProfileWindow

        builtinassets.audio.swish.get().play()

        profile = action.args.get('profile')
        assert isinstance(profile, str)

        # Play a random sound from the character.
        classic = bui.app.classic
        if classic is not None:
            profiles = bui.app.config.get('Player Profiles', {})
            p_info = profiles.get(profile)
            if p_info:
                char = p_info.get('character', 'Spaz')
                appearance = classic.spaz_appearances.get(char)
                if appearance:
                    sounds = (
                        appearance.jump_sounds
                        + appearance.attack_sounds
                        + appearance.pickup_sounds
                    )
                    if sounds:
                        bui.getsound(random.choice(sounds)).play()

        action.window.main_window_replace(
            lambda: EditProfileWindow(
                profile,
                origin_widget=action.widget,
                on_profile_save=bui.WeakCallPartial(self._on_profile_save),
                on_profile_delete=bui.WeakCallPartial(self._on_profile_delete),
            )
        )

    def _spawn_bot(self, action: DocUILocalAction) -> None:
        import bascenev1 as bs
        from bascenev1lib.mainmenu import MainMenuActivity
        from bascenev1lib.actor.spazbot import DemoSpazBotSet, DemoBot
        from bascenev1lib.actor.spazappearance import get_appearances

        name = action.args.get('name')
        assert isinstance(name, str)
        # Modern flow passes the exact internal appearance name (from
        # the server's spawn_char widget-id markers); the legacy scan
        # below also tolerates old Lstr-JSON display strings.

        activity = bs.get_foreground_host_activity()
        if not isinstance(activity, MainMenuActivity) or activity.map is None:
            return
        bounds = activity.map.get_def_bound_box('map_bounds')
        if bounds is None:
            return
        i = 0
        while i < len(activity.bot_sets):
            if activity.bot_sets[i].have_living_bots():
                i += 1
            else:
                activity.bot_sets.pop(i)
        for appearance in get_appearances(True):
            if appearance == name or f'"{appearance}"' in name:
                with activity.context:
                    bot_set = DemoSpazBotSet()
                    DemoBot.randomize_traits(appearance)
                    bot_set.spawn_bot(
                        DemoBot,
                        (
                            (bounds[0] + bounds[3]) / 2 + random.uniform(-7, 7),
                            bounds[4] - 2,
                            (bounds[2] + bounds[5]) / 2 + random.uniform(-7, 7),
                        ),
                        0,
                    )
                activity.bot_sets.append(bot_set)
                break
