# Released under the MIT License. See LICENSE for details.
#
# Auto-generated; do not edit by hand.
"""Asset-package wrapper for ``a-0.bauiv1assets.261003`` (bauiv1).

Standard ui chrome the ui_v1 widget layer draws itself with -- window backings,
button faces, scroll furniture, the ui atlases -- supplied to ui_v1 by the
active app-mode (see bauiv1.UIAssetSet), so an app-mode can skin the ui by
supplying its own set instead. Also holds a few classic bits server-rendered
pages show that await a better home: plus_button, and the economy and profile
string groups.
"""

# ba_meta require api 9
# ba_meta require asset-package 393

# pylint: disable=useless-suppression
# pylint: disable=too-many-lines
# pylint: disable=too-few-public-methods, disallowed-name

from typing import TYPE_CHECKING

from bacommon.assetpackage import ApverNum

from bauiv1._assetref import AssetGroup

from babase import LangStrDir

# a-0.bauiv1assets.261003
_ASSET_PACKAGE = ApverNum(393)

if TYPE_CHECKING:
    from bauiv1._assetref import MeshHandle, SoundHandle, TextureHandle
    from babase import LangStr

    class AudioGroup:
        """
        ::

            Standard ui interaction sounds -- the widget-layer swishes and
            tickers an app-mode can reskin along with the chrome.

            See source for the full asset list.
        """

        score_increase: SoundHandle
        swish2: SoundHandle
        swish3: SoundHandle

    class MeshesGroup:
        """
        ::

            Standard ui chrome meshes -- the backing geometry the widget layer
            stretches its chrome textures over.

            See source for the full asset list.
        """

        button_back_opaque: MeshHandle
        button_back_small_opaque: MeshHandle
        button_back_small_transparent: MeshHandle
        button_back_transparent: MeshHandle
        button_large_opaque: MeshHandle
        button_large_transparent: MeshHandle
        button_larger_opaque: MeshHandle
        button_larger_transparent: MeshHandle
        button_medium_opaque: MeshHandle
        button_medium_transparent: MeshHandle
        button_small_opaque: MeshHandle
        button_small_transparent: MeshHandle
        button_square_opaque: MeshHandle
        button_square_transparent: MeshHandle
        button_tab_opaque: MeshHandle
        button_tab_transparent: MeshHandle
        check_transparent: MeshHandle
        image1x1: MeshHandle
        scroll_bar_thumb_opaque: MeshHandle
        scroll_bar_thumb_short_opaque: MeshHandle
        scroll_bar_thumb_short_simple: MeshHandle
        scroll_bar_thumb_short_transparent: MeshHandle
        scroll_bar_thumb_simple: MeshHandle
        scroll_bar_thumb_transparent: MeshHandle
        scroll_bar_trough_transparent: MeshHandle
        soft_edge_inside: MeshHandle
        soft_edge_outside: MeshHandle
        text_box_transparent: MeshHandle
        window_hsmall_vmed_opaque: MeshHandle
        window_hsmall_vmed_transparent: MeshHandle
        window_hsmall_vsmall_opaque: MeshHandle
        window_hsmall_vsmall_transparent: MeshHandle

    class StringsEconomyGroup:
        """
        ::

            Screen-messages about currency: grants and related notices. Also
            'Watch an Ad' (rewarded-ad buttons).

            See source for the full asset list.
        """

        def received_tickets(self, *, count: int) -> LangStr:
            """
            ::

                Confirmation of how many tickets were received.

                English: (one) "Received # Ticket!" / (other) "Received #
                Tickets!"
            """

        #: ::
        #:
        #:     Button to watch an ad for tournament entry.
        #:
        #:     English: "Watch an Ad"
        watch_an_ad: LangStr

        def you_got_tokens(self, *, tokens: int) -> LangStr:
            """
            ::

                Confirmation effect sent to game clients when tokens are
                credited (store purchases, promo codes, and other grant flows).

                English: (one) "You got # Token!" / (other) "You got # Tokens!"
            """

    class StringsProfileGroup:
        """
        ::

            Player-profile editor strings: create/edit/delete profiles, the
            local/global/account profile explanations, and global-name upgrade
            flow.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Parenthetical marker labeling the account-based profile.
        #:
        #:     English: "(account profile)"
        account_profile: LangStr

        def account_profile_info(self, *, icons: str | LangStr) -> LangStr:
            """
            ::

                Explanation of what an account profile is.

                English: "This profile uses your account name and icon {icons}.
                Create custom profiles for different names or icons."
            """

        def available(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Status shown when a chosen global name is available.

                English: "The name {name} is available."
            """

        #: ::
        #:
        #:     Error when trying to delete the account profile.
        #:
        #:     English: "You can't delete your account profile."
        cant_delete_account_profile: LangStr

        #: ::
        #:
        #:     Lowercase field label for the profile character.
        #:
        #:     English: "character"
        character: LangStr

        #: ::
        #:
        #:     Field label in the profile editor for the profile's character.
        #:
        #:     English: "Character"
        character_label: LangStr

        def checking_availability(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Status shown while checking global-name availability.

                English: "Checking availability for "{name}"..."
            """

        #: ::
        #:
        #:     Title of the profile editor's character picker.
        #:
        #:     English: "Choose Character"
        choose_character: LangStr

        #: ::
        #:
        #:     Lowercase field label for profile color.
        #:
        #:     English: "color"
        color: LangStr

        #: ::
        #:
        #:     Field label in the profile editor for the profile's main color.
        #:
        #:     English: "Color"
        color_label: LangStr

        def delete_confirm(self, *, profile: str | LangStr) -> LangStr:
            """
            ::

                Confirmation before deleting a named profile.

                English: "Delete '{profile}'?"
            """

        #: ::
        #:
        #:     Button (and menu entry) deleting the player profile being edited.
        #:
        #:     English: "Delete Profile"
        delete_profile: LangStr

        #: ::
        #:
        #:     Question heading the delete-confirmation box, shown above the
        #:     profile being deleted.
        #:
        #:     English: "Delete this profile?"
        delete_this_profile: LangStr

        #: ::
        #:
        #:     Button to get more player characters.
        #:
        #:     English: "Get More Characters..."
        get_more_characters: LangStr

        #: ::
        #:
        #:     Button to get more profile icons.
        #:
        #:     English: "Get More Icons..."
        get_more_icons: LangStr

        #: ::
        #:
        #:     Parenthetical marker labeling a global profile.
        #:
        #:     English: "(global profile)"
        global_profile: LangStr

        #: ::
        #:
        #:     Explanation of global profiles in the edit window.
        #:
        #:     English: "Global player profiles are guaranteed to have unique
        #:     names worldwide. They also include custom icons."
        global_profile_info: LangStr

        #: ::
        #:
        #:     Lowercase field label for profile highlight color.
        #:
        #:     English: "highlight"
        highlight: LangStr

        #: ::
        #:
        #:     Field label in the profile editor for the profile's highlight
        #:     (accent) color.
        #:
        #:     English: "Highlight"
        highlight_label: LangStr

        #: ::
        #:
        #:     Lowercase field label for profile icon.
        #:
        #:     English: "icon"
        icon: LangStr

        #: ::
        #:
        #:     Field label in the profile editor for the profile's icon.
        #:
        #:     English: "Icon"
        icon_label: LangStr

        def in_game_clipped_name(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Preview of how a profile name appears in-game (possibly
                clipped).

                English: "In-game: {name}"
            """

        #: ::
        #:
        #:     Parenthetical marker labeling a local profile.
        #:
        #:     English: "(local profile)"
        local_profile: LangStr

        #: ::
        #:
        #:     Explanation of local profiles in the edit window.
        #:
        #:     English: "Local player profiles have no icons and their names are
        #:     not guaranteed to be unique. Upgrade to a global profile to
        #:     reserve a unique name and add a custom icon."
        local_profile_info: LangStr

        #: ::
        #:
        #:     Label for the profile name input field.
        #:
        #:     English: "Player Name"
        name_description: LangStr

        #: ::
        #:
        #:     Error when the profile name field is empty.
        #:
        #:     English: "Name cannot be empty!"
        name_not_empty: LangStr

        #: ::
        #:
        #:     Error when the player lacks enough tickets for an upgrade.
        #:
        #:     English: "Not enough Tickets!"
        not_enough_tickets: LangStr

        #: ::
        #:
        #:     Error when no item is selected.
        #:
        #:     English: "Nothing is selected!"
        nothing_selected: LangStr

        #: ::
        #:
        #:     Error when a profile name is already taken.
        #:
        #:     English: "A profile with that name already exists."
        profile_already_exists: LangStr

        #: ::
        #:
        #:     Status shown while a purchase is processing.
        #:
        #:     English: "Purchasing..."
        purchasing: LangStr

        #: ::
        #:
        #:     Button in the profile editor filling in a randomly generated
        #:     player name.
        #:
        #:     English: "Random Name"
        random_name: LangStr

        #: ::
        #:
        #:     Title of the edit-profile window.
        #:
        #:     English: "Edit Profile"
        title_edit: LangStr

        #: ::
        #:
        #:     Title of the new-profile window.
        #:
        #:     English: "New Profile"
        title_new: LangStr

        def unavailable(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Status shown when a chosen global name is taken.

                English: ""{name}" is unavailable. Try another name."
            """

        #: ::
        #:
        #:     Explanation shown in the upgrade-to-global window.
        #:
        #:     English: "This will reserve your player name worldwide and allow
        #:     you to assign a custom icon to it."
        upgrade_profile_info: LangStr

        #: ::
        #:
        #:     Button/title to upgrade a profile to global.
        #:
        #:     English: "Upgrade to Global Profile"
        upgrade_to_global: LangStr

    class StringsProfilesGroup:
        """
        ::

            Player-profile management UI: profile lists, creation, and related
            hints.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Single-line parenthetical hint; keep the parentheses.
        #:
        #:     English: "(custom player names and appearances for this account)"
        explanation: LangStr

        #: ::
        #:
        #:     Single-line parenthetical hint under the legacy-profiles heading;
        #:     keep the parentheses.
        #:
        #:     English: "(stored on this device and your legacy account; cloud
        #:     profiles are used when available)"
        legacy_explanation: LangStr

        #: ::
        #:
        #:     Section heading for the locally-stored legacy player profiles on
        #:     the inventory page (shown below or instead of the cloud
        #:     profiles).
        #:
        #:     English: "Legacy Profiles"
        legacy_title: LangStr

        #: ::
        #:
        #:     Error screen-message when creating another player profile would
        #:     exceed the account limit.
        #:
        #:     English: "Max number of profiles reached."
        max_reached: LangStr

        #: ::
        #:
        #:     Button label.
        #:
        #:     English: "New Profile"
        new_profile: LangStr

        #: ::
        #:
        #:     Small toggle-button label on the inventory page switching the
        #:     profile list from legacy profiles back to cloud profiles.
        #:
        #:     English: "Show Cloud Profiles"
        show_cloud_profiles: LangStr

        #: ::
        #:
        #:     Small toggle-button label on the inventory page switching the
        #:     profile list from cloud profiles to legacy profiles.
        #:
        #:     English: "Show Legacy Profiles"
        show_legacy_profiles: LangStr

        #: ::
        #:
        #:     Section heading / window title for player-profile management.
        #:
        #:     English: "Player Profiles"
        title: LangStr

    class StringsGroup:
        """
        ::

            Shared ui vocabulary the game and server-rendered pages (store,
            inbox, profile editor) both show -- character, game and map names
            and descriptions plus the profile and economy strings those pages
            use.

            See source for the full asset list.
        """

        economy: StringsEconomyGroup
        profile: StringsProfileGroup
        profiles: StringsProfilesGroup

    class TexturesGroup:
        """
        ::

            Standard ui chrome textures -- window backings, button faces, scroll
            furniture, the ui atlases.

            See source for the full asset list.
        """

        back_icon: TextureHandle
        bomb_button: TextureHandle
        button_square: TextureHandle
        button_square_wide: TextureHandle
        circle: TextureHandle
        circle_soft: TextureHandle
        glow: TextureHandle
        lock: TextureHandle
        menu_button: TextureHandle
        page_left_right: TextureHandle
        plus_button: TextureHandle
        quote_bubble: TextureHandle
        scroll_widget: TextureHandle
        scroll_widget_glow: TextureHandle
        shadow_sharp: TextureHandle
        spinner: TextureHandle
        spinner0: TextureHandle
        spinner1: TextureHandle
        spinner10: TextureHandle
        spinner11: TextureHandle
        spinner2: TextureHandle
        spinner3: TextureHandle
        spinner4: TextureHandle
        spinner5: TextureHandle
        spinner6: TextureHandle
        spinner7: TextureHandle
        spinner8: TextureHandle
        spinner9: TextureHandle
        start_button: TextureHandle
        text_clear_button: TextureHandle
        tv: TextureHandle
        ui_atlas: TextureHandle
        ui_atlas2: TextureHandle
        users_button: TextureHandle
        white: TextureHandle
        window_hsmall_vmed: TextureHandle
        window_hsmall_vsmall: TextureHandle

    #: The ``audio`` group - 3 assets (``score_increase``, ``swish2``,
    #: ``swish3``). Full list in source.
    audio: AudioGroup

    #: The ``meshes`` group - 32 assets (``button_back_opaque``,
    #: ``button_back_small_opaque``, ``button_back_small_transparent``,
    #: ``button_back_transparent``, ``button_large_opaque``, and 27 more). Full
    #: list in source.
    meshes: MeshesGroup

    #: The ``strings`` group - 47 strings (``economy``, ``profile``,
    #: ``profiles``, and 44 more). Full list in source.
    strings: StringsGroup

    #: The ``textures`` group - 37 assets (``back_icon``, ``bomb_button``,
    #: ``button_square``, ``button_square_wide``, ``circle``, and 32 more). Full
    #: list in source.
    textures: TexturesGroup

_TREE = {
    'audio': {'score_increase': 's', 'swish2': 's', 'swish3': 's'},
    'meshes': {
        'button_back_opaque': 'm',
        'button_back_small_opaque': 'm',
        'button_back_small_transparent': 'm',
        'button_back_transparent': 'm',
        'button_large_opaque': 'm',
        'button_large_transparent': 'm',
        'button_larger_opaque': 'm',
        'button_larger_transparent': 'm',
        'button_medium_opaque': 'm',
        'button_medium_transparent': 'm',
        'button_small_opaque': 'm',
        'button_small_transparent': 'm',
        'button_square_opaque': 'm',
        'button_square_transparent': 'm',
        'button_tab_opaque': 'm',
        'button_tab_transparent': 'm',
        'check_transparent': 'm',
        'image1x1': 'm',
        'scroll_bar_thumb_opaque': 'm',
        'scroll_bar_thumb_short_opaque': 'm',
        'scroll_bar_thumb_short_simple': 'm',
        'scroll_bar_thumb_short_transparent': 'm',
        'scroll_bar_thumb_simple': 'm',
        'scroll_bar_thumb_transparent': 'm',
        'scroll_bar_trough_transparent': 'm',
        'soft_edge_inside': 'm',
        'soft_edge_outside': 'm',
        'text_box_transparent': 'm',
        'window_hsmall_vmed_opaque': 'm',
        'window_hsmall_vmed_transparent': 'm',
        'window_hsmall_vsmall_opaque': 'm',
        'window_hsmall_vsmall_transparent': 'm',
    },
    'strings': {
        'economy': {
            'received_tickets': ('count',),
            'watch_an_ad': (),
            'you_got_tokens': ('tokens',),
        },
        'profile': {
            'account_profile': (),
            'account_profile_info': ('icons',),
            'available': ('name',),
            'cant_delete_account_profile': (),
            'character': (),
            'character_label': (),
            'checking_availability': ('name',),
            'choose_character': (),
            'color': (),
            'color_label': (),
            'delete_confirm': ('profile',),
            'delete_profile': (),
            'delete_this_profile': (),
            'get_more_characters': (),
            'get_more_icons': (),
            'global_profile': (),
            'global_profile_info': (),
            'highlight': (),
            'highlight_label': (),
            'icon': (),
            'icon_label': (),
            'in_game_clipped_name': ('name',),
            'local_profile': (),
            'local_profile_info': (),
            'name_description': (),
            'name_not_empty': (),
            'not_enough_tickets': (),
            'nothing_selected': (),
            'profile_already_exists': (),
            'purchasing': (),
            'random_name': (),
            'title_edit': (),
            'title_new': (),
            'unavailable': ('name',),
            'upgrade_profile_info': (),
            'upgrade_to_global': (),
        },
        'profiles': {
            'explanation': (),
            'legacy_explanation': (),
            'legacy_title': (),
            'max_reached': (),
            'new_profile': (),
            'show_cloud_profiles': (),
            'show_legacy_profiles': (),
            'title': (),
        },
    },
    'textures': {
        'back_icon': 't',
        'bomb_button': 't',
        'button_square': 't',
        'button_square_wide': 't',
        'circle': 't',
        'circle_soft': 't',
        'glow': 't',
        'lock': 't',
        'menu_button': 't',
        'page_left_right': 't',
        'plus_button': 't',
        'quote_bubble': 't',
        'scroll_widget': 't',
        'scroll_widget_glow': 't',
        'shadow_sharp': 't',
        'spinner': 't',
        'spinner0': 't',
        'spinner1': 't',
        'spinner10': 't',
        'spinner11': 't',
        'spinner2': 't',
        'spinner3': 't',
        'spinner4': 't',
        'spinner5': 't',
        'spinner6': 't',
        'spinner7': 't',
        'spinner8': 't',
        'spinner9': 't',
        'start_button': 't',
        'text_clear_button': 't',
        'tv': 't',
        'ui_atlas': 't',
        'ui_atlas2': 't',
        'users_button': 't',
        'white': 't',
        'window_hsmall_vmed': 't',
        'window_hsmall_vsmall': 't',
    },
}


if not TYPE_CHECKING:
    audio = AssetGroup(_ASSET_PACKAGE, _TREE['audio'], 'audio')
    meshes = AssetGroup(_ASSET_PACKAGE, _TREE['meshes'], 'meshes')
    strings = LangStrDir(_ASSET_PACKAGE, _TREE['strings'], 'strings')
    textures = AssetGroup(_ASSET_PACKAGE, _TREE['textures'], 'textures')
