# Released under the MIT License. See LICENSE for details.
#
"""Transcode a v2 doc-ui page into the equivalent v1 page.

v2's element schema mirrors v1's, except text is a language-agnostic
:class:`~bacommon.langstr.LangStr` instead of a raw ``str``. Once the referenced
asset-packages are resolved and a decode context is built, we decode each
``LangStr`` to a flat string and construct the equivalent v1 dataclasses (text
as ``literal`` -- ``is_lstr=False``). The existing v1 render pipeline
(``v1prep``) then draws a v2 page unchanged, so v2 needs no parallel renderer
for this milestone.
"""

from typing import TYPE_CHECKING

import bacommon.docui.v1 as dui1
import bacommon.docui.v2 as dui2
from bacommon.langstr import LangStr

if TYPE_CHECKING:
    from bacommon.locale import Locale
    from bacommon.docui import DocUIRequest
    from bacommon.langstr import LanguageStringNameDecodeContext
    from bacommon.assetref import TextureRef, MeshRef


def request_is_get(request: DocUIRequest) -> bool:
    """Whether a v1 or v2 doc-ui request uses the GET method."""
    if isinstance(request, dui1.Request):
        return request.method is dui1.RequestMethod.GET
    if isinstance(request, dui2.Request):
        return request.method is dui2.RequestMethod.GET
    return False


def request_to_v2(request: dui1.Request | dui2.Request) -> dui2.Request:
    """Return the v2 form of a v1 or v2 doc-ui request.

    Navigation from a transcoded v2 page hands the controller *v1*
    requests (the v2→v1 transcode converts the requests embedded in
    page actions along with everything else), so a v2-native
    controller should normalize incoming requests through this before
    dispatching on paths.
    """
    if isinstance(request, dui2.Request):
        return request
    return dui2.Request(
        path=request.path,
        method=dui2.RequestMethod(request.method.value),
        args=request.args,
    )


def resolve_and_transcode(response: dui2.Response) -> dui1.Response:
    """Resolve a v2 response's packages and transcode it to a v1 response.

    Runs in the background prep thread: marshals the (async, logic-thread)
    asset resolve over and blocks on it, reads the resolved per-locale string
    values, builds a name-decode context for the current locale, and
    transcodes the v2 page into the equivalent v1 page so the existing v1
    render pipeline can draw it.
    """
    import bauiv1 as bui
    from bacommon.langstr import LanguageStringNameDecodeContext

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
    apverids: set[str] = set()
    collect_apverids(response.page, apverids)
    # Response-level client-effects may reference packages too (v2
    # effect forms); pre-resolving here means they're warm by the time
    # the effects run.
    clfx.collect_apverids(response.client_effects, apverids)

    _resolve_packages_blocking(sorted(apverids), locale)

    language = {
        apverid: bui.app.assets.get_package_strings(apverid, locale)
        for apverid in apverids
    }
    ctx = LanguageStringNameDecodeContext(language, locale)
    return transcode_response(response, ctx)


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

    def _walk(lstr: LangStr) -> None:
        from bacommon.langstr import LangStrResource, LangStrValue

        if isinstance(lstr, LangStrResource):
            acc.add(lstr.apverid)
            subvals = lstr.subs.values()
        elif isinstance(lstr, LangStrValue):
            subvals = lstr.subs.values()
        else:
            # Indexed values resolve against an out-of-band context;
            # they carry no apverids of their own.
            return
        for sub in subvals:
            if isinstance(sub, LangStr):
                _walk(sub)

    def _maybe(lstr: LangStr | None) -> None:
        if lstr is not None:
            _walk(lstr)

    def _ref(ref: TextureRef | MeshRef | None) -> None:
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


def transcode_response(
    response: dui2.Response, ctx: LanguageStringNameDecodeContext
) -> dui1.Response:
    """Build the v1 ``Response`` equivalent of a decoded v2 ``Response``."""
    return dui1.Response(
        page=_page(response.page, ctx),
        status=dui1.ResponseStatus(response.status.value),
        client_effects=response.client_effects,
        local_action=response.local_action,
        local_action_args=response.local_action_args,
        timed_action=(
            None
            if response.timed_action is None
            else _action(response.timed_action)
        ),
        timed_action_delay=response.timed_action_delay,
        shared_state_id=response.shared_state_id,
    )


def _page(page: dui2.Page, ctx: LanguageStringNameDecodeContext) -> dui1.Page:
    return dui1.Page(
        title=ctx.decode(page.title),
        title_is_lstr=False,
        title_wrap=page.title_wrap,
        rows=[_row(r, ctx) for r in page.rows],
        center_vertically=page.center_vertically,
        row_spacing=page.row_spacing,
        simple_culling_v=page.simple_culling_v,
        padding_bottom=page.padding_bottom,
        padding_left=page.padding_left,
        padding_top=page.padding_top,
        padding_right=page.padding_right,
    )


