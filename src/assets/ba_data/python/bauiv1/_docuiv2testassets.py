# Released under the MIT License. See LICENSE for details.
#
# Auto-generated; do not edit by hand.
"""Asset-package wrapper for ``a-0.badocuiv2testassets.260716`` (bauiv1)."""

# ba_meta require api 9
# ba_meta require asset-package a-0.badocuiv2testassets.260716

# pylint: disable=useless-suppression
# pylint: disable=too-many-lines
# pylint: disable=too-few-public-methods, disallowed-name

__asset_package__ = 'a-0.badocuiv2testassets.260716'

from typing import TYPE_CHECKING

from bacommon.langstr import LangStrDir

if TYPE_CHECKING:
    from bacommon.langstr import LangStr

    class StringsCloudGroup:
        """
        Cloud-message test page strings.

        See source for the full asset list.
        """

        #: Body text on the cloud-message test page.
        #:
        #: English: "This page came from the cloud."
        came_from_cloud: LangStr

        #: Button requesting a test page via a cloud message.
        #:
        #: English: "Cloud-Msg GET"
        cloud_msg_get: LangStr

        #: Button posting a test action via a cloud message.
        #:
        #: English: "Cloud-Msg POST"
        cloud_msg_post: LangStr

        #: Title of the cloud-message test page.
        #:
        #: English: "Cloud Test"
        cloud_test: LangStr

    class StringsCommonGroup:
        """
        Greetings, debug toggles, and shared bits.

        See source for the full asset list.
        """

        def code_literal(self, *, text: str | LangStr) -> LangStr:
            """
            Verbatim passthrough for code identifiers (button style names etc.)
            on test pages.

            English: "{text}"
            """

        #: Developer note on the test root page.
        #:
        #: English: "Use this as a reference for building UIs with DocUI. Its
        #: code lives at bauiv1lib.docuitest."
        docui_reference: LangStr

        #: Subtitle on the timed-actions test page.
        #:
        #: English: "Each change here is a new request/response."
        each_change: LangStr

        #: Placeholder label for layout tests.
        #:
        #: English: "foo"
        foo: LangStr

        #: Debug marker for the left header slot.
        #:
        #: English: "HeaderLeft"
        header_left: LangStr

        #: Debug marker for the right header slot.
        #:
        #: English: "HeaderRight"
        header_right: LangStr

        #: Greeting text at the top of the test root page.
        #:
        #: English: "Hello from DocUI!"
        hello_from_docui: LangStr

        #: Screen-message from the centered-content test button.
        #:
        #: English: "Hello There!"
        hello_there: LangStr

        def hello_there_num(self, *, num: str | LangStr) -> LangStr:
            """
            Row title on the timed-actions page; {num} increments with each
            timed update.

            English: "Hello There {num}"
            """

        #: Button toggling layout-debug decorations off.
        #:
        #: English: "Hide Debug"
        hide_debug: LangStr

        #: Button deliberately sending a malformed request to test error
        #: handling.
        #:
        #: English: "Invalid Request"
        invalid_request: LangStr

        #: Button toggling layout-debug decorations on.
        #:
        #: English: "Show Debug"
        show_debug: LangStr

        #: Wry button label on the slow-load test page.
        #:
        #: English: "Sure Did"
        sure_did: LangStr

        #: Row title shown after the deliberately slow page loads.
        #:
        #: English: "That Took a While"
        that_took_a_while: LangStr

        #: Button opening the timed-actions test page.
        #:
        #: English: "Timed Actions"
        timed_actions: LangStr

        def you_are(self, *, name: str | LangStr) -> LangStr:
            """
            Account-name line on a server-driven test page.

            English: "You are: {name}"
            """

    class StringsEffectsGroup:
        """
        Client-effect and local-action test buttons and messages.

        See source for the full asset list.
        """

        #: Screen-message confirming a test effect/action ran.
        #:
        #: English: "Success!"
        effect_success: LangStr

        #: Button firing client-effects immediately on press (no request
        #: round-trip).
        #:
        #: English: "Immediate ClientEffects"
        immediate_client_effects: LangStr

        #: Screen-message fired by the immediate client-effects test button.
        #:
        #: English: "Hello From Immediate Client Effects"
        immediate_effects_hello: LangStr

        #: Button firing a local action immediately on press.
        #:
        #: English: "Immediate Local Action"
        immediate_local_action: LangStr

        #: Button whose response carries client-effects to run.
        #:
        #: English: "Response Client Effects"
        response_client_effects: LangStr

        #: Screen-message fired by the response client-effects test button.
        #:
        #: English: "Hello From Response Client Effects"
        response_effects_hello: LangStr

        #: Button whose response carries a local action to run.
        #:
        #: English: "Response Local Action"
        response_local_action: LangStr

    class StringsItemsGroup:
        """
        Display-item test page strings.

        See source for the full asset list.
        """

        #: Title of the display-item test page's row.
        #:
        #: English: "Display Item Tests"
        display_item_tests: LangStr

        #: Button opening (and title of) the display-item test page.
        #:
        #: English: "Display Items"
        display_items: LangStr

        #: Debug legend describing the display-item layout matrix.
        #:
        #: English: "top=FULL, center=COMPACT, bottom=ICON; left=regular,
        #: right=unknown"
        display_items_sub: LangStr

    class StringsLayoutGroup:
        """
        Layout/bounds test strings and debug markers.

        See source for the full asset list.
        """

        #: Placeholder label on the bounds-test page background.
        #:
        #: English: "(background texture)"
        background_texture: LangStr

        #: Button opening a single bounds test.
        #:
        #: English: "Bounds Test"
        bounds_test: LangStr

        #: Button opening the bounds-tests page.
        #:
        #: English: "Bounds Tests"
        bounds_tests: LangStr

        #: Title of the bounds-tests page.
        #:
        #: English: "Bounds Tests"
        bounds_tests_title: LangStr

        #: Title of the centered-content layout test row.
        #:
        #: English: "Centered Content / Faded Title"
        centered_faded_title: LangStr

        #: Corner-position marker (bottom-left) for layout debug.
        #:
        #: English: "BL"
        corner_bl: LangStr

        #: Corner-position marker (bottom-right) for layout debug.
        #:
        #: English: "BR"
        corner_br: LangStr

        #: Corner-position marker (top-left) for layout debug.
        #:
        #: English: "TL"
        corner_tl: LangStr

        #: Corner-position marker (top-right) for layout debug.
        #:
        #: English: "TR"
        corner_tr: LangStr

        #: Button opening the deliberately empty page.
        #:
        #: English: "Empty Page"
        empty_page: LangStr

        #: Title of the deliberately empty test page.
        #:
        #: English: "Empty Page"
        empty_page_title: LangStr

        #: Title of the deliberately empty button-row.
        #:
        #: English: "Empty Row"
        empty_row: LangStr

        #: Sample button label repeated across button styles on the bounds-tests
        #: page.
        #:
        #: English: "Hello"
        hello: LangStr

        #: Title of the layout-tests button-row.
        #:
        #: English: "Layout Tests"
        layout_tests: LangStr

        #: Title of the horizontally-scrolling long button-row.
        #:
        #: English: "Long Row Test"
        long_row_test: LangStr

        #: Subtitle on the long-row layout test.
        #:
        #: English: "Look - a subtitle!"
        look_a_subtitle: LangStr

        #: Debug marker exercising max-height/multi-line text layout.
        #:
        #: English: "MaxHeightTest SecondLine"
        max_height_test: LangStr

        #: Debug marker exercising max-width text layout.
        #:
        #: English: "MaxWidthTest"
        max_width_test: LangStr

        #: Button label inside the titleless-row layout test.
        #:
        #: English: "Row-With-No-Title Test"
        row_with_no_title: LangStr

        #: Subtitle on the subtitle-only layout test row.
        #:
        #: English: "Subtitle only!"
        subtitle_only: LangStr

        #: Subtitle on the centered-content layout test row.
        #:
        #: English: "Testing Centered Title/Content"
        testing_centered: LangStr

    class StringsNavGroup:
        """
        Page titles, row titles, and navigation buttons.

        See source for the full asset list.
        """

        #: Button opening a sub-page in browse (push) mode.
        #:
        #: English: "Browse"
        browse: LangStr

        #: Button closing the test window.
        #:
        #: English: "Close"
        close: LangStr

        #: Button dismissing the timed-actions test page.
        #:
        #: English: "Done"
        done: LangStr

        #: Title of the third button-row on the root page.
        #:
        #: English: "Even More Tests"
        even_more_tests: LangStr

        #: Title of the second button-row on the root page.
        #:
        #: English: "A Few More Tests"
        few_more_tests: LangStr

        #: Title of test page 2's button-row.
        #:
        #: English: "More Tests"
        more_tests: LangStr

        #: Button loading a page in replace mode (swaps the current page instead
        #: of pushing).
        #:
        #: English: "Replace"
        replace: LangStr

        #: Button opening a slow-loading sub-page in browse mode (exercises the
        #: loading state).
        #:
        #: English: "Slow Browse"
        slow_browse: LangStr

        #: Button loading a slow page in replace mode.
        #:
        #: English: "Slow Replace"
        slow_replace: LangStr

        #: Title of the first button-row on the root page.
        #:
        #: English: "Some Tests"
        some_tests: LangStr

        #: Generic test button label; also titles the slow-load and
        #: timed-actions pages.
        #:
        #: English: "Test"
        test: LangStr

        #: Title of the docui-v2 test root page.
        #:
        #: English: "Test Root"
        test_root_title: LangStr

        #: Another generic test button.
        #:
        #: English: "Test 3"
        test_three: LangStr

        #: Button opening test page 2.
        #:
        #: English: "Test 2"
        test_two: LangStr

        #: Title of test page 2.
        #:
        #: English: "Test 2"
        test_two_title: LangStr

    class StringsWebGroup:
        """
        Web-request test page strings.

        See source for the full asset list.
        """

        def came_from_web(self, *, method: str | LangStr) -> LangStr:
            """
            Body text on the web-request test page; {method} is the literal HTTP
            method used.

            English: "This page came from a web {method} request."
            """

        #: Button requesting a test page via a web GET request.
        #:
        #: English: "Web GET"
        web_get: LangStr

        #: Button requesting a test page via a web POST request.
        #:
        #: English: "Web POST"
        web_post: LangStr

        #: Title of the web-request test page.
        #:
        #: English: "Web Test"
        web_test: LangStr

    class StringsGroup:
        """
        Strings for the docui-v2 test UI (bauiv1lib.docuitest plus the master
        server's test pages) - a working reference for DocUI development.

        See source for the full asset list.
        """

        cloud: StringsCloudGroup
        common: StringsCommonGroup
        effects: StringsEffectsGroup
        items: StringsItemsGroup
        layout: StringsLayoutGroup
        nav: StringsNavGroup
        web: StringsWebGroup

    #: The ``strings`` group - 70 strings (``cloud``, ``common``, ``effects``,
    #: ``items``, ``layout``, and 65 more). Full list in source.
    strings: StringsGroup

