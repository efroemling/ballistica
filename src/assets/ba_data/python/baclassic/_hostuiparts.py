# Released under the MIT License. See LICENSE for details.
#
"""Building blocks for host-ui pages.

The default pages (stats, party member, player, kick vote) are built
from these, and so can yours: they're public (``baclassic.host_ui_text``
and friends), so a page copied from ours keeps working with them. They
cover what pages can't get at through public api alone, such as how a
player's icon and name draw as they do in game.
"""

import logging
from typing import TYPE_CHECKING

from efro.util import strip_exception_tracebacks
from efro.dataclassio import dataclass_from_json
import bacommon.depiction as bdep
import bacommon.docui.v2 as dui2
from bacommon.langstr import LangStrSpec, LangStrSpecValue

import babase
import bascenev1
from bascenev1 import _classicassets, _commonassets, _classiccatalogassets

if TYPE_CHECKING:
    from typing import Sequence

#: The icon size the placeholder's '?' is scaled for.
_REFERENCE_ICON_SIZE = 48.0


def host_ui_text(text: str | babase.LangStr | LangStrSpec) -> LangStrSpec:
    """Text for a host-ui page, as doc-ui wants it.

    Plain strings show as-is; a language-string (``babase.LangStr``)
    shows in each client's own language, and must come from one of the
    host's own asset-packages (clients refuse anything else). A spec
    passes through.
    """
    if isinstance(text, str):
        return LangStrSpecValue.literal(text)
    if isinstance(text, babase.LangStr):
        return dataclass_from_json(LangStrSpec, text.to_resource_json())
    return text


def host_ui_gone_page() -> dui2.Response:
    """For someone no longer here: say so, with an Ok to leave.

    :meta private:
    """
    return dui2.Response(
        page=dui2.Page(
            title=LangStrSpecValue.literal(''),
            rows=[
                dui2.ButtonRow(
                    title=host_ui_text(
                        _classicassets.strings.host_ui.player_gone
                    ),
                    buttons=[
                        dui2.Button(
                            label=host_ui_text(
                                _commonassets.strings.actions.ok
                            ),
                            action=dui2.Local(close_window=True),
                            size=(200.0, 70.0),
                            style=dui2.ButtonStyle.MEDIUM,
                        )
                    ],
                    center_title=True,
                    center_content=True,
                    padding_top=30.0,
                )
            ],
            center_vertically=True,
        )
    )


def host_ui_player_icon(
    player: bascenev1.SessionPlayer, center: tuple[float, float], size: float
) -> list[dui2.Decoration]:
    """A player's icon, as page decorations centered at ``center``.

    Drawn as it is in game (their team's color in team games): their
    icon depiction if they have one; else their old-style icon if it
    can be shown; else a faint box with a '?' holding the spot (bots,
    say).
    """
    icon = _depiction_from_json(player.get_icon_depiction_json())
    if icon is not None:
        return [
            dui2.Depiction(depiction=icon, position=center, size=(size, size))
        ]
    if (legacy_icon := _legacy_icon(player, center, size)) is not None:
        # Players on legacy profiles or random looks have their
        # old-style icon instead (a tinted character texture).
        return [legacy_icon]
    box = size * 0.8
    return [
        dui2.Image(
            texture=_commonassets.textures.white,
            position=center,
            size=(box, box),
            color=(1.0, 1.0, 1.0, 0.08),
        ),
        dui2.Text(
            text=LangStrSpecValue.literal('?'),
            position=center,
            size=(box, box),
            scale=0.9 * size / _REFERENCE_ICON_SIZE,
            color=(1.0, 1.0, 1.0, 0.25),
        ),
    ]


def host_ui_player_name(player: bascenev1.SessionPlayer) -> bdep.Depiction:
    """A player's name for a page, as a depiction.

    Shown as in game: shortened and numbered as
    :meth:`~bascenev1.SessionPlayer.getname` is (the depiction by its
    ``max_chars`` and ``number``), since that's what everyone sees and
    what tells repeated names apart, and in their color. Players with
    no name depiction of their own (bots, say) get a plain one of their
    name. Put it on a page with a ``bacommon.docui.v2.Depiction``
    decoration.
    """
    name = _depiction_from_json(player.get_name_depiction_json())
    if name is None:
        # (getname() is already shortened and numbered.)
        return bdep.NameDepiction(
            bascenev1.plain_name_json(player.getname()),
            color_override=_rgb(player.color),
        )
    if isinstance(name, bdep.NameDepiction):
        name.max_chars = bdep.IN_GAME_NAME_MAX_CHARS
        name.number = player.get_name_number()
    return name


def _legacy_icon(
    player: bascenev1.SessionPlayer, center: tuple[float, float], size: float
) -> dui2.Image | None:
    """A player's old-style icon as an image, if it can be shown.

    That is, if it is all from our own asset-packages (clients refuse
    anything else, and with it the whole page). Icons that aren't (a
    mod's legacy texture names, say) give None.
    """
    info = player.get_icon_info()
    try:
        texture = bascenev1.texture_spec_from_ref(info['texture'])
        tint_texture = bascenev1.texture_spec_from_ref(info['tint_texture'])
    except KeyError, ValueError:
        return None
    mask_texture = _classiccatalogassets.textures.character_icon_mask
    scanresults = babase.app.meta.scanresults
    universe = set() if scanresults is None else set(scanresults.asset_packages)
    # (Reading identity, not building a path.)
    # pylint: disable-next=protected-access
    if any(t._apvernum not in universe for t in (texture, tint_texture)):
        return None
    tint3 = info.get('tint3_color')
    return dui2.Image(
        texture=texture,
        tint_texture=tint_texture,
        tint_color=_rgb(info['tint_color']),
        tint2_color=_rgb(info['tint2_color']),
        tint3_color=None if tint3 is None else _rgb(tint3),
        mask_texture=mask_texture,
        position=center,
        size=(size, size),
    )


def _rgb(color: Sequence[float]) -> tuple[float, float, float]:
    return (float(color[0]), float(color[1]), float(color[2]))


def _depiction_from_json(depjson: str | None) -> bdep.Depiction | None:
    """A depiction from our own json (None for None or invalid json)."""
    if depjson is None:
        return None
    # Not lossy: this is our own data, and lossy objects can't be
    # written back out (which serving it does).
    try:
        return dataclass_from_json(bdep.Depiction, depjson)
    except Exception as exc:
        logging.exception('Invalid depiction json.')
        strip_exception_tracebacks(exc)
        return None
