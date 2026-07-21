# Released under the MIT License. See LICENSE for details.
#
"""Pre-display resolution for native (v2) doc-ui responses.

Before a v2 page renders, every asset-package its language-strings and
asset refs reference must be resolved locally in the current locale
(loading the packages' per-locale values into the native language
tables). Client-effects that may run later are also de-indexed to the
self-describing resource form here, while the response's package-index
map is still at hand.
"""

from typing import TYPE_CHECKING

import bacommon.docui.v2 as dui2
from bacommon.langstr import LangStrSpec

if TYPE_CHECKING:
    from typing import Iterator

    from bacommon.locale import Locale
    from bacommon.docui import DocUIRequest
    from bacommon.assetref import TextureSpec, MeshSpec


def request_is_get(request: DocUIRequest) -> bool:
    """Whether a doc-ui request uses the GET method."""
    import bacommon.docui.v1 as dui1

    if isinstance(request, dui1.Request):
        return request.method is dui1.RequestMethod.GET
    if isinstance(request, dui2.Request):
        return request.method is dui2.RequestMethod.GET
    return False


def check_finalization_leaks(response: dui2.Response) -> None:
    """Flag resource-form strings in a finalized server response.

    A response carrying a package manifest claims to be *fully*
    indexed; any full-size (resource-form) value means some server
    path skipped finalization. Call this on pristine server responses
    only — controllers may legitimately splice local resource-form
    content in afterward (offline rows etc.), so checking later would
    misfire on that. (Decode is tolerant of mixed forms, so this is a
    diagnostic, not a render gate. Local pages carry no manifest and
    legitimately stay resource-form.)
    """
    import bauiv1 as bui
    import bacommon.clienteffect as clfx
    from bacommon.langstr import contains_resource_form

    if not response.packages:
        return
    leaks = sum(
        1
        for lstr in page_langstrs(response.page)
        if contains_resource_form(lstr)
    )
    leaks += sum(
        1
        for effect in response.client_effects
        if isinstance(effect, clfx.ScreenMessageV2)
        and contains_resource_form(effect.message)
    )
    if leaks:
        bui.uilog.error(
            'Doc-ui response declares indexed language-strings but'
            ' contains %d resource-form value(s); some server path'
            ' is skipping finalization.',
            leaks,
        )


def resolve_response(response: dui2.Response) -> None:
    """Resolve packages + de-index deferred effects for a v2 response.

    Runs in a background thread (the resolve itself is marshalled to
    the logic thread and awaited). After this returns, every package
    the page references is locally resolved in the current locale and
    the response's client-effects carry self-describing language
    strings, so the page can be prepped and rendered natively.
    """
    import bauiv1 as bui

    assert not bui.in_logic_thread()

    import bacommon.clienteffect as clfx

    # Sanity check: responses can be tailored per-build (client-effect
    # forms etc.), so one stamped for a different build is stale — note
    # it loudly. (When response caching arrives this should become a
    # toss-and-refetch.)
    ourbuild = bui.app.env.engine_build_number
    if response.for_build is not None and response.for_build != ourbuild:
        bui.uilog.warning(
            'Got doc-ui response built for engine build %d but we are'
            ' build %d; it may contain stale/mismatched content.',
            response.for_build,
            ourbuild,
        )

    locale = bui.app.locale.current_locale

    # A wire response finalized to the indexed form carries its package
    # manifest; that plus the walk below (asset refs, plus any
    # resource-form strings on local/legacy pages) covers everything we
    # need resolved before render — including packages the contained
    # client-effects will want later.
    apverids: set[str] = set(response.packages)
    collect_apverids(response.page, apverids)
    clfx.collect_apverids(response.client_effects, apverids)

    bui.uilog.debug(
        'docui v2 prep: resolving %d package(s) for locale %s: %s.',
        len(apverids),
        locale.name,
        sorted(apverids),
    )
    _resolve_packages_blocking(sorted(apverids), locale)
    bui.uilog.debug(
        'docui v2 prep: resolve complete for locale %s.', locale.name
    )

    # Native handles bound against this payload's package manifest;
    # evaluation and de-indexing both resolve through the native
    # language tables the resolve just (re)loaded.
    import babase
    from efro.dataclassio import dataclass_to_json, dataclass_from_json

    packages = list(response.packages)

    def _native(lstr: LangStrSpec) -> babase.LangStr:
        return babase.LangStr(dataclass_to_json(lstr), packages=packages)

    # Client-effects run later (deferred; possibly after this
    # response and its package-index map are gone), so convert their
    # indexed strings back to the self-describing resource form the
    # effects runner consumes. Fail-soft per effect: an unconvertible
    # message is left as-is and fails visibly at run time instead.
    def _deindex_effects(effects: 'list[clfx.Effect]') -> None:
        for effect in effects:
            if isinstance(effect, clfx.ScreenMessageV2):
                try:
                    effect.message = dataclass_from_json(
                        LangStrSpec, _native(effect.message).to_resource_json()
                    )
                except Exception:
                    bui.uilog.exception(
                        'Error de-indexing client-effect message.'
                    )

    if response.packages:
        _deindex_effects(response.client_effects)
        for row in response.page.rows:
            if not isinstance(row, dui2.ButtonRow):
                continue
            for button in row.buttons:
                if isinstance(button.action, dui2.Local):
                    _deindex_effects(button.action.immediate_client_effects)


