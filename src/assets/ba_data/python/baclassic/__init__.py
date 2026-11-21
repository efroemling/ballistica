# Released under the MIT License. See LICENSE for details.
#
"""Components for the classic BombSquad experience.

This package/feature-set contains functionality related to the classic
BombSquad experience. Note that much legacy BombSquad code is still a
bit tangled and thus this feature-set is largely inseperable from
:mod:`bascenev1` and :mod:`bauiv1`. Future feature-sets will be
designed in a more modular way.
"""

# ba_meta require api 9

# Note: Stuff in this module mostly exists for type-checking and docs
# generation and should generally not be imported or used at runtime.
# Generally all interaction with this feature-set should go through
# `ba*.app.classic`.

import logging
from typing import TYPE_CHECKING

from _baclassic import reload_hooks
from baclassic._appmode import ClassicAppMode, ClassicAppModeConfig
from baclassic._appsubsystem import ClassicAppSubsystem
from baclassic._achievement import Achievement, AchievementSubsystem
from baclassic._chest import (
    ChestAppearanceDisplayInfo,
    CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT,
    CHEST_APPEARANCE_DISPLAY_INFOS,
)
from baclassic._displayitem import (
    show_display_item,
    display_item_decorations,
    depiction_assets,
)
from baclassic._music import MusicPlayer
from baclassic._clienteffect import (
    ClientEffectContext,
    EffectTarget,
    EffectTargets,
)

# Host-ui is re-exported lazily: it pulls in the whole doc-ui wire
# format, and most runs never host anyone or join a host that uses it,
# so loading it at launch was a waste (~90ms on a mid-range phone).
# These names load on first access instead. app.classic.host_ui loads
# them in the background ahead of need (see ClassicAppSubsystem).
#
# TODO: Once we're on Python 3.15+, replace this with PEP 810 lazy
# imports ('lazy from baclassic._hostui import ...') and drop
# __getattr__/__dir__ below.
_LAZY_EXPORTS: dict[str, str] = {
    'HostUIButton': 'baclassic._hostuibutton',
    'HostUIClientPage': 'baclassic._hostuimembers',
    'HostUIPlayerPage': 'baclassic._hostuimembers',
    'HostUISubsystem': 'baclassic._hostui',
    'HostUIHandler': 'baclassic._hostuihandler',
    'HostUIKickRequest': 'baclassic._hostuikick',
    'HostUIKickVote': 'baclassic._hostuikick',
    'HostUIKickVotes': 'baclassic._hostuikick',
    'KickVoteRefusal': 'baclassic._hostuikick',
    'HostUIStatsColumn': 'baclassic._hostuistats',
    'HostUIStatsContext': 'baclassic._hostuistats',
    'HostUIStatsPage': 'baclassic._hostuistats',
    'host_ui_player_icon': 'baclassic._hostuiparts',
    'host_ui_player_name': 'baclassic._hostuiparts',
    'host_ui_text': 'baclassic._hostuiparts',
}

if TYPE_CHECKING:
    from types import FunctionType

    from baclassic._hostuiparts import (
        host_ui_player_icon,
        host_ui_player_name,
        host_ui_text,
    )
    from baclassic._hostui import HostUISubsystem
    from baclassic._hostuibutton import HostUIButton
    from baclassic._hostuihandler import HostUIHandler
    from baclassic._hostuikick import (
        HostUIKickRequest,
        HostUIKickVote,
        HostUIKickVotes,
        KickVoteRefusal,
    )
    from baclassic._hostuimembers import HostUIClientPage, HostUIPlayerPage
    from baclassic._hostuistats import (
        HostUIStatsColumn,
        HostUIStatsContext,
        HostUIStatsPage,
    )


def __getattr__(name: str) -> type | FunctionType:
    modname = _LAZY_EXPORTS.get(name)
    if modname is None:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    import importlib

    value: type | FunctionType = getattr(importlib.import_module(modname), name)

    # Cache it so we only come through here once per name.
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    # Without this, tools that list our members via dir() (sphinx
    # autodoc, for one) would silently skip the lazy exports.
    return sorted({*globals(), *_LAZY_EXPORTS})


# (Pylint can't see the lazy exports above.)
# pylint: disable=undefined-all-variable
__all__ = [
    'ChestAppearanceDisplayInfo',
    'CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT',
    'CHEST_APPEARANCE_DISPLAY_INFOS',
    'ClassicAppMode',
    'ClassicAppModeConfig',
    'ClassicAppSubsystem',
    'ClientEffectContext',
    'EffectTarget',
    'EffectTargets',
    'HostUIButton',
    'HostUIClientPage',
    'HostUIHandler',
    'HostUIKickRequest',
    'HostUIKickVote',
    'HostUIKickVotes',
    'HostUIPlayerPage',
    'HostUIStatsColumn',
    'HostUIStatsContext',
    'HostUIStatsPage',
    'HostUISubsystem',
    'host_ui_player_icon',
    'host_ui_player_name',
    'host_ui_text',
    'KickVoteRefusal',
    'Achievement',
    'AchievementSubsystem',
    'show_display_item',
    'display_item_decorations',
    'depiction_assets',
    'MusicPlayer',
    'reload_hooks',
]

# We want stuff here to show up as packagename.Foo instead of
# packagename._submodule.Foo.
# UPDATE: Trying without this for now. Seems like this might cause more
# harm than good. Can flip it back on if it is missed.
# set_canonical_module_names(globals())

# Sanity check: we want to keep ballistica's dependencies and
# bootstrapping order clearly defined; let's check a few particular
# modules to make sure they never directly or indirectly import us
# before their own execs complete.
if __debug__:
    for _mdl in 'babase', '_babase':
        if not hasattr(__import__(_mdl), '_REACHED_END_OF_MODULE'):
            logging.warning(
                '%s was imported before %s finished importing;'
                ' should not happen.',
                __name__,
                _mdl,
            )
