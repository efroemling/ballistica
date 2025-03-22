# Released under the MIT License. See LICENSE for details.
#
"""Common high level values/functionality related to Ballistica apps."""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated

from efro.dataclassio import ioprepped, IOAttrs

from bacommon.locale import Locale

if TYPE_CHECKING:
    pass


class AppInterfaceIdiom(Enum):
    """A general form-factor or method of experiencing a Ballistica app.

    Note that it may be possible for a running app to switch idioms (for
    instance if a mobile device or computer is connected to a TV).
    """

    #: Small screen; assumed to have touch as primary input.
    PHONE = 'phn'

    #: Medium size screen; assumed to have touch as primary input.
    TABLET = 'tab'

    #: Medium size screen; assumed to have game controller as primary
    #: input.
    HANDHELD = 'hnd'

    #: Large screen with high amount of detail visible; assumed to have
    #: keyboard/mouse as primary input.
    DESKTOP = 'dsk'

    #: Large screen with medium amount of detail visible; assumed to have
    #: game controller as primary input.
    TV = 'tv'

    #: Displayed over or in place of of the real world on a headset;
    #: assumed to have hand tracking or spacial controllers as primary
    #: input.
    XR_HEADSET = 'xrh'

    #: Displayed over or instead of the real world on a screen; assumed
    #: to have device movement augmented by physical or touchscreen
    #: controls as primary input.
    XR_SCREEN = 'xrs'


class AppExperience(Enum):
    """A particular experience provided by a Ballistica app.

    This is one metric used to isolate different playerbases from each
    other where there might be no technical barriers doing so. For
    example, a casual one-hand-playable phone game and an augmented
    reality tabletop game may both use the same scene-versions and
    networking-protocols and whatnot, but it would make no sense to
    allow players of one to join servers of the other. AppExperience can
    be used to keep these player bases separate.

    Generally a single Ballistica app targets a single AppExperience.
    This is not a technical requirement, however. A single app may
    support multiple experiences, or there may be multiple apps
    targeting one experience. Cloud components such as leagues are
    generally associated with an AppExperience so that they are only
    visible to client apps designed for that play style, and the same is
    true for games joinable over the local network, bluetooth, etc.
    """

    #: An experience that is supported everywhere. Used for the default
    #: empty AppMode when starting the app, etc.
    EMPTY = 'empt'

    #: The traditional BombSquad experience - multiple players using
    #: game controllers (or touch screen equivalents) in a single arena
    #: small enough for all action to be viewed on a single screen.
    MELEE = 'mlee'

    #: The traditional BombSquad Remote experience; buttons on a
    #: touch-screen allowing a mobile device to be used as a game
    #: controller.
    REMOTE = 'rmt'


class AppArchitecture(Enum):
    """Processor architecture an app can be running on."""

    ARM = 'arm'
    ARM64 = 'arm64'
    X86 = 'x86'
    X86_64 = 'x64'


class AppPlatform(Enum):
    """Overall platform a build can target.

    Each distinct flavor of an app has a unique combination of
    AppPlatform and AppVariant. Generally platform describes a set of
    hardware, while variant describes a destination or purpose for the
    build.
    """

    MAC = 'mac'
    WINDOWS = 'win'
    LINUX = 'lin'
    ANDROID = 'andr'
    IOS = 'ios'
    TVOS = 'tvos'


class AppVariant(Enum):
    """A unique Ballistica build type within a single platform.

    Each distinct flavor of an app has a unique combination of
    AppPlatform and AppVariant. Generally platform describes a set of
    hardware, while variant describes a destination or purpose for the
    build.
    """

    #: Default builds.
    GENERIC = 'gen'

    #: Builds intended for public testing (may have some extra checks
    #: or logging enabled).
    TEST = 'tst'

    # Various stores.
    AMAZON_APPSTORE = 'amzn'
    GOOGLE_PLAY = 'gpl'
    APPLE_APP_STORE = 'appl'
    WINDOWS_STORE = 'wins'
    STEAM = 'stm'
    META = 'meta'
    EPIC_GAMES_STORE = 'epic'

    # Other.
    ARCADE = 'arcd'
    DEMO = 'demo'


class AppName(Enum):
    """A predefined Ballistica app name.

    This encompasses official or well-known apps. Other app projects
    should set this to CUSTOM and provide a 'name_custom' value.
    """

    BOMBSQUAD = 'bs'
    CUSTOM = 'c'


@ioprepped
@dataclass
class AppInstanceInfo:
    """General info about an individual running ballistica app."""

    name: Annotated[str, IOAttrs('name')]
    name_custom: Annotated[
        str | None, IOAttrs('namc', soft_default=None, store_default=False)
    ]

    engine_version: Annotated[str, IOAttrs('evrs')]
    engine_build: Annotated[int, IOAttrs('ebld')]

    platform: Annotated[AppPlatform, IOAttrs('plat')]
    variant: Annotated[AppVariant, IOAttrs('vrnt')]
    architecture: Annotated[AppArchitecture, IOAttrs('arch')]
    os_version: Annotated[str | None, IOAttrs('osvr')]

    interface_idiom: Annotated[AppInterfaceIdiom, IOAttrs('intf')]
    locale: Annotated[Locale, IOAttrs('loc')]

    #: OS-specific string describing the device running the app.
    device: Annotated[str | None, IOAttrs('devc')]
