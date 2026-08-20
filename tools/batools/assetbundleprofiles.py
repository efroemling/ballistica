# Released under the MIT License. See LICENSE for details.
#
"""Declarative definitions of asset-package *bundle profiles*.

A *bundle profile* names the set of asset packages baked into a
particular build, each with its texture profile / quality / language.
:func:`batools.pcommands2.asset_bundle_build` assembles a profile into
``.cache/asset_bundle/<profile>/`` and the ``stage_build`` pcommand
copies that into the build's ``ba_data/``. The two agree purely on the
profile *name* (the cache dir is namespaced by it), so they can't drift.

Today's profiles are 'minimal' -- just the builtin construct package
(``gui-minimal`` with real fallback-flavor textures, ``headless-minimal``
with null textures). New profiles -- e.g. a desktop build that also
bundles a platform-flavored ``baclassicassets`` -- are added here as plain
data. The assemble + stage + runtime machinery is already package-plural
(the bundle manifest is keyed by apverid and every consumer iterates it),
so carrying additional packages needs no code changes -- only a new
entry below (and, for a new package, its projectconfig pin).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BundlePackage:
    """One asset package within a bundle profile."""

    #: projectconfig field holding this package's pinned apverid (e.g.
    #: ``'assets'`` for the builtin construct package). Resolved to a
    #: concrete apverid at assemble time.
    projectconfig_key: str

    #: Texture flavor to assemble. ``'null'`` ships a single shared
    #: empty blob per logical texture (headless builds); real flavors
    #: ship image data (``'fallback_v1'`` today; ``'desktop_v1'`` /
    #: ``'astc'`` / ... as per-platform flavors come online).
    texture_profile: str

    #: Texture quality tier (e.g. ``'regular'``, ``'high'``).
    texture_tier: str

    #: Language bucket to include (e.g. ``'eng'``).
    language: str


@dataclass(frozen=True)
class BundleProfile:
    """A named set of asset packages to bundle into a build."""

    name: str
    packages: tuple[BundlePackage, ...]


# The builtin/construct package, pinned via projectconfig's "assets"
# field. The minimal profiles carry only this -- the gui one with real
# (fallback-flavor) textures, the headless one with null textures (same
# wrapper-module layout, no image data).
_BUILTINS_GUI = BundlePackage(
    projectconfig_key='assets',
    texture_profile='fallback_v1',
    texture_tier='regular',
    language='eng',
)
_BUILTINS_HEADLESS = BundlePackage(
    projectconfig_key='assets',
    texture_profile='null',
    texture_tier='regular',
    language='eng',
)

PROFILES: dict[str, BundleProfile] = {
    'gui-minimal': BundleProfile(name='gui-minimal', packages=(_BUILTINS_GUI,)),
    'headless-minimal': BundleProfile(
        name='headless-minimal', packages=(_BUILTINS_HEADLESS,)
    ),
}


def get_profile(name: str) -> BundleProfile:
    """Look up a bundle profile by name (or raise ``CleanError``)."""
    from efro.error import CleanError

    profile = PROFILES.get(name)
    if profile is None:
        valid = ', '.join(sorted(PROFILES))
        raise CleanError(
            f"Unknown asset-bundle profile '{name}'."
            f' Valid profiles: {valid}.'
        )
    return profile
