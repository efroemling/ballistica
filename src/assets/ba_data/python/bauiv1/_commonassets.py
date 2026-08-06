# Released under the MIT License. See LICENSE for details.
#
# Auto-generated; do not edit by hand.
"""Asset-package wrapper for ``a-0.bacommonassets.260806`` (bauiv1).

Cross-cutting assets used everywhere -- by the engine, by every game built on
it, and by the master server's own web pages. Content here must be free of any
single game's concepts, which is what distinguishes it from BaClassicAssets.
"""

# ba_meta require api 9
# ba_meta require asset-package a-0.bacommonassets.260806

# pylint: disable=useless-suppression
# pylint: disable=too-many-lines
# pylint: disable=too-few-public-methods, disallowed-name

__asset_package__ = 'a-0.bacommonassets.260806'

from typing import TYPE_CHECKING

from babase import LangStrDir

if TYPE_CHECKING:
    from babase import LangStr

    class StringsActionsGroup:
        """
        ::

            Title-cased labels for things the user activates: buttons, menu
            items, links that perform an action. They are styled as labels, NOT
            as prose -- do not substitute one into the middle of a sentence
            (author a dedicated string for that instead).

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Button label to accept an offer or invitation.
        #:
        #:     English: "Accept"
        accept: LangStr

        #: ::
        #:
        #:     Generic "Apply" button label.
        #:
        #:     English: "Apply"
        apply: LangStr

        #: ::
        #:
        #:     Generic back-navigation button label.
        #:
        #:     English: "Back"
        back: LangStr

        #: ::
        #:
        #:     Abort button label; backs out of a dialog or in-progress action
        #:     without applying anything. NOT a "no" answer to a question and
        #:     not "back" navigation.
        #:
        #:     English: "Cancel"
        cancel: LangStr

        #: ::
        #:
        #:     Confirmation label; commits a pending action (purchases and other
        #:     are-you-sure moments). Appears on commit buttons and as
        #:     confirm-dialog titles. Stronger than "ok" — implies something
        #:     happens as a result.
        #:
        #:     English: "Confirm"
        confirm: LangStr

        #: ::
        #:
        #:     Generic "Connect" button label.
        #:
        #:     English: "Connect"
        connect: LangStr

        #: ::
        #:
        #:     Generic "Continue" button label.
        #:
        #:     English: "Continue"
        continue_: LangStr

        #: ::
        #:
        #:     Generic copy-to-clipboard button label.
        #:
        #:     English: "Copy"
        copy: LangStr

        #: ::
        #:
        #:     Generic "Customize..." button label.
        #:
        #:     English: "Customize..."
        customize: LangStr

        #: ::
        #:
        #:     Button label to decline an offer or invitation.
        #:
        #:     English: "Decline"
        decline: LangStr

        #: ::
        #:
        #:     Generic "Delete" button label.
        #:
        #:     English: "Delete"
        delete: LangStr

        #: ::
        #:
        #:     Button label to discard something.
        #:
        #:     English: "Discard"
        discard: LangStr

        #: ::
        #:
        #:     Completion button label; closes a screen or flow the user has
        #:     finished working in. Implies completed work — not a generic
        #:     "close" or "back".
        #:
        #:     English: "Done"
        done: LangStr

        #: ::
        #:
        #:     Generic "Duplicate" button label.
        #:
        #:     English: "Duplicate"
        duplicate: LangStr

        #: ::
        #:
        #:     Generic "Edit" button label.
        #:
        #:     English: "Edit"
        edit: LangStr

        #: ::
        #:
        #:     Generic "Enter" button label.
        #:
        #:     English: "Enter"
        enter: LangStr

        #: ::
        #:
        #:     Generic "Filter" label.
        #:
        #:     English: "Filter"
        filter: LangStr

        #: ::
        #:
        #:     Button label to ignore something.
        #:
        #:     English: "Ignore"
        ignore: LangStr

        #: ::
        #:
        #:     Generic "Import" button label.
        #:
        #:     English: "Import"
        import_: LangStr

        #: ::
        #:
        #:     Generic "Learn More" button label.
        #:
        #:     English: "Learn More"
        learn_more: LangStr

        #: ::
        #:
        #:     Generic "More..." label for expanding a list or seeing additional
        #:     items.
        #:
        #:     English: "More..."
        more: LangStr

        #: ::
        #:
        #:     Generic "Not Now" dismiss button.
        #:
        #:     English: "Not Now"
        not_now: LangStr

        #: ::
        #:
        #:     Generic affirmative/acknowledge button label; dismisses a dialog
        #:     or message with agreement. NOT a "yes" answer to a question (use
        #:     a dedicated yes/no pair for those).
        #:
        #:     English: "Ok"
        ok: LangStr

        #: ::
        #:
        #:     Generic "Other..." option label.
        #:
        #:     English: "Other..."
        other: LangStr

        #: ::
        #:
        #:     Generic "Rename" button label.
        #:
        #:     English: "Rename"
        rename: LangStr

        #: ::
        #:
        #:     Generic reset-to-defaults button label.
        #:
        #:     English: "Reset"
        reset: LangStr

        #: ::
        #:
        #:     Button label to restart an activity.
        #:
        #:     English: "Restart"
        restart: LangStr

        #: ::
        #:
        #:     Button label.
        #:
        #:     English: "Retry"
        retry: LangStr

        #: ::
        #:
        #:     Generic save-changes button label.
        #:
        #:     English: "Save"
        save: LangStr

        #: ::
        #:
        #:     Generic "Select" button label.
        #:
        #:     English: "Select"
        select: LangStr

        #: ::
        #:
        #:     Generic "Select..." button label.
        #:
        #:     English: "Select..."
        select_ellipsis: LangStr

        #: ::
        #:
        #:     Generic "Send" button label.
        #:
        #:     English: "Send"
        send: LangStr

        #: ::
        #:
        #:     Generic "Share" button label.
        #:
        #:     English: "Share"
        share: LangStr

        #: ::
        #:
        #:     Generic "Show" button label.
        #:
        #:     English: "Show"
        show: LangStr

        #: ::
        #:
        #:     Generic "Submit" button label.
        #:
        #:     English: "Submit"
        submit: LangStr

        #: ::
        #:
        #:     Generic "Upgrade" button label.
        #:
        #:     English: "Upgrade"
        upgrade: LangStr

    class StringsComposeGroup:
        """
        ::

            Layout primitives: pure-substitution templates for assembling other
            strings (wrapping in parentheses, joining a pair, appending an
            ellipsis). They carry no vocabulary of their own, so what they hold
            is punctuation and word order -- which is exactly the part that
            varies by language.

            See source for the full asset list.
        """

        def angle_button_suffix(
            self, *, main: str | LangStr, button: str | LangStr
        ) -> LangStr:
            """
            ::

                Pure-formatting template appending an angle-bracketed button
                hint to a prompt; substitution-only.

                English: "{main} < {button} >"
            """

        def dash_wrap(self, *, main: str | LangStr) -> LangStr:
            """
            ::

                Pure-formatting template flanking a label with dashes;
                substitution-only.

                English: "- {main} -"
            """

        def data_size(self, *, size: int) -> LangStr:
            """
            ::

                A bare human-readable data size (the value alone, no surrounding
                words) for value-position slots: table cells, size readouts,
                storage meters. Rendered through the data_size display
                formatter, so every locale gets its own units and decimal mark.

                English: "{size}"
            """

        def ellipsis_suffix(self, *, main: str | LangStr) -> LangStr:
            """
            ::

                Pure-formatting template appending an ellipsis to a status
                label; substitution-only.

                English: "{main}..."
            """

        def gapped_pair(
            self, *, first: str | LangStr, second: str | LangStr
        ) -> LangStr:
            """
            ::

                Pure-formatting template joining two labels with a wide gap;
                substitution-only.

                English: "{first} {second}"
            """

        def heading_suffix(self, *, main: str | LangStr) -> LangStr:
            """
            ::

                Pure-formatting template appending a colon to a heading label;
                substitution-only.

                English: "{main}:"
            """

        def icon_label(
            self, *, icon: str | LangStr, label: str | LangStr
        ) -> LangStr:
            """
            ::

                Pure-formatting template joining an icon glyph and a text label
                with a space; substitution-only.

                English: "{icon} {label}"
            """

        def line_pair(
            self, *, first: str | LangStr, second: str | LangStr
        ) -> LangStr:
            """
            ::

                Pure-formatting template stacking two labels on separate lines;
                substitution-only.

                English: "{first} {second}"
            """

        def or_join(self, *, a: str | LangStr, b: str | LangStr) -> LangStr:
            """
            ::

                Joiner between exactly two complete pre-rendered alternatives
                (e.g. a price payable in either of two currencies: "500 tickets
                or 10 tokens"). Not for lists of three or more and not a
                standalone "or" word.

                English: "{a} or {b}"
            """

        def paren_suffix(
            self, *, main: str | LangStr, note: str | LangStr
        ) -> LangStr:
            """
            ::

                Pure-formatting template appending a parenthesized note to a
                main label; substitution-only.

                English: "{main} ({note})"
            """

        def parenthesized(self, *, note: str | LangStr) -> LangStr:
            """
            ::

                Pure-formatting template wrapping a whole value in parentheses;
                substitution-only.

                English: "({note})"
            """

        def spaced_pair(
            self, *, first: str | LangStr, second: str | LangStr
        ) -> LangStr:
            """
            ::

                Pure-formatting template joining two labels with a space;
                substitution-only.

                English: "{first} {second}"
            """

    class StringsLocalesGroup:
        """
        ::

            Language names, one per supported locale, translated into every
            locale. The counterpart to LocaleResolved.endonym (which gives a
            language's name in its own language): a picker shows "<endonym>
            (<name in the current language>)" so a user can find their language
            whatever the ui is set to, and recognize languages whose endonym
            they cannot read. Keyed by the locale's short value.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Name of the Arabic language (endonym: العربية), for language
        #:     pickers.
        #:
        #:     English: "Arabic"
        arabc: LangStr

        #: ::
        #:
        #:     Name of the Belarussian language (endonym: Беларуская), for
        #:     language pickers.
        #:
        #:     English: "Belarusian"
        blrs: LangStr

        #: ::
        #:
        #:     Name of the Chinese (Simplified) language (endonym: 简体中文), for
        #:     language pickers.
        #:
        #:     English: "Chinese (Simplified)"
        chn_sim: LangStr

        #: ::
        #:
        #:     Name of the Chinese (Traditional) language (endonym: 繁體中文), for
        #:     language pickers.
        #:
        #:     English: "Chinese (Traditional)"
        chn_tr: LangStr

        #: ::
        #:
        #:     Name of the Croatian language (endonym: Hrvatski), for language
        #:     pickers.
        #:
        #:     English: "Croatian"
        croat: LangStr

        #: ::
        #:
        #:     Name of the Czech language (endonym: Čeština), for language
        #:     pickers.
        #:
        #:     English: "Czech"
        czch: LangStr

        #: ::
        #:
        #:     Name of the Danish language (endonym: Dansk), for language
        #:     pickers.
        #:
        #:     English: "Danish"
        dnsh: LangStr

        #: ::
        #:
        #:     Name of the Dutch language (endonym: Nederlands), for language
        #:     pickers.
        #:
        #:     English: "Dutch"
        dtch: LangStr

        #: ::
        #:
        #:     Name of the English language (endonym: English), for language
        #:     pickers.
        #:
        #:     English: "English"
        eng: LangStr

        #: ::
        #:
        #:     Name of the Esperanto language (endonym: Esperanto), for language
        #:     pickers.
        #:
        #:     English: "Esperanto"
        esprnto: LangStr

        #: ::
        #:
        #:     Name of the Filipino language (endonym: Wikang Pilipino), for
        #:     language pickers.
        #:
        #:     English: "Filipino"
        filp: LangStr

        #: ::
        #:
        #:     Name of the French language (endonym: Français), for language
        #:     pickers.
        #:
        #:     English: "French"
        frnch: LangStr

        #: ::
        #:
        #:     Name of the Gibberish (imaginary words vaguely reminiscent of
        #:     English; translated phrases should be roughly 150%-200% as long
        #:     as the English versions) language (endonym: Abuktarika), for
        #:     language pickers.
        #:
        #:     English: "Gibberish"
        gibber: LangStr

        #: ::
        #:
        #:     Name of the Greek language (endonym: Ελληνικά), for language
        #:     pickers.
        #:
        #:     English: "Greek"
        greek: LangStr

        #: ::
        #:
        #:     Name of the German language (endonym: Deutsch), for language
        #:     pickers.
        #:
        #:     English: "German"
        grmn: LangStr

        #: ::
        #:
        #:     Name of the Hindi language (endonym: हिंदी), for language
        #:     pickers.
        #:
        #:     English: "Hindi"
        hndi: LangStr

        #: ::
        #:
        #:     Name of the Hungarian language (endonym: Magyar), for language
        #:     pickers.
        #:
        #:     English: "Hungarian"
        hngr: LangStr

        #: ::
        #:
        #:     Name of the Indonesian language (endonym: Bahasa Indonesia), for
        #:     language pickers.
        #:
        #:     English: "Indonesian"
        indnsn: LangStr

        #: ::
        #:
        #:     Name of the Italian language (endonym: Italiano), for language
        #:     pickers.
        #:
        #:     English: "Italian"
        italn: LangStr

        #: ::
        #:
        #:     Name of the Japanese language (endonym: 日本語), for language
        #:     pickers.
        #:
        #:     English: "Japanese"
        jpn: LangStr

        #: ::
        #:
        #:     Name of the Kazakh language (endonym: Қазақша), for language
        #:     pickers.
        #:
        #:     English: "Kazakh"
        kazk: LangStr

        #: ::
        #:
        #:     Name of the Korean language (endonym: 한국어), for language pickers.
        #:
        #:     English: "Korean"
        kor: LangStr

        #: ::
        #:
        #:     Name of the Malay language (endonym: Melayu), for language
        #:     pickers.
        #:
        #:     English: "Malay"
        mlay: LangStr

        #: ::
        #:
        #:     Name of the Persian language (endonym: فارسی), for language
        #:     pickers.
        #:
        #:     English: "Persian"
        pers: LangStr

        #: ::
        #:
        #:     Name of the Pirate-Speak (English as spoken by a pirate) language
        #:     (endonym: Pirate Speak), for language pickers.
        #:
        #:     English: "Pirate Speak"
        pirate: LangStr

        #: ::
        #:
        #:     Name of the Polish language (endonym: Polski), for language
        #:     pickers.
        #:
        #:     English: "Polish"
        pol: LangStr

        #: ::
        #:
        #:     Name of the Portuguese (Brazil) language (endonym: Português -
        #:     Brasil), for language pickers.
        #:
        #:     English: "Portuguese (Brazil)"
        prtg_brz: LangStr

        #: ::
        #:
        #:     Name of the Portuguese (Portugal) language (endonym: Português -
        #:     Portugal), for language pickers.
        #:
        #:     English: "Portuguese (Portugal)"
        prtg_pr: LangStr

        #: ::
        #:
        #:     Name of the Romanian language (endonym: Română), for language
        #:     pickers.
        #:
        #:     English: "Romanian"
        rom: LangStr

        #: ::
        #:
        #:     Name of the Russian language (endonym: Русский), for language
        #:     pickers.
        #:
        #:     English: "Russian"
        rusn: LangStr

        #: ::
        #:
        #:     Name of the Slovak language (endonym: Slovenčina), for language
        #:     pickers.
        #:
        #:     English: "Slovak"
        slvk: LangStr

        #: ::
        #:
        #:     Name of the Spanish (Latin America) language (endonym: Español -
        #:     Latinoamérica), for language pickers.
        #:
        #:     English: "Spanish (Latin America)"
        spn_lat: LangStr

        #: ::
        #:
        #:     Name of the Spanish (Spain) language (endonym: Español - España),
        #:     for language pickers.
        #:
        #:     English: "Spanish (Spain)"
        spn_spn: LangStr

        #: ::
        #:
        #:     Name of the Serbian language (endonym: Српски), for language
        #:     pickers.
        #:
        #:     English: "Serbian"
        srbn: LangStr

        #: ::
        #:
        #:     Name of the Swedish language (endonym: Svenska), for language
        #:     pickers.
        #:
        #:     English: "Swedish"
        swed: LangStr

        #: ::
        #:
        #:     Name of the Tamil language (endonym: தமிழ்), for language
        #:     pickers.
        #:
        #:     English: "Tamil"
        taml: LangStr

        #: ::
        #:
        #:     Name of the Thai language (endonym: ภาษาไทย), for language
        #:     pickers.
        #:
        #:     English: "Thai"
        thai: LangStr

        #: ::
        #:
        #:     Name of the Turkish language (endonym: Türkçe), for language
        #:     pickers.
        #:
        #:     English: "Turkish"
        turk: LangStr

        #: ::
        #:
        #:     Name of the Ukrainian language (endonym: Українська), for
        #:     language pickers.
        #:
        #:     English: "Ukrainian"
        ukrn: LangStr

        #: ::
        #:
        #:     Name of the Venetian language (endonym: Veneto), for language
        #:     pickers.
        #:
        #:     English: "Venetian"
        venetn: LangStr

        #: ::
        #:
        #:     Name of the Vietnamese language (endonym: Tiếng Việt), for
        #:     language pickers.
        #:
        #:     English: "Vietnamese"
        viet: LangStr

    class StringsStatusGroup:
        """
        ::

            Transient sentence-case messages and prompts: progress notes,
            failures, confirmations. Written as full sentences, so unlike the
            actions group these are not label-styled and should not be used as
            button text.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Default confirmation-dialog question.
        #:
        #:     English: "Are you sure?"
        are_you_sure: LangStr

        #: ::
        #:
        #:     Generic "Connected." status label.
        #:
        #:     English: "Connected."
        connected: LangStr

        #: ::
        #:
        #:     Generic "Connecting..." status label.
        #:
        #:     English: "Connecting..."
        connecting: LangStr

        #: ::
        #:
        #:     Confirmation shown after copying text to the clipboard.
        #:
        #:     English: "Copied to clipboard."
        copied_to_clipboard: LangStr

        #: ::
        #:
        #:     Instruction to open a URL in a web browser.
        #:
        #:     English: "Please direct a web-browser to the following URL:"
        direct_browser_to_url: LangStr

        #: ::
        #:
        #:     Generic error-page message.
        #:
        #:     English: "An error has occurred."
        error_occurred: LangStr

        #: ::
        #:
        #:     Generic "Importing..." status label.
        #:
        #:     English: "Importing..."
        importing: LangStr

        #: ::
        #:
        #:     Parenthetical "(invalid)" marker.
        #:
        #:     English: "(invalid)"
        invalid: LangStr

        #: ::
        #:
        #:     Generic lowercase "loading" status word.
        #:
        #:     English: "loading"
        loading: LangStr

        #: ::
        #:
        #:     Notice shown when a changed setting only takes effect after an
        #:     app restart.
        #:
        #:     English: "You must restart the game for this to take effect."
        must_restart: LangStr

        #: ::
        #:
        #:     Error-page message.
        #:
        #:     English: "You must update the app to view this."
        need_update: LangStr

        #: ::
        #:
        #:     Generic "not available" apology.
        #:
        #:     English: "Sorry, this is not available."
        not_available: LangStr

        #: ::
        #:
        #:     Placeholder shown for an empty page or list with no content to
        #:     display.
        #:
        #:     English: "There is nothing here."
        nothing_here: LangStr

        #: ::
        #:
        #:     Generic "One Moment..." status line.
        #:
        #:     English: "One Moment..."
        one_moment: LangStr

        #: ::
        #:
        #:     Transient screen-message.
        #:
        #:     English: "Page is refreshing - try again in a moment."
        page_refreshing_try_again: LangStr

        #: ::
        #:
        #:     Generic "Please wait..." status line.
        #:
        #:     English: "Please wait..."
        please_wait: LangStr

        #: ::
        #:
        #:     Error-page message; usually paired with a Retry button.
        #:
        #:     English: "Error talking to server."
        server_error: LangStr

        #: ::
        #:
        #:     Generic "Sharing..." status label.
        #:
        #:     English: "Sharing..."
        sharing: LangStr

        #: ::
        #:
        #:     Notice shown when a feature needs the OS storage-access
        #:     permission (mobile).
        #:
        #:     English: "This requires storage access"
        storage_permission_needed: LangStr

        #: ::
        #:
        #:     Generic failure message asking the player to retry.
        #:
        #:     English: "Unable to complete this right now. Please try again."
        unable_to_complete: LangStr

        #: ::
        #:
        #:     Notice when a feature is unavailable, likely due to no internet.
        #:
        #:     English: "This is currently unavailable (no internet
        #:     connection?)"
        unavailable_no_connection: LangStr

        #: ::
        #:
        #:     Lowercase "unavailable" status indicator.
        #:
        #:     English: "unavailable"
        unavailable_status: LangStr

        #: ::
        #:
        #:     Error/placeholder-page message.
        #:
        #:     English: "Under construction - check back soon."
        under_construction: LangStr

        #: ::
        #:
        #:     Generic "What is this?" help link.
        #:
        #:     English: "What is this?"
        what_is_this: LangStr

    class StringsValuesGroup:
        """
        ::

            Single generic words naming a state, option, or field: on/off,
            enabled/disabled, auto, never, low/medium/high, name, description.
            Title-cased for use in option lists and table headers.

            See source for the full asset list.
        """

        #: ::
        #:
        #:     Generic 'All' filter/category label (e.g. showing all items in a
        #:     list).
        #:
        #:     English: "All"
        all: LangStr

        #: ::
        #:
        #:     Generic 'Always' option value (e.g. when to apply an effect).
        #:
        #:     English: "Always"
        always: LangStr

        #: ::
        #:
        #:     Generic 'Auto' option value (automatic selection, e.g. graphics
        #:     quality or resolution).
        #:
        #:     English: "Auto"
        auto: LangStr

        #: ::
        #:
        #:     Generic "Code" field label.
        #:
        #:     English: "Code"
        code: LangStr

        #: ::
        #:
        #:     Generic "Deprecated" marker for outdated options.
        #:
        #:     English: "Deprecated"
        deprecated: LangStr

        #: ::
        #:
        #:     Generic "Description" field label.
        #:
        #:     English: "Description"
        description: LangStr

        #: ::
        #:
        #:     Generic 'Disabled' state/filter label.
        #:
        #:     English: "Disabled"
        disabled: LangStr

        #: ::
        #:
        #:     Generic 'Enabled' state/filter label.
        #:
        #:     English: "Enabled"
        enabled: LangStr

        #: ::
        #:
        #:     Error-dialog title label; the dialog body carries the failure
        #:     details. Title only — never used as a full error message.
        #:
        #:     English: "Error"
        error: LangStr

        #: ::
        #:
        #:     Generic 'High' quality-level option value.
        #:
        #:     English: "High"
        high: LangStr

        #: ::
        #:
        #:     Generic 'Higher' quality-level option value (a step above
        #:     'High').
        #:
        #:     English: "Higher"
        higher: LangStr

        #: ::
        #:
        #:     Generic 'Low' quality-level option value.
        #:
        #:     English: "Low"
        low: LangStr

        #: ::
        #:
        #:     Generic 'Medium' quality-level option value.
        #:
        #:     English: "Medium"
        medium: LangStr

        #: ::
        #:
        #:     Generic "Name" field label.
        #:
        #:     English: "Name"
        name: LangStr

        #: ::
        #:
        #:     Generic 'Never' option value (e.g. when to apply an effect).
        #:
        #:     English: "Never"
        never: LangStr

        #: ::
        #:
        #:     Generic "New" button label.
        #:
        #:     English: "New"
        new: LangStr

        #: ::
        #:
        #:     Generic "Off" toggle label.
        #:
        #:     English: "Off"
        off: LangStr

        #: ::
        #:
        #:     Generic "On" toggle label.
        #:
        #:     English: "On"
        on: LangStr

        #: ::
        #:
        #:     Generic 'Random' option value (e.g. random playlist type).
        #:
        #:     English: "Random"
        random: LangStr

        #: ::
        #:
        #:     Lowercase "total" label.
        #:
        #:     English: "total"
        total: LangStr

        #: ::
        #:
        #:     Small connector word "via" (as in "signed in via X").
        #:
        #:     English: "via"
        via: LangStr

    class StringsGroup:
        """
        ::

            Vocabulary shared across the whole platform -- engine UI,
            server-rendered web pages, and tools alike. Nothing here may be
            specific to a particular game or app mode; that belongs in that
            game's own package.

            See source for the full asset list.
        """

        actions: StringsActionsGroup
        compose: StringsComposeGroup
        locales: StringsLocalesGroup
        status: StringsStatusGroup
        values: StringsValuesGroup

    #: The ``strings`` group - 134 strings (``actions``, ``compose``,
    #: ``locales``, ``status``, ``values``, and 129 more). Full list in source.
    strings: StringsGroup

_TREE = {
    'strings': {
        'actions': {
            'accept': (),
            'apply': (),
            'back': (),
            'cancel': (),
            'confirm': (),
            'connect': (),
            'continue_': (),
            'copy': (),
            'customize': (),
            'decline': (),
            'delete': (),
            'discard': (),
            'done': (),
            'duplicate': (),
            'edit': (),
            'enter': (),
            'filter': (),
            'ignore': (),
            'import_': (),
            'learn_more': (),
            'more': (),
            'not_now': (),
            'ok': (),
            'other': (),
            'rename': (),
            'reset': (),
            'restart': (),
            'retry': (),
            'save': (),
            'select': (),
            'select_ellipsis': (),
            'send': (),
            'share': (),
            'show': (),
            'submit': (),
            'upgrade': (),
        },
        'compose': {
            'angle_button_suffix': ('main', 'button'),
            'dash_wrap': ('main',),
            'data_size': ('size',),
            'ellipsis_suffix': ('main',),
            'gapped_pair': ('first', 'second'),
            'heading_suffix': ('main',),
            'icon_label': ('icon', 'label'),
            'line_pair': ('first', 'second'),
            'or_join': ('a', 'b'),
            'paren_suffix': ('main', 'note'),
            'parenthesized': ('note',),
            'spaced_pair': ('first', 'second'),
        },
        'locales': {
            'arabc': (),
            'blrs': (),
            'chn_sim': (),
            'chn_tr': (),
            'croat': (),
            'czch': (),
            'dnsh': (),
            'dtch': (),
            'eng': (),
            'esprnto': (),
            'filp': (),
            'frnch': (),
            'gibber': (),
            'greek': (),
            'grmn': (),
            'hndi': (),
            'hngr': (),
            'indnsn': (),
            'italn': (),
            'jpn': (),
            'kazk': (),
            'kor': (),
            'mlay': (),
            'pers': (),
            'pirate': (),
            'pol': (),
            'prtg_brz': (),
            'prtg_pr': (),
            'rom': (),
            'rusn': (),
            'slvk': (),
            'spn_lat': (),
            'spn_spn': (),
            'srbn': (),
            'swed': (),
            'taml': (),
            'thai': (),
            'turk': (),
            'ukrn': (),
            'venetn': (),
            'viet': (),
        },
        'status': {
            'are_you_sure': (),
            'connected': (),
            'connecting': (),
            'copied_to_clipboard': (),
            'direct_browser_to_url': (),
            'error_occurred': (),
            'importing': (),
            'invalid': (),
            'loading': (),
            'must_restart': (),
            'need_update': (),
            'not_available': (),
            'nothing_here': (),
            'one_moment': (),
            'page_refreshing_try_again': (),
            'please_wait': (),
            'server_error': (),
            'sharing': (),
            'storage_permission_needed': (),
            'unable_to_complete': (),
            'unavailable_no_connection': (),
            'unavailable_status': (),
            'under_construction': (),
            'what_is_this': (),
        },
        'values': {
            'all': (),
            'always': (),
            'auto': (),
            'code': (),
            'deprecated': (),
            'description': (),
            'disabled': (),
            'enabled': (),
            'error': (),
            'high': (),
            'higher': (),
            'low': (),
            'medium': (),
            'name': (),
            'never': (),
            'new': (),
            'off': (),
            'on': (),
            'random': (),
            'total': (),
            'via': (),
        },
    }
}
_DISPLAY_KINDS = {'strings/compose/data_size': {'size': 'bytes'}}


if not TYPE_CHECKING:
    strings = LangStrDir(
        __asset_package__,
        _TREE['strings'],
        'strings',
        display_kinds=_DISPLAY_KINDS,
    )
