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
    from bacommon.assetspec import (
        TextureSpec,
        MeshSpec,
        SoundSpec,
        CollisionMeshSpec,
        AssetBucketKind,
        AssetIndexContext,
    )
    from bacommon.langstr import LangStrFlatIndexContext
    import bacommon.clienteffect as clfx


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
        and not isinstance(effect.message, int)
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
                if isinstance(effect.message, int):
                    # deindex_langstrs runs first, so a folded index
                    # here means it failed to unfold; leave it to fail
                    # visibly at run time rather than guessing.
                    continue
                try:
                    effect.message = dataclass_from_json(
                        LangStrSpec, _native(effect.message).to_resource_json()
                    )
                except Exception:
                    bui.uilog.exception(
                        'Error de-indexing client-effect message.'
                    )

    if response.packages:
        # Strings first: the effect de-index below consumes them, and
        # it expects the two-int form rather than a folded index.
        deindex_langstrs(
            response.page,
            packages,
            response.client_effects,
            expect_digest=response.langstr_index_digest,
        )
        deindex_assets(
            response.page,
            packages,
            response.client_effects,
            expect_digest=response.asset_index_digest,
        )
        _deindex_effects(response.client_effects)
        for row in response.page.rows:
            if not isinstance(row, dui2.ButtonRow):
                continue
            for button in row.buttons:
                if isinstance(button.action, dui2.Local):
                    _deindex_effects(button.action.immediate_client_effects)


def package_asset_listing(apverid: str) -> list[str] | None:
    """Canonical sorted logical paths for every asset in a package.

    The client's half of the flat-index mapping. Deliberately the union
    across buckets rather than one bucket: the server groups the same
    paths differently (collision meshes sit in the ``constant`` bucket
    here but under ``meshes`` there), so only the union is guaranteed
    to agree. Indexing the whole package makes the grouping irrelevant.

    This is the *registry*, i.e. what the package actually built, which
    is why the server has to vendor an equally complete listing rather
    than derive one from its wrapper accessors -- cube maps and the
    legacy-language-data blob appear here and have no accessor. When
    the two lists disagree the digest check in :func:`_domains_agree`
    is what catches it; nothing else would.

    ``None`` when the package isn't registered at all -- a
    resolve-ordering fault -- as distinct from a registered package that
    holds nothing.
    """
    import babase

    from bacommon.assetspec import AssetBucketKind

    out: list[str] = []
    known = False
    for kind in AssetBucketKind:
        paths = babase.asset_package_bucket_paths(apverid, kind)
        if paths is None:
            continue
        known = True
        out.extend(paths)
    if not known:
        return None
    return sorted(set(out))


def package_string_count(apverid: str) -> int | None:
    """Language-string count for a package, this locale.

    The client's half of the flat string mapping. Only the count is
    needed: unfolding produces the two-integer form the native decoder
    already consumes, so the names stay native.
    """
    import babase

    return babase.asset_package_string_count(apverid)


def deindex_langstrs(
    page: dui2.Page,
    packages: list[str],
    effects: 'list[clfx.Effect] | None' = None,
    *,
    expect_digest: str | None = None,
) -> None:
    """Unfold a page's flat string indices into the two-int form.

    Runs after the page's packages resolve, so every language table the
    indices address is loaded. Produces
    :class:`~bacommon.langstr.LangStrSpecResourceIndexed` -- exactly
    what the native decoder already consumed before folding existed --
    so nothing downstream changes.

    ``expect_digest`` is the producer's
    :meth:`~bacommon.langstr.LangStrFlatIndexContext.domain_digest`;
    see :func:`deindex_assets` for why a mismatch means we must not
    unfold at all.

    Fail-visible per slot: a bad index logs and leaves the integer in
    place rather than substituting a wrong string.
    """
    import bauiv1 as bui
    from bacommon.langstr import (
        LangStrFlatIndexContext,
        LangStrIndexError,
        LangStrSpecResourceIndexed,
    )
    from bacommon.docui.walk import walk_page

    if not packages:
        return

    ctx = LangStrFlatIndexContext(packages, package_string_count)
    if not _domains_agree(ctx, expect_digest, 'language-string'):
        return

    def _lstr(val: 'LangStrSpec | int') -> 'LangStrSpec | None':
        # Spec-form strings pass through: a response can mix forms, and
        # anything with substitutions never folds.
        if not isinstance(val, int):
            return None
        try:
            pkg, index = ctx.from_flat(val)
        except LangStrIndexError:
            bui.uilog.exception('Error unfolding string index %d.', val)
            return None
        return LangStrSpecResourceIndexed(pkg=pkg, index=index)

    walk_page(page, langstr=_lstr)
    if effects:
        # Response-level effects are outside the page walk, and they
        # carry folded strings just the same.
        import bacommon.clienteffect as clfx

        clfx.walk_effects(effects, langstr=_lstr)