_TREE = {
    'strings': {
        'cloud': {
            'came_from_cloud': (),
            'cloud_msg_get': (),
            'cloud_msg_post': (),
            'cloud_test': (),
        },
        'common': {
            'code_literal': ('text',),
            'docui_reference': (),
            'each_change': (),
            'foo': (),
            'header_left': (),
            'header_right': (),
            'hello_from_docui': (),
            'hello_there': (),
            'hello_there_num': ('num',),
            'hide_debug': (),
            'invalid_request': (),
            'show_debug': (),
            'sure_did': (),
            'that_took_a_while': (),
            'timed_actions': (),
            'you_are': ('name',),
        },
        'effects': {
            'effect_success': (),
            'immediate_client_effects': (),
            'immediate_effects_hello': (),
            'immediate_local_action': (),
            'response_client_effects': (),
            'response_effects_hello': (),
            'response_local_action': (),
        },
        'items': {
            'display_item_tests': (),
            'display_items': (),
            'display_items_sub': (),
        },
        'layout': {
            'background_texture': (),
            'bounds_test': (),
            'bounds_tests': (),
            'bounds_tests_title': (),
            'centered_faded_title': (),
            'corner_bl': (),
            'corner_br': (),
            'corner_tl': (),
            'corner_tr': (),
            'empty_page': (),
            'empty_page_title': (),
            'empty_row': (),
            'hello': (),
            'layout_tests': (),
            'long_row_test': (),
            'look_a_subtitle': (),
            'max_height_test': (),
            'max_width_test': (),
            'row_with_no_title': (),
            'subtitle_only': (),
            'testing_centered': (),
        },
        'nav': {
            'browse': (),
            'close': (),
            'done': (),
            'even_more_tests': (),
            'few_more_tests': (),
            'more_tests': (),
            'replace': (),
            'slow_browse': (),
            'slow_replace': (),
            'some_tests': (),
            'test': (),
            'test_root_title': (),
            'test_three': (),
            'test_two': (),
            'test_two_title': (),
        },
        'web': {
            'came_from_web': ('method',),
            'web_get': (),
            'web_post': (),
            'web_test': (),
        },
    }
}


if not TYPE_CHECKING:
    strings = LangStrDir(__asset_package__, _TREE['strings'], 'strings')
