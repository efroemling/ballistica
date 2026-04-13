# Released under the MIT License. See LICENSE for details.
#
"""Common high level values/functionality related to Ballistica apps."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# NOTE TO SELF - These are used on various server components, so be sure
# to update ALL servers before running any clients that might be using
# newly defined values. Alterntely we could set up fallback values but I
# don't think that will be necessary and could mask problems.


class AppInterfaceIdiom(Enum):
    """A general form-factor or method of experiencing a Ballistica app.

    Note that it may be possible for a running app to switch idioms (for
    instance if a mobile device or computer is connected to a TV).
    """

    #: Small screen; assumed to have touch as primary input.
    PHONE = 'phone'

    #: Medium size screen; assumed to have touch as primary input.
    TABLET = 'tablet'

    #: Screen with medium amount of detail visible; assumed to have game
    #: controller(s) as primary input. Note that this covers handheld or
    #: arcade cabinet scenarios in addition to tv-connected consoles.
    CONSOLE = 'console'

    #: Screen with high amount of detail visible; assumed to have
    #: keyboard/mouse as primary input.
    DESKTOP = 'desktop'

    #: Displayed over or in place of of the real world on a headset;
    #: assumed to have hand tracking or spatial controllers as primary
    #: input.
    XR_HEADSET = 'xr_headset'

    #: Displayed over or instead of the real world on a small screen;
    #: assumed to have device movement augmented by physical or
    #: touchscreen controls as primary input.
    XR_PHONE = 'xr_phone'

    #: Displayed over or instead of the real world on a medium size
    #: screen; assumed to have device movement augmented by physical or
    #: touchscreen controls as primary input.
    XR_TABLET = 'xr_tablet'

    #: The app has no interface (generally is acting as a server).
    HEADLESS = 'headless'


# UPDATE: Don't think this will be necessary. Will keep it around for a
# moment in case I change my mind. Current plan is to just have AppModes
# check for compatible AppInterfaceIdioms or whatever else as part of
# their can_handle_intent() call.

# class AppExperience(Enum):
#     """A type of experience provided by a Ballistica app.

#     This metric is used to ensure that an :class:`~babase.AppMode` can
#     be properly presented by a running app. Requirements for supporting
#     an experience can include things like running in a particular
#     :class:`AppInterfaceIdiom` or having particular features or input
#     device(s) present.
#     """

#     #: A special experience that is supported everywhere. Used for the
#     #: default empty AppMode when starting the app, etc.
#     EMPTY = 'empty'

#     #: The traditional BombSquad experience - multiple players using
#     #: game controllers (or touch screen equivalents) in a single arena
#     #: small enough for all action to be viewed on a single screen.
#     MELEE = 'melee'

#     #: The traditional BombSquad Remote experience; buttons on a
#     #: touch-screen allowing a mobile device to be used as a game
#     #: controller.
#     REMOTE = 'remote'


class AppArchitecture(Enum):
    """Processor architecture an app can be running on."""

    UNKNOWN = 'unknown'
    ARM = 'arm'
    ARM64 = 'arm64'
    X86 = 'x86'
    X86_64 = 'x86_64'


class AppPlatform(Enum):
    """Overall platform a build can target.

    Each distinct flavor of an app has a unique combination of
    AppPlatform and AppVariant. Generally platform describes a set of
    hardware, while variant describes a destination or purpose for the
    build.
    """

    UNKNOWN = 'unknown'
    MACOS = 'macos'
    WINDOWS = 'windows'
    LINUX = 'linux'
    ANDROID = 'android'
    IOS = 'ios'
    TVOS = 'tvos'


class AppVariant(Enum):
    """A unique Ballistica build variation within a single platform.

    Each distinct permutation of an app has a unique combination of
    :class:`AppPlatform` and ``AppVariant``. Generally platform
    describes a set of hardware, while variant describes a destination
    or purpose for the build.
    """

    #: Default builds.
    GENERIC = 'generic'

    #: Particular builds intended for public testing (may have some extra
    #: checks or logging enabled).
    TEST_BUILD = 'test_build'

    # Various stores.
    AMAZON_APPSTORE = 'amazon_appstore'
    GOOGLE_PLAY = 'google_play'
    APPLE_APP_STORE = 'apple_app_store'
    WINDOWS_STORE = 'windows_store'
    STEAM = 'steam'
    META = 'meta'
    EPIC_GAMES_STORE = 'epic_games_store'

    # Other.
    ARCADE = 'arcade'
    DEMO = 'demo'
    CARDBOARD = 'cardboard'