def _resolve_packages_blocking(apverids: list[str], locale: Locale) -> None:
    """Run the async, logic-thread asset resolve and block until done.

    Called from the background prep thread; marshals the resolve onto the
    logic thread (where it must run) and waits on it.
    """
    import threading

    import bauiv1 as bui

    if not apverids:
        return

    done = threading.Event()
    box: dict[str, BaseException] = {}

    def _kick() -> None:
        async def _run() -> None:
            try:
                await bui.app.assets.resolve(apverids, language=locale)
            except Exception as exc:
                box['error'] = exc
            finally:
                done.set()

        bui.app.create_async_task(_run())

    bui.pushcall(_kick, from_other_thread=True)
    if not done.wait(timeout=30.0):
        raise RuntimeError('Timed out resolving doc-ui asset-packages.')
    if 'error' in box:
        raise box['error']


def collect_apverids(page: dui2.Page, acc: set[str]) -> None:
    """Gather every asset-package-version the page's l-strings reference."""
    import bacommon.clienteffect as clfx
    from bacommon import langstr

    # (The recursive langstr walk lives at module level in
    # bacommon.langstr; a self-recursive closure here would create a
    # reference cycle per call.)
    def _walk(lstr: LangStrSpec) -> None:
        langstr.collect_apverids(lstr, acc)

    def _maybe(lstr: LangStrSpec | None) -> None:
        if lstr is not None:
            _walk(lstr)

    def _ref(ref: TextureSpec | MeshSpec | None) -> None:
        if ref is not None:
            acc.add(ref.apverid)

    def _decos(decos: list[dui2.Decoration] | None) -> None:
        for deco in decos or []:
            if isinstance(deco, dui2.Text):
                _walk(deco.text)
            elif isinstance(deco, dui2.Image):
                _ref(deco.texture)
                _ref(deco.tint_texture)
                _ref(deco.mask_texture)
                _ref(deco.mesh_opaque)
                _ref(deco.mesh_transparent)

    _walk(page.title)
    for row in page.rows:
        if not isinstance(row, dui2.ButtonRow):
            continue
        _maybe(row.title)
        _maybe(row.subtitle)
        _decos(row.header_decorations_left)
        _decos(row.header_decorations_center)
        _decos(row.header_decorations_right)
        for button in row.buttons:
            _maybe(button.label)
            _ref(button.texture)
            _ref(button.icon)
            _decos(button.decorations)
            # Button-press effects (v2 forms) reference packages too;
            # gathering them here pre-warms them during page resolve so
            # press-time runs are cache hits.
            if isinstance(button.action, dui2.Local):
                clfx.collect_apverids(
                    button.action.immediate_client_effects, acc
                )


def page_langstrs(page: dui2.Page) -> 'Iterator[LangStrSpec]':
    """Yield every top-level language-string slot in a page.

    Covers titles/subtitles/labels/text decorations plus messages in
    button immediate-client-effects (nested substitution values are
    *not* yielded separately; walk each yielded tree if you need
    those).
    """
    import bacommon.clienteffect as clfx

    def _decos(
        decos: list[dui2.Decoration] | None,
    ) -> 'Iterator[LangStrSpec]':
        for deco in decos or []:
            if isinstance(deco, dui2.Text):
                yield deco.text

    yield page.title
    for row in page.rows:
        if not isinstance(row, dui2.ButtonRow):
            continue
        if row.title is not None:
            yield row.title
        if row.subtitle is not None:
            yield row.subtitle
        yield from _decos(row.header_decorations_left)
        yield from _decos(row.header_decorations_center)
        yield from _decos(row.header_decorations_right)
        for button in row.buttons:
            if button.label is not None:
                yield button.label
            yield from _decos(button.decorations)
            if isinstance(button.action, dui2.Local):
                for effect in button.action.immediate_client_effects:
                    if isinstance(effect, clfx.ScreenMessageV2):
                        yield effect.message