def _row(row: dui2.Row, ctx: LanguageStringNameDecodeContext) -> dui1.Row:
    if not isinstance(row, dui2.ButtonRow):
        return dui1.UnknownRow()
    return dui1.ButtonRow(
        buttons=[_button(b, ctx) for b in row.buttons],
        header_height=row.header_height,
        header_scale=row.header_scale,
        header_decorations_left=_decos_opt(row.header_decorations_left, ctx),
        header_decorations_center=_decos_opt(
            row.header_decorations_center, ctx
        ),
        header_decorations_right=_decos_opt(row.header_decorations_right, ctx),
        title=None if row.title is None else ctx.decode(row.title),
        title_is_lstr=False,
        title_color=row.title_color,
        title_flatness=row.title_flatness,
        title_shadow=row.title_shadow,
        title_wrap=row.title_wrap,
        subtitle=None if row.subtitle is None else ctx.decode(row.subtitle),
        subtitle_is_lstr=False,
        subtitle_color=row.subtitle_color,
        subtitle_flatness=row.subtitle_flatness,
        subtitle_shadow=row.subtitle_shadow,
        subtitle_wrap=row.subtitle_wrap,
        button_spacing=row.button_spacing,
        spacing_top=row.spacing_top,
        spacing_bottom=row.spacing_bottom,
        padding_left=row.padding_left,
        padding_right=row.padding_right,
        padding_top=row.padding_top,
        padding_bottom=row.padding_bottom,
        center_content=row.center_content,
        center_title=row.center_title,
        simple_culling_h=row.simple_culling_h,
        debug=row.debug,
    )


def _button(
    button: dui2.Button, ctx: LanguageStringNameDecodeContext
) -> dui1.Button:
    return dui1.Button(
        label=None if button.label is None else ctx.decode(button.label),
        label_is_lstr=False,
        label_wrap=button.label_wrap,
        action=None if button.action is None else _action(button.action),
        size=button.size,
        color=button.color,
        label_color=button.label_color,
        label_scale=button.label_scale,
        label_flatness=button.label_flatness,
        texture=_ref_str_opt(button.texture),
        scale=button.scale,
        padding_left=button.padding_left,
        padding_top=button.padding_top,
        padding_right=button.padding_right,
        padding_bottom=button.padding_bottom,
        decorations=(
            None
            if button.decorations is None
            else [_deco(d, ctx) for d in button.decorations]
        ),
        style=dui1.ButtonStyle(button.style.value),
        default=button.default,
        selected=button.selected,
        icon=_ref_str_opt(button.icon),
        icon_scale=button.icon_scale,
        icon_color=button.icon_color,
        depth_range=button.depth_range,
        widget_id=button.widget_id,
        debug=button.debug,
    )


def _decos_opt(
    decos: list[dui2.Decoration] | None, ctx: LanguageStringNameDecodeContext
) -> list[dui1.Decoration] | None:
    """Transcode an optional decoration list (``None`` passes through)."""
    return None if decos is None else [_deco(d, ctx) for d in decos]


def _deco(
    deco: dui2.Decoration, ctx: LanguageStringNameDecodeContext
) -> dui1.Decoration:
    if isinstance(deco, dui2.Text):
        return dui1.Text(
            text=ctx.decode(deco.text),
            is_lstr=False,
            wrap=deco.wrap,
            position=deco.position,
            size=deco.size,
            scale=deco.scale,
            h_align=dui1.HAlign(deco.h_align.value),
            v_align=dui1.VAlign(deco.v_align.value),
            color=deco.color,
            flatness=deco.flatness,
            shadow=deco.shadow,
            highlight=deco.highlight,
            depth_range=deco.depth_range,
            debug=deco.debug,
        )
    if isinstance(deco, dui2.Image):
        # Textures/meshes are language-independent; the qualified
        # ``<apverid>:<name>`` ref the engine resolves is just the flattened
        # form of our typed ref (no decode needed).
        return dui1.Image(
            texture=_ref_str(deco.texture),
            position=deco.position,
            size=deco.size,
            color=deco.color,
            h_align=dui1.HAlign(deco.h_align.value),
            v_align=dui1.VAlign(deco.v_align.value),
            tint_texture=_ref_str_opt(deco.tint_texture),
            tint_color=deco.tint_color,
            tint2_color=deco.tint2_color,
            mask_texture=_ref_str_opt(deco.mask_texture),
            mesh_opaque=_ref_str_opt(deco.mesh_opaque),
            mesh_transparent=_ref_str_opt(deco.mesh_transparent),
            highlight=deco.highlight,
            depth_range=deco.depth_range,
        )
    if isinstance(deco, dui2.DisplayItem):
        # DisplayItem wrappers localize their own text client-side;
        # straight field copy.
        return dui1.DisplayItem(
            wrapper=deco.wrapper,
            position=deco.position,
            size=deco.size,
            style=dui1.DisplayItemStyle(deco.style.value),
            text_color=deco.text_color,
            highlight=deco.highlight,
            depth_range=deco.depth_range,
            debug=deco.debug,
        )
    return dui1.UnknownDecoration()


def _ref_str(ref: TextureRef | MeshRef) -> str:
    """Flatten a typed asset ref to the engine's ``<apverid>:<name>`` form."""
    return f'{ref.apverid}:{ref.name}'


def _ref_str_opt(ref: TextureRef | MeshRef | None) -> str | None:
    """Flatten an optional typed asset ref (``None`` passes through)."""
    return None if ref is None else _ref_str(ref)


def _action(action: dui2.Action) -> dui1.Action:
    if isinstance(action, dui2.Browse):
        return dui1.Browse(
            request=_request(action.request),
            default_sound=action.default_sound,
        )
    if isinstance(action, dui2.Replace):
        return dui1.Replace(
            request=_request(action.request),
            default_sound=action.default_sound,
        )
    if isinstance(action, dui2.Local):
        return dui1.Local(
            close_window=action.close_window,
            default_sound=action.default_sound,
            immediate_client_effects=action.immediate_client_effects,
            immediate_local_action=action.immediate_local_action,
            immediate_local_action_args=action.immediate_local_action_args,
        )
    return dui1.UnknownAction()


def _request(request: dui2.Request) -> dui1.Request:
    return dui1.Request(
        path=request.path,
        method=dui1.RequestMethod(request.method.value),
        args=request.args,
    )
