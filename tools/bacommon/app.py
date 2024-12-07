# Released under the MIT License. See LICENSE for details.
#
"""Common high level values/functionality related to apps."""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated

from efro.dataclassio import ioprepped, IOAttrs

if TYPE_CHECKING:
    pass


class AppInterfaceIdiom(Enum):
    """A general form-factor or method of experiencing a Ballistica app.

    Note that it is possible for a running app to switch idioms (for
    instance if a mobile device or computer is connected to a TV).
    """

    PHONE = 'phone'
    TABLET = 'tablet'
    DESKTOP = 'desktop'
    TV = 'tv'
    XR = 'xr'


class AppExperience(Enum):
    """A particular experience that can be provided by a Ballistica app.

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
    visible to client apps designed for that play style.
    """

    # An experience that is supported everywhere. Used for the default
    # empty AppMode when starting the app, etc.
    EMPTY = 'empty'

    # The traditional BombSquad experience: multiple players using
    # traditional game controllers (or touch screen equivalents) in a
    # single arena small enough for all action to be viewed on a single
    # screen.
    MELEE = 'melee'

    # The traditional BombSquad Remote experience; buttons on a
    # touch-screen allowing a mobile device to be used as a game
    # controller.
    REMOTE = 'remote'


class AppArchitecture(Enum):
    """Processor architecture the App is running on."""

    ARM = 'arm'
    ARM64 = 'arm64'
    X86 = 'x86'
    X86_64 = 'x86_64'


class AppPlatform(Enum):
    """Overall platform a Ballistica build is targeting.

    Each distinct flavor of an app has a unique combination of
    AppPlatform and AppVariant. Generally platform describes a set of
    hardware, while variant describes a destination or purpose for the
    build.
    """

    MAC = 'mac'
    WINDOWS = 'windows'
    LINUX = 'linux'
    ANDROID = 'android'
    IOS = 'ios'
    TVOS = 'tvos'


class AppVariant(Enum):
    """A unique Ballistica build type within a single platform.

    Each distinct flavor of an app has a unique combination of
    AppPlatform and AppVariant. Generally platform describes a set of
    hardware, while variant describes a destination or purpose for the
    build.
    """

    # Default builds.
    GENERIC = 'generic'

    # Builds intended for public testing (may have some extra checks
    # or logging enabled).
    TEST = 'test'

    # Various stores.
    AMAZON_APPSTORE = 'amazon_appstore'
    GOOGLE_PLAY = 'google_play'
    APP_STORE = 'app_store'
    WINDOWS_STORE = 'windows_store'
    STEAM = 'steam'
    META = 'meta'
    EPIC_GAMES_STORE = 'epic_games_store'

    # Other.
    ARCADE = 'arcade'
    DEMO = 'demo'


@ioprepped
@dataclass
class AppInstanceInfo:
    """General info about an individual running app."""

    name = Annotated[str, IOAttrs('n')]

    engine_version = Annotated[str, IOAttrs('ev')]
    engine_build = Annotated[int, IOAttrs('eb')]

    platform = Annotated[AppPlatform, IOAttrs('p')]
    variant = Annotated[AppVariant, IOAttrs('va')]
    architecture = Annotated[AppArchitecture, IOAttrs('a')]
    os_version = Annotated[str | None, IOAttrs('o')]

    interface_idiom: Annotated[AppInterfaceIdiom, IOAttrs('i')]
    locale: Annotated[str, IOAttrs('l')]

    device: Annotated[str | None, IOAttrs('d')]