def _domains_agree(
    ctx: 'AssetIndexContext | LangStrFlatIndexContext',
    expect_digest: str | None,
    what: str,
) -> bool:
    """Whether an index domain matches the one the producer used.

    The two ends build their domains from different sources, so they
    can disagree -- and a disagreement hides itself: an index that is
    wrong but still in range names a different asset or string, so the
    page renders wrong and nothing raises. The digest is the only thing
    that makes that visible, which is why a mismatch has to stop the
    de-index entirely rather than proceed per-slot. Leaving the
    integers in place lands the failure on the existing loud paths.

    A payload with no digest (an older producer) is taken as agreeing;
    the digest is a guard, not a requirement.
    """
    import bauiv1 as bui

    if expect_digest is None:
        return True
    ours = ctx.domain_digest()
    if ours == expect_digest:
        return True
    bui.uilog.error(
        'Doc-ui %s index domain disagrees with the producer'
        ' (ours %s, theirs %s); refusing to de-index, so this page will'
        ' render incompletely. Our per-package sizes: %s. This means the'
        ' two ends derive different listings for some package above;'
        ' compare those sizes against the producer side.',
        what,
        ours,
        expect_digest,
        ctx.describe_domain(),
    )
    return False


def deindex_assets(
    page: dui2.Page,
    packages: list[str],
    effects: 'list[clfx.Effect] | None' = None,
    *,
    expect_digest: str | None = None,
) -> None:
    """Replace a page's flat asset indices with real specs.

    Runs after the page's packages are resolved, so every listing the
    indices address is locally available. Everything downstream of this
    -- prep, render, the depiction code -- therefore only ever sees
    specs, and never has to know the indexed form existed.

    ``expect_digest`` is the producer's
    :meth:`~bacommon.assetspec.AssetIndexContext.domain_digest`; a
    mismatch skips de-indexing entirely (see :func:`_domains_agree`).

    Fail-visible per reference: a bad index logs and leaves the integer
    in place rather than substituting a wrong asset, and the render then
    fails on that one slot.
    """
    import bauiv1 as bui

    from bacommon.assetspec import AssetIndexContext, AssetIndexError
    from bacommon.docui.walk import walk_page

    if not packages:
        return

    ctx = AssetIndexContext(packages, package_asset_listing)
    if not _domains_agree(ctx, expect_digest, 'asset'):
        return

    def _convert(
        ref: 'TextureSpec | MeshSpec | SoundSpec | int',
        kind: 'AssetBucketKind',
    ) -> 'TextureSpec | MeshSpec | SoundSpec | CollisionMeshSpec | None':
        # Spec-form refs pass through: a response can legitimately mix
        # forms (an old-form producer, a locally-built page).
        if not isinstance(ref, int):
            return None
        try:
            return ctx.from_index(ref, kind)
        except AssetIndexError:
            bui.uilog.exception(
                'Error de-indexing %s asset ref %d.', kind.value, ref
            )
            return None

    # One visitor for every slot, not one per spec union. `walk_page`
    # hands a button's immediate client-effects to `walk_effects` using
    # the *page* visitor, so a textures-and-meshes-only visitor silently
    # dropped the sound refs in them -- they stayed integers and failed
    # at run time with 'Un-de-indexed sound ref N in a client-effect'.
    # The slot's own `kind` already decides which spec `_convert`
    # produces, so no narrowing is needed (or correct) here.
    walk_page(page, assetref=_convert)  # type: ignore[arg-type]
    if effects:
        # Response-level effects are outside the page walk, and their
        # sounds are indexed the same as page art.
        import bacommon.clienteffect as clfx

        clfx.walk_effects(effects, assetref=_convert)  # type: ignore[arg-type]


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
        raise RuntimeError(
            f'Timed out resolving doc-ui asset-packages: {apverids}.'
        )
    if 'error' in box:
        raise box['error']


def collect_apverids(page: dui2.Page, acc: set[str]) -> None:
    """Gather every asset-package a page references into ``acc``.

    Covers both the packages its language-strings resolve against and
    the ones its textures and meshes live in -- the client must have
    all of them before it can render.
    """
    from bacommon import langstr
    import bacommon.clienteffect as clfx
    from bacommon.docui.walk import walk_page

    def _lstr(lstr: 'LangStrSpec | int') -> None:
        # Read-only: returning nothing leaves the slot as it is. A
        # folded index names no package of its own.
        if not isinstance(lstr, int):
            langstr.collect_apverids(lstr, acc)

    def _ref(
        ref: 'TextureSpec | MeshSpec | int', _kind: 'AssetBucketKind'
    ) -> None:
        # An already-indexed ref names no package of its own -- it
        # resolves through ``Response.packages``, which the caller
        # already seeded ``acc`` from. Nothing to collect.
        if not isinstance(ref, int):
            acc.add(ref.apverid)

    walk_page(page, langstr=_lstr, assetref=_ref)

    # Client-effects hanging off buttons reference packages too;
    # gathering them here pre-warms them during page resolve so
    # press-time runs are cache hits. They have their own walk.
    for row in page.rows:
        if not isinstance(row, dui2.ButtonRow):
            continue
        for button in row.buttons:
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
    from bacommon.docui.walk import walk_page

    out: list['LangStrSpec'] = []

    def _lstr(lstr: 'LangStrSpec | int') -> None:
        # A folded index carries no inspectable content; callers that
        # want one resolved should unfold it first.
        if not isinstance(lstr, int):
            out.append(lstr)

    walk_page(page, langstr=_lstr)
    yield from out
