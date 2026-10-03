# Released under the MIT License. See LICENSE for details.
#
"""Declarative definitions of asset-package *bundle profiles*.

A *bundle profile* names the set of asset packages baked into a
particular build, each with its texture profiles / tier / languages.
:func:`batools.pcommands2.asset_bundle_build` assembles a profile into
``.cache/asset_bundle/<cache-dir>/`` and the ``stage_build`` pcommand
copies that into the build's ``ba_data/``. The two agree purely on the
cache-dir name (see :func:`bundle_cache_dirname`), so they can't drift.

Two kinds of profile exist:

- **Minimal** profiles (``gui-minimal`` / ``headless-minimal``) carry a
  fixed package list -- just the builtin construct package -- at the
  baseline flavors (English, ``fallback_v1`` or ``null`` textures).
  Every ordinary build stages one of these; anything else is
  downloaded at first launch.
- The **``store``** profile is what shipping store builds use: every
  asset package the bundled Python code declares a dependency on
  (discovered by the same ``# ba_meta require asset-package`` scan
  construct-mode runs at boot -- so the bundle can never drift from
  what the code actually needs), at the build target's *device-native*
  texture flavor, with *every* language flavor. That is exactly the
  set required to boot and play offline in any locale. The builtin
  package additionally carries the universal ``fallback_v1`` texture
  flavor: it is the bootstrap floor construct-mode can always fall
  back to (and from which it can then download the rest) should the
  native flavor ever be unusable. See asset-packages.md decision #10.

The native texture flavor is a *device-fixed* dimension (decision
#5/#10), so ``store`` is parameterized by *form factor*: a desktop
store build bundles ``desktop_v1`` (BC7), a mobile one ``mobile_v1``
(ASTC). The two materializations cache separately
(``store-desktop`` / ``store-mobile``).
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from bacommon.assetpackage import ApverNum

#: Texture tier every profile bundles today.
_TIER = 'regular'

#: Device-native texture profile per build form factor (mirrors the
#: runtime selection in ``Assets::PreferredTextureProfile``).
NATIVE_TEXTURE_PROFILE_BY_FORM_FACTOR: dict[str, str] = {
    'desktop': 'desktop_v1',
    'mobile': 'mobile_v1',
}

#: The universal uncompressed texture flavor (the construct-mode
#: bootstrap floor; see ``_BUCKET_FALLBACKS`` in babase).
FALLBACK_TEXTURE_PROFILE = 'fallback_v1'


@dataclass(frozen=True)
class BundlePackage:
    """One asset package within a materialized bundle profile."""

    #: The asset-package-version's numeric id.
    apvernum: ApverNum

    #: Primary texture flavor, assembled with every language in
    #: ``languages``. ``'null'`` ships a single shared empty blob per
    #: logical texture (headless builds); real flavors ship image data
    #: (``'fallback_v1'``, ``'desktop_v1'``, ``'mobile_v1'``).
    texture_profile: str

    #: Texture quality tier (e.g. ``'regular'``).
    texture_tier: str

    #: Language buckets to include (e.g. ``('eng',)``).
    languages: tuple[str, ...]

    #: Additional texture flavors to bundle alongside the primary one.
    #: A textures coord doesn't vary by language, so each of these is
    #: assembled with just the first language -- it contributes only
    #: its ``textures/<profile>...`` coord.
    extra_texture_profiles: tuple[str, ...] = ()


@dataclass(frozen=True)
class BundleProfile:
    """A named bundle profile.

    ``form_factors`` is empty for profiles whose contents don't depend
    on the build target; otherwise it lists the accepted values and
    the caller must supply one (the native texture flavor and the
    cache dir both derive from it).
    """

    name: str
    form_factors: tuple[str, ...] = ()


PROFILES: dict[str, BundleProfile] = {
    'gui-minimal': BundleProfile(name='gui-minimal'),
    'headless-minimal': BundleProfile(name='headless-minimal'),
    'store': BundleProfile(
        name='store',
        form_factors=tuple(NATIVE_TEXTURE_PROFILE_BY_FORM_FACTOR),
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


def bundle_cache_dirname(
    profile: BundleProfile, form_factor: str | None
) -> str:
    """The ``.cache/asset_bundle/<dirname>`` a profile materializes into.

    Form-factor-parameterized profiles get one dir per form factor
    (``store-desktop``); others use the bare profile name. Validates
    that a form factor is supplied exactly when the profile needs one.
    """
    from efro.error import CleanError

    if profile.form_factors:
        valid = ', '.join(profile.form_factors)
        if form_factor is None:
            raise CleanError(
                f"Asset-bundle profile '{profile.name}' needs a form"
                f' factor; valid values: {valid}.'
            )
        if form_factor not in profile.form_factors:
            raise CleanError(
                f"Invalid form factor '{form_factor}' for asset-bundle"
                f" profile '{profile.name}'; valid values: {valid}."
            )
        return f'{profile.name}-{form_factor}'
    if form_factor is not None:
        raise CleanError(
            f"Asset-bundle profile '{profile.name}' is not"
            ' form-factor-specific; do not pass one.'
        )
    return profile.name


def form_factor_for_staging_platform(platform_arg: str) -> str:
    """Map a ``stage_build`` platform arg to a bundle form factor."""
    if platform_arg in ('-android', '-xcode-ios', '-xcode-tvos'):
        return 'mobile'
    return 'desktop'


def all_bundle_languages() -> tuple[str, ...]:
    """Every language flavor a client can actually request.

    The runtime always derives its locale through
    :class:`bacommon.locale.LocaleResolved` (obsolete
    :class:`~bacommon.locale.Locale` values never get requested), so
    the resolvable set is exactly the set of ``language/<x>`` buckets
    a fully-offline build must carry.
    """
    from bacommon.locale import LocaleResolved

    return tuple(sorted({lr.locale.value for lr in LocaleResolved}))


_g_builtin_apvernums: dict[str, ApverNum] = {}


def _builtin_apvernum(projroot: Path) -> ApverNum:
    """The builtin construct package's numeric id.

    Looked up from projectconfig's ``"assets"`` string pin (the one
    source every build environment syncs; some lack the C++ tree or the
    Python wrappers). Bundle builds talk to the server anyway.
    """
    from efro.error import CleanError
    from efrotools.project import getprojectconfig

    from batools.builtinassetids import fetch_apvernum

    apverid = getprojectconfig(projroot).get('assets')
    if not isinstance(apverid, str) or not apverid:
        raise CleanError(
            "Need a string 'assets' value in projectconfig; got"
            f' {type(apverid).__name__} value {apverid!r}.'
        )
    num = _g_builtin_apvernums.get(apverid)
    if num is None:
        num = _g_builtin_apvernums[apverid] = fetch_apvernum(projroot, apverid)
    return num


def _scanned_apvernums(projroot: Path) -> list[ApverNum]:
    """Asset packages the bundled Python code declares it requires.

    Runs the same ``# ba_meta require asset-package`` scan over
    ``src/assets/ba_data/python`` that construct-mode runs at boot, so
    what gets bundled is by construction what the shipped code will
    demand (decision #7: build-time meta-scan == runtime meta-scan).
    """
    from efro.error import CleanError
    from bacommon.metascan import DirectoryScan

    python_root = projroot / 'src/assets/ba_data/python'
    if not python_root.is_dir():
        raise CleanError(f'Python source root not found: {python_root}')
    scanner = DirectoryScan(paths=[str(python_root)])
    scanner.run()
    if scanner.results.announce_errors_occurred:
        raise CleanError(
            'Errors occurred meta-scanning bundled Python for asset-package'
            ' requirements; see warnings above.'
        )
    return sorted(scanner.results.asset_packages)


def materialize_profile(
    profile: BundleProfile, form_factor: str | None, projroot: Path
) -> list[BundlePackage]:
    """Turn a profile (+ form factor) into the concrete package list.

    Packages are named by numeric id: the builtin one from its C++
    splice, the rest from the bundled code's ``require asset-package``
    lines (always concrete; pin-state mutation lives exclusively in
    ``tools/pcommand assetpins``).
    """
    from efro.error import CleanError

    # Validates the form-factor/profile pairing up front.
    bundle_cache_dirname(profile, form_factor)

    packages: list[BundlePackage]
    if profile.name == 'gui-minimal':
        packages = [
            BundlePackage(
                apvernum=_builtin_apvernum(projroot),
                texture_profile=FALLBACK_TEXTURE_PROFILE,
                texture_tier=_TIER,
                languages=('eng',),
            )
        ]
    elif profile.name == 'headless-minimal':
        packages = [
            BundlePackage(
                apvernum=_builtin_apvernum(projroot),
                texture_profile='null',
                texture_tier=_TIER,
                languages=('eng',),
            )
        ]
    elif profile.name == 'store':
        assert form_factor is not None
        native = NATIVE_TEXTURE_PROFILE_BY_FORM_FACTOR[form_factor]
        builtin = _builtin_apvernum(projroot)
        languages = all_bundle_languages()
        apvernums = _scanned_apvernums(projroot)
        if builtin not in apvernums:
            raise CleanError(
                f'Builtin package {builtin} (the C++ splice) is not among'
                f' the packages bundled code requires ({apvernums}); the'
                ' builtin wrapper and the pin have drifted.'
            )
        packages = [
            BundlePackage(
                apvernum=apvernum,
                texture_profile=native,
                texture_tier=_TIER,
                languages=languages,
                # Only the builtin/bootstrap package carries the
                # universal fallback alongside the native flavor.
                extra_texture_profiles=(
                    (FALLBACK_TEXTURE_PROFILE,) if apvernum == builtin else ()
                ),
            )
            for apvernum in apvernums
        ]
    else:
        raise CleanError(f"Profile '{profile.name}' has no materializer.")

    return packages
