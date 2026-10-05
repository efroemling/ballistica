# Released under the MIT License. See LICENSE for details.
#
# Auto-generated; do not edit by hand.
"""Asset-package wrapper for ``a-0.baclassicuiassets.261004b`` (bauiv1).

Classic-specific ui text -- and any small art -- that both the game's own ui and
server-rendered pages (store, inventory, profile editor, chests) show: the
economy notices and the player-profile strings. Server pages may reference it,
so it stays small: strings, plus at most a little art.
"""

# ba_meta require api 9
# ba_meta require asset-package 413

# pylint: disable=useless-suppression
# pylint: disable=too-many-lines
# pylint: disable=too-few-public-methods, disallowed-name

from typing import TYPE_CHECKING

from bacommon.assetpackage import ApverNum

from babase import LangStrDir

# a-0.baclassicuiassets.261004b
_ASSET_PACKAGE = ApverNum(413)

if TYPE_CHECKING:
    from babase import LangStr

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

                English: "This special profile has a name and icon based on your
                account. {icons} Create custom profiles to use different names
                or custom icons."
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
        #:     Title of the profile editor's icon picker.
        #:
        #:     English: "Choose Icon"
        choose_icon: LangStr

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
        #:     Small note under the profile on the delete-confirmation page,
        #:     shown only when the profile being deleted is a global profile.
        #:
        #:     English: "Note: to release a global profile you must delete the
        #:     legacy profile"
        delete_global_note: LangStr

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
        #:     English: "Global profiles are guaranteed to have unique names
        #:     worldwide. They also include custom icons."
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
        #:     Confirmation shown briefly after a profile is upgraded to a
        #:     global profile.
        #:
        #:     English: "Upgraded to a global profile."
        profile_upgraded: LangStr

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

        #: ::
        #:
        #:     Error when a global-profile upgrade needs to create a legacy
        #:     profile to hold the name and the account already has the maximum
        #:     number.
        #:
        #:     English: "You have too many legacy profiles; delete one and try
        #:     again."
        too_many_legacy_profiles: LangStr

        def unavailable(self, *, name: str | LangStr) -> LangStr:
            """
            ::

                Status shown when a chosen global name is taken.

                English: ""{name}" is unavailable. Try another name."
            """

        #: ::
        #:
        #:     Error when the price of a global-profile upgrade changed between
        #:     being shown and being bought.
        #:
        #:     English: "The price has changed; please try again."
        upgrade_price_changed: LangStr

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

            Classic ui text that both the game's own ui and server-rendered
            pages (store, inventory, profile editor, chests) show.

            See source for the full asset list.
        """

        economy: StringsEconomyGroup
        profile: StringsProfileGroup
        profiles: StringsProfilesGroup

    #: The ``strings`` group - 52 strings (``economy``, ``profile``,
    #: ``profiles``, and 49 more). Full list in source.
    strings: StringsGroup

_TREE = {
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
            'choose_icon': (),
            'color': (),
            'color_label': (),
            'delete_confirm': ('profile',),
            'delete_global_note': (),
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
            'profile_upgraded': (),
            'purchasing': (),
            'random_name': (),
            'title_edit': (),
            'title_new': (),
            'too_many_legacy_profiles': (),
            'unavailable': ('name',),
            'upgrade_price_changed': (),
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
    }
}


if not TYPE_CHECKING:
    strings = LangStrDir(_ASSET_PACKAGE, _TREE['strings'], 'strings')
