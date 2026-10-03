# Released under the MIT License. See LICENSE for details.
#
"""Provides help related ui."""

import random
from dataclasses import replace
from typing import override, assert_never, TYPE_CHECKING

from efro.util import asserttype
import bacommon.docui.v2 as dui2
import bacommon.docui.routes.classicstore as sroutes
from bacommon.assetspec import TextureSpec
from bacommon.assetpackage import ApverNum
from bacommon.langstr import LangStrSpecValue
import bauiv1 as bui
from bascenev1lib.actor import spazappearance
from bauiv1 import _builtinassets
from bauiv1 import (
    _classicassets,
    _commonassets,
    _uiv1assets,
    _classiccatalogassets,
)

from bauiv1lib.docui import TypedDocUIController

if TYPE_CHECKING:
    from typing import Any

    import bacommon.docui.v2
    import bacommon.docui.routes.classicstore
    from bacommon.docui import DocUIResponse
    from bacommon.langstr import LangStrSpec

    from bauiv1lib.docui import DocUILocalAction, DocUIWindow


def _tex_from_qualified(qualified: str) -> TextureSpec:
    """Typed ref for a qualified ``<apvernum>:<name>`` texture string.

    (Appearance texture fields carry qualified strings; docui v2 wants
    typed refs.)
    """
    apvernum, _, name = qualified.partition(':')
    return TextureSpec(ApverNum(int(apvernum)), name)


class InventoryUIController(
    TypedDocUIController[sroutes.AnyStoreRoute, sroutes.AnyInventoryLocalAction]
):
    """DocUI setup for inventory.

    Player profiles come in two flavors here. *Cloud profiles* are
    stored on the v2 master server and the server renders their rows
    and editor into the inventory page itself. *Legacy profiles* are
    the local-config ones (synced via the v1 account); their rows are
    spliced in client-side so they work offline. We show cloud
    profiles by default and switch to legacy when the user asks
    (``show_legacy_profiles``) or when the cloud page can't be fetched.
    """

    def __init__(self, player_profiles_only: bool = False) -> None:
        self._next_selected_profile: str | None = None
        self._player_profiles_only = player_profiles_only
        self._legacy_profiles = False

    @override
    @classmethod
    def get_route_type(
        cls,
    ) -> type[bacommon.docui.routes.classicstore.StoreRoute]:
        return sroutes.StoreRoute

    @override
    @classmethod
    def get_local_action_type(
        cls,
    ) -> type[bacommon.docui.routes.classicstore.InventoryLocalAction]:
        return sroutes.InventoryLocalAction

    @override
    def get_cache_key_extra(self) -> str | None:
        # We serve entirely different pages depending on these -- from
        # the same '/' request path -- so they have to partition the
        # cache.
        return (
            f'profilesonly={self._player_profiles_only}'
            f' legacy={self._legacy_profiles}'
        )

    @override
    def fulfill_route(
        self, route: bacommon.docui.routes.classicstore.AnyStoreRoute
    ) -> DocUIResponse:
        # All local authoring here uses strings from BUNDLED packages
        # (baclassicassets/builtin) so these pages keep working offline.
        invstrs = _classicassets.strings.inventory
        profstrs = _uiv1assets.strings.profiles

        response: DocUIResponse
        cloud_ok = False

        if self._player_profiles_only and self._legacy_profiles:
            # Legacy profiles alone need no cloud at all.
            response = dui2.Response(
                page=dui2.Page(title=profstrs.title.spec, rows=[])
            )
        else:
            # The rest of our inventory (and, for new-enough servers,
            # our cloud profiles) comes from the cloud. The root page
            # takes flags for which flavor we want; the profile editor
            # pages carry their own args and pass through untouched.
            cloudroute = route
            if isinstance(route, sroutes.Root):
                cloudroute = replace(
                    route,
                    legacy_profiles=self._legacy_profiles,
                    profiles_only=self._player_profiles_only,
                )
            cloudresponse = self.fulfill_request_cloud(
                cloudroute, 'classicinventory'
            )

            if not isinstance(cloudresponse, dui2.Response):
                # A server that doesn't speak v2 for us; show its
                # response as-is (no local additions).
                return cloudresponse
            response = cloudresponse

            if not isinstance(route, sroutes.Root):
                return response

            cloud_ok = response.status is dui2.ResponseStatus.SUCCESS

            # If anything went wrong, replace the error page they sent
            # us with a minimal placeholder page saying why the rest of
            # the inventory isn't here (or just an empty profiles page)
            # and fall back to legacy profiles below.
            if not cloud_ok:
                signed_in = (
                    bui.app.plus is not None
                    and bui.app.plus.accounts.primary is not None
                )
                # Say why, by the response's status. The server declining
                # us as too old comes first: it's definitive, and signing
                # in wouldn't help. Then not signed in, the cloud
                # unreachable (our own error page), or anything else.
                status = response.status
                ustat = _commonassets.strings.status
                offline_msg: LangStrSpec
                if status is dui2.ResponseStatus.NEED_UPDATE_ERROR or (
                    response.minimum_engine_build is not None
                    and response.minimum_engine_build
                    > bui.app.env.engine_build_number
                ):
                    offline_msg = ustat.need_update.spec
                elif (
                    not signed_in
                    or status is dui2.ResponseStatus.NOT_SIGNED_IN_ERROR
                ):
                    offline_msg = invstrs.only_available_signed_in.spec
                elif status is dui2.ResponseStatus.COMMUNICATION_ERROR:
                    offline_msg = invstrs.only_available_online.spec
                else:
                    offline_msg = ustat.error_occurred.spec
                offline_rows: list[dui2.Row] = [
                    dui2.ButtonRow(
                        center_content=True,
                        buttons=[
                            dui2.Button(
                                offline_msg,
                                texture=_builtinassets.textures.white,
                                size=(600, 100),
                                color=(1, 1, 1, 0.0),
                                label_scale=0.7,
                                label_color=(1, 0.4, 0.4, 0.8),
                            )
                        ],
                    ),
                ]
                response = dui2.Response(
                    page=dui2.Page(
                        title=(
                            profstrs.title.spec
                            if self._player_profiles_only
                            else invstrs.title.spec
                        ),
                        rows=[] if self._player_profiles_only else offline_rows,
                    ),
                )

        # (Spawn-bot actions on character buttons come wired up from the
        # server these days; see bacommon.docui.routes.classicstore.)

        # Splice in our legacy profiles when they were asked for, or
        # when the cloud page (and thus cloud profiles) is unavailable.
        if self._legacy_profiles or not cloud_ok:
            response.page.rows = (
                self._get_legacy_profile_rows(show_cloud_toggle=cloud_ok)
                + response.page.rows
            )

        return response

    def _get_legacy_profile_rows(
        self, *, show_cloud_toggle: bool
    ) -> list[dui2.Row]:
        """Rows for our locally-authored legacy profiles section."""
        profstrs = _uiv1assets.strings.profiles

        buttons = [
            dui2.Button(
                profstrs.new_profile.spec,
                action=sroutes.NewProfile().local(),
                icon=_uiv1assets.textures.plus_button,
                icon_scale=1.3,
                icon_color=(0.7, 0.6, 0.9, 1),
                style=dui2.ButtonStyle.MEDIUM,
                size=(210, 60),
                scale=0.8,
                color=(0.6, 0.5, 0.8, 1.0),
                label_color=(1, 1, 1, 1),
            ),
        ]
        if show_cloud_toggle:
            # Small and translucent (wide-square art at 15% opacity),
            # tinted slightly purple, so it reads as a secondary option.
            #
            # Keep in lockstep with the server-rendered 'Show Legacy
            # Profiles' button (bamaster classic/profileui.py): same
            # look, and the SAME widget_id -- selection is restored by
            # id across the view switch (see _set_legacy_profiles), so
            # matching ids keep the toggle selected when jumping back
            # and forth.
            buttons.append(
                dui2.Button(
                    profstrs.show_cloud_profiles.spec,
                    action=sroutes.ShowCloudProfiles().local(),
                    texture=_uiv1assets.textures.button_square_wide,
                    size=(338, 70),
                    scale=0.5,
                    color=(0.9, 0.8, 1.0, 0.15),
                    label_color=(0.85, 0.85, 0.9, 1),
                    widget_id='profiles_toggle',
                )
            )

        return [
            dui2.ButtonRow(
                title=profstrs.legacy_title.spec,
                subtitle=profstrs.legacy_explanation.spec,
                button_spacing=15,
                buttons=self._get_profile_buttons(),
            ),
            dui2.ButtonRow(
                spacing_top=-15,
                spacing_bottom=15,
                padding_left=13,
                buttons=buttons,
            ),
        ]

    @override
    def fulfill_unrouted_request(
        self, request: bacommon.docui.v2.Request, error: str
    ) -> DocUIResponse:
        # Something newer than us from the server; let it handle it.
        return self.fulfill_request_cloud(request, 'classicinventory')

    @override
    def run_local_action(
        self,
        action: bacommon.docui.routes.classicstore.AnyInventoryLocalAction,
        context: DocUILocalAction,
    ) -> None:
        match action:
            case sroutes.NewProfile():
                self._new_profile(context)
            case sroutes.EditProfile():
                self._edit_profile(action, context)
            case sroutes.SpawnBot():
                self._spawn_bot(action)
            case sroutes.ShowLegacyProfiles():
                self._set_legacy_profiles(context, True)
            case sroutes.ShowCloudProfiles():
                self._set_legacy_profiles(context, False)
            case _:
                assert_never(action)

    @override
    def restore_window_shared_state(
        self, window: DocUIWindow, state: dict
    ) -> None:
        """Called when a window shared state is being restored."""

        # If desired, set the profile button that will be selected in
        # the new window. We do this when coming back from creating a
        # new profile/etc.
        if (
            isinstance(self.get_window_route(window), sroutes.Root)
            and self._next_selected_profile is not None
        ):
            state['selection'] = f'$(WIN)|profile.{self._next_selected_profile}'

            # Only do this once (return to normal selection save/restore
            # after).
            self._next_selected_profile = None

    def _set_legacy_profiles(
        self, action: DocUILocalAction, legacy: bool
    ) -> None:
        """Switch the root page between cloud and legacy profiles."""
        self._legacy_profiles = legacy
        # Save selection first so the rebuilt page re-selects the
        # toggle: both flavors' toggle buttons share one widget_id
        # ('profiles_toggle'), and the window restores selection by id
        # once the new page is built. (The stock Replace action does
        # this save for us; a local action has to do it itself.)
        action.window.main_window_save_shared_state()
        # Re-fetch the root page in the new flavor (the cache is keyed
        # on the flavor, so this never shows the other one).
        self.replace(
            action.window, action.window.request, origin_widget=action.widget
        )

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

            # Profiles aren't guaranteed a character entry (the
            # account profile and older/hand-edited configs can lack
            # one); treat that like an unknown character.
            appearance = spaz_appearances.get(p_info.get('character', 'Spaz'))
            if appearance is None:
                appearance = spaz_appearance_default

            buttons.append(
                dui2.Button(
                    texture=_builtinassets.textures.white,
                    size=(145, 175),
                    action=sroutes.EditProfile(profile=p_name).local(),
                    # color=(0.6, 0.5, 0.7, 1.0),
                    color=(1, 1, 1, 0.0),
                    widget_id=f'profile.{p_name}',
                    decorations=[
                        dui2.Image(
                            spazappearance.texture_spec(
                                appearance.icon_texture
                            ),
                            position=(0, 15),
                            size=(140, 140),
                            mask_texture=(
                                (
                                    _classiccatalogassets.textures
                                ).character_icon_mask
                            ),
                            tint_texture=spazappearance.texture_spec(
                                appearance.icon_mask_texture
                            ),
                            tint_color=color,
                            tint2_color=highlight,
                        ),
                        dui2.Text(
                            # Raw profile name (+icon glyph); the
                            # literal form brace-escapes so a name
                            # like '{test}' displays verbatim instead
                            # of erroring as a substitution token.
                            LangStrSpecValue.literal(tval),
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

        plus = bui.app.plus
        assert plus is not None

        # Clamp at 100 profiles (otherwise the server will and that's less
        # elegant looking).
        profiles = bui.app.config.get('Player Profiles', {})
        if len(profiles) > 100:
            bui.screenmessage(
                _uiv1assets.strings.profiles.max_reached,
                color=(1, 0, 0),
            )
            _builtinassets.audio.error.get().play()
            return

        action.window.main_window_replace(
            lambda: EditProfileWindow(
                existing_profile=None,
                on_profile_save=bui.WeakCallPartial(self._on_profile_save),
                on_profile_delete=bui.WeakCallPartial(self._on_profile_delete),
            )
        )

    def _edit_profile(
        self,
        editaction: bacommon.docui.routes.classicstore.EditProfile,
        action: DocUILocalAction,
    ) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.profile.edit import EditProfileWindow

        profile = editaction.profile

        # Play a random sound from the character.
        classic = bui.app.classic
        if classic is not None:
            profiles = bui.app.config.get('Player Profiles', {})
            p_info = profiles.get(profile)
            if p_info:
                char = p_info.get('character', 'Spaz')
                appearance = classic.spaz_appearances.get(char)
                if appearance:
                    sounds = [
                        *appearance.jump_sounds,
                        *appearance.attack_sounds,
                        *appearance.pickup_sounds,
                    ]
                    if sounds:
                        spazappearance.ui_sound(random.choice(sounds)).play()

        action.window.main_window_replace(
            lambda: EditProfileWindow(
                profile,
                origin_widget=action.widget,
                on_profile_save=bui.WeakCallPartial(self._on_profile_save),
                on_profile_delete=bui.WeakCallPartial(self._on_profile_delete),
            )
        )

    def _spawn_bot(
        self, action: bacommon.docui.routes.classicstore.SpawnBot
    ) -> None:
        import bascenev1 as bs
        from bascenev1lib.mainmenu import MainMenuActivity
        from bascenev1lib.actor.spazbot import DemoSpazBotSet, DemoBot
        from bascenev1lib.actor.spazappearance import get_appearances

        # Modern flow passes the exact internal appearance name; the
        # legacy scan below also tolerates old Lstr-JSON display
        # strings.
        name = action.name

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
