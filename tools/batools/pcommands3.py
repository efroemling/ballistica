# Released under the MIT License. See LICENSE for details.
#
"""A nice collection of ready-to-use pcommands for this package."""

# Note: import as little as possible here at the module level to
# keep launch times fast for small snippets.
import sys
from typing import TYPE_CHECKING

from efrotools import pcommand

if TYPE_CHECKING:
    from libcst import BaseExpression
    from libcst.metadata import CodeRange


def compose_docker_gui_release() -> None:
    """Build the docker image with bombsquad cmake gui."""
    import batools.docker

    batools.docker.docker_compose(headless_build=False)


def compose_docker_gui_debug() -> None:
    """Build the docker image with bombsquad debug cmake gui."""
    import batools.docker

    batools.docker.docker_compose(headless_build=False, build_type='Debug')


def compose_docker_server_release() -> None:
    """Build the docker image with bombsquad cmake server."""
    import batools.docker

    batools.docker.docker_compose()


def compose_docker_server_debug() -> None:
    """Build the docker image with bombsquad debug cmake server."""
    import batools.docker

    batools.docker.docker_compose(build_type='Debug')


def compose_docker_arm64_gui_release() -> None:
    """Build the docker image with bombsquad cmake for arm64."""
    import batools.docker

    batools.docker.docker_compose(headless_build=False, platform='linux/arm64')


def compose_docker_arm64_gui_debug() -> None:
    """Build the docker image with bombsquad cmake for arm64."""
    import batools.docker

    batools.docker.docker_compose(
        headless_build=False, platform='linux/arm64', build_type='Debug'
    )


def compose_docker_arm64_server_release() -> None:
    """Build the docker image with bombsquad cmake server for arm64."""
    import batools.docker

    batools.docker.docker_compose(platform='linux/arm64')


def compose_docker_arm64_server_debug() -> None:
    """Build the docker image with bombsquad cmake server for arm64."""
    import batools.docker

    batools.docker.docker_compose(platform='linux/arm64', build_type='Debug')


def save_docker_images() -> None:
    """Saves bombsquad images loaded into docker."""
    import batools.docker

    batools.docker.docker_save_images()


def remove_docker_images() -> None:
    """Remove the bombsquad images loaded in docker."""
    import batools.docker

    batools.docker.docker_remove_images()


def generate_flatpak_build_env() -> None:
    """Regenerate the offline Python build env used by flatpak builds.

    Rewrites pconfig/requirements_build_lock.txt and
    pconfig/flatpak/python-build-env.yml from the main lockfile. Needs
    network access (it reads PyPI file metadata); the outputs are
    committed so the builds themselves stay offline.
    """
    import batools.flatpakbuildenv

    batools.flatpakbuildenv.generate(str(pcommand.PROJROOT))


def _github_repo() -> str:
    """Return 'owner/repo' from GITHUB_REPOSITORY or the git remote."""
    import os
    import subprocess

    from efro.error import CleanError

    try:
        return os.environ['GITHUB_REPOSITORY']
    except KeyError:
        try:
            user_plus_repo: list[str] = (
                subprocess.run(
                    'git config remote.origin.url',
                    check=True,
                    shell=True,
                    capture_output=True,
                    text=True,
                )
                .stdout.strip(' \n')
                .split('/')
            )
            return (
                user_plus_repo[-2]
                + '/'
                + user_plus_repo[-1].removesuffix('.git')
            )
        except Exception as e:
            raise CleanError(
                f'GITHUB_REPOSITORY env var not'
                f'set and git remote.origin.url not set.'
                f'{e}'
            ) from e


def generate_flathub_manifest() -> None:
    """Generate a Flathub manifest for Ballistica into build/flathub.
    This function is intended to be run within a GitHub Actions workflow.

    Replaces everything in build/flathub (except .git and flathub.json)
    with the manifest, its python-build-env module, and a generated
    bombsquad-sources.yml: git at the release's tag plus that release's
    prebuilt-inputs archive. The release is the one for the tag that
    triggered the workflow, or else the latest one.
    """
    # pylint: disable=too-many-locals
    import json
    import os
    import shutil
    import subprocess
    import urllib.request

    from efro.error import CleanError
    from efro.terminal import Clr
    from efrotools.util import writefile

    github_repo = _github_repo()
    flatpak_src_dir = os.path.join(pcommand.PROJROOT, 'pconfig', 'flatpak')
    flathub_dir = os.path.join(pcommand.PROJROOT, 'build', 'flathub')
    os.makedirs(flathub_dir, exist_ok=True)

    print(f'{Clr.BLD}Generating Flathub manifest...{Clr.RST}')

    # The flathub repo holds only what this writes; Flathub wants
    # everything the build installs to come from the app's sources.
    for name in os.listdir(flathub_dir):
        if name in {'.git', 'flathub.json'}:
            continue
        path = os.path.join(flathub_dir, name)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    for filename in ['net.froemling.bombsquad.yml', 'python-build-env.yml']:
        shutil.copy2(
            os.path.join(flatpak_src_dir, filename),
            os.path.join(flathub_dir, filename),
        )
        print(f'  Copied {filename}')

    in_tag_workflow = os.environ.get('GITHUB_REF_TYPE') == 'tag'
    ref_name = os.environ.get('GITHUB_REF_NAME')
    which = f'tags/{ref_name}' if in_tag_workflow else 'latest'
    print(f'{Clr.BLD}Fetching GitHub release info ({which})...{Clr.RST}')
    asset_name = 'bombsquad_prebuilt_inputs.tar.xz'
    try:
        api_url = f'https://api.github.com/repos/{github_repo}/releases/{which}'
        with urllib.request.urlopen(api_url) as response:
            release_data = json.loads(response.read().decode())
        tag = release_data['tag_name']
        asset = next(
            a for a in release_data['assets'] if a['name'] == asset_name
        )
    except StopIteration:
        raise CleanError(f'No {asset_name} in release {which}.') from None
    except Exception as e:
        raise CleanError(f'Failed to fetch release info: {e}') from e
    digest = asset.get('digest') or ''
    if not digest.startswith('sha256:'):
        raise CleanError(f'No SHA256 digest for {asset_name}.')
    asset_url = asset['browser_download_url']
    checksum = digest.removeprefix('sha256:')
    print(f'  Release tag: {tag}')
    print(f'  Found asset: {asset_url}')

    # Pin the git source to the commit as well as the tag, so a moved
    # tag can't change what Flathub builds. In the release workflow
    # that's GITHUB_SHA, which also covers a shallow checkout that can't
    # resolve the tag itself.
    if in_tag_workflow:
        commit = os.environ['GITHUB_SHA']
    else:
        try:
            commit = subprocess.run(
                ['git', 'rev-parse', f'{tag}^{{commit}}'],
                cwd=pcommand.PROJROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        except subprocess.CalledProcessError as e:
            raise CleanError(
                f'Could not resolve tag {tag} to a commit: {e.stderr}'
            ) from e
    print(f'  Release commit: {commit}')

    # The Flathub copy of pconfig/flatpak/bombsquad-sources.yml: the
    # code from git, and what git lacks from the release's archive,
    # extracted over the checkout.
    sources_path = os.path.join(flathub_dir, 'bombsquad-sources.yml')
    writefile(
        sources_path,
        '# Generated by generate_flathub_manifest; do not edit.\n'
        '# This file contains the precompiled assets and resources\n'
        '# for the release, which are not in git,\n'
        '# and are considered closed source.\n'
        '# The git source is pinned to the release commit\n'
        '# as well as the tag, so a moved tag cannot change\n'
        '# what Flathub builds.\n'
        '# It contains the following sources:\n'
        '# - The icon for the application\n'
        '# - The precompiled binaries and resources for the release\n'
        '- type: git\n'
        f'  url: https://github.com/{github_repo}.git\n'
        f'  tag: {tag}\n'
        f'  commit: {commit}\n'
        '- type: archive\n'
        f'  url: {asset_url}\n'
        f'  sha256: {checksum}\n'
        '  strip-components: 0\n',
    )
    print(f'  Wrote {sources_path}')

    print(f'{Clr.BLD}{Clr.GRN}Flathub manifest generation complete!{Clr.RST}')


def flatpak_prebuilt_inputs() -> None:
    """Pack the parts of a flatpak build's tree that aren't in git.

    Writes build/flatpak/bombsquad_prebuilt_inputs.tar.xz: what
    `make flatpak-prefetch` fetched (built assets, resources, the
    prebuilt plus lib for each arch, the gui asset bundle and the
    content-store blobs it references, the app icon) plus releases.xml,
    which the release workflow adds this release's entry to. Flathub
    builds take the code from git and extract this over it.

    The archive also carries a list of its own files,
    .flatpak-prebuilt-inputs, which the manifest uses to mark exactly
    those files fresh after extracting them over the checkout.
    """
    import io
    import os
    import tarfile

    from efro.terminal import Clr
    from batools._bundlestage import (
        assetdata_blob_path,
        collect_bundle_hashes,
    )

    projroot = str(pcommand.PROJROOT)
    bundle_manifest = '.cache/asset_bundle/gui-minimal/manifest.json'
    paths = [
        'build/assets',
        'build/prefab/lib/linux_x86_64_gui/release',
        'build/prefab/lib/linux_arm64_gui/release',
        'ballisticakit-windows/Generic/BallisticaKit.ico',
        os.path.dirname(bundle_manifest),
        'pconfig/flatpak/net.froemling.bombsquad.releases.xml',
        'pconfig/flatpak/net.froemling.bombsquad.png',
    ]
    # Staging copies the bundle's blobs out of the local content store;
    # take only those, not the whole (much larger) store.
    paths += sorted(
        assetdata_blob_path(h)
        for h in collect_bundle_hashes(
            projroot, os.path.join(projroot, bundle_manifest)
        )
    )
    # Not needed: Windows-only assets, and scripts the build copies
    # into build/assets from the git checkout itself.
    excluded = ('build/assets/windows', 'build/assets/ba_data/python')

    packed: list[str] = []

    def _filter(info: tarfile.TarInfo) -> tarfile.TarInfo | None:
        if any(
            info.name == e or info.name.startswith(f'{e}/') for e in excluded
        ):
            return None
        if info.isfile():
            packed.append(info.name)
        return info

    outpath = os.path.join(
        projroot, 'build', 'flatpak', 'bombsquad_prebuilt_inputs.tar.xz'
    )
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with tarfile.open(outpath, 'w:xz') as tar:
        for path in paths:
            tar.add(os.path.join(projroot, path), arcname=path, filter=_filter)
        listing = ('\n'.join(packed) + '\n').encode()
        info = tarfile.TarInfo('.flatpak-prebuilt-inputs')
        info.size = len(listing)
        tar.addfile(info, io.BytesIO(listing))
    print(f'{Clr.GRN}Wrote {outpath} ({len(packed)} files).{Clr.RST}')


def flatpak_add_release() -> None:
    """Add a release entry to the flatpak releases.xml.

    Args: <version>

    Writes pconfig/flatpak/net.froemling.bombsquad.releases.xml, which
    the flatpak build installs. The release workflow runs this before
    packing the prebuilt-inputs archive that carries it to Flathub;
    committing the entry ahead of time works too (an existing version
    is left alone). The release date is today (UTC).
    """
    # pylint: disable=too-many-locals
    import os
    import datetime
    from xml.etree import ElementTree as ET

    from efro.error import CleanError
    from efro.terminal import Clr
    from batools.changelog import get_version_changelog

    args = pcommand.get_args()
    if len(args) != 1:
        raise CleanError('Expected args: <version>')
    version = args[0].removeprefix('v')
    release_date = datetime.datetime.now(datetime.UTC).date().isoformat()
    github_repo = _github_repo()

    releases_xml_path = os.path.join(
        pcommand.PROJROOT,
        'pconfig',
        'flatpak',
        'net.froemling.bombsquad.releases.xml',
    )

    print(f'{Clr.BLD}Adding release {version} to releases.xml...{Clr.RST}')

    # Parse the existing releases.xml
    if not os.path.exists(releases_xml_path):
        raise CleanError(f'releases.xml not found at {releases_xml_path}')

    try:
        tree = ET.parse(releases_xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        raise CleanError(f'Failed to parse releases.xml: {e}') from e

    # Check if release with this version already exists
    existing_release = root.find(f".//release[@version='{version}']")
    if existing_release is not None:
        print(
            f'{Clr.YLW}Warning: Release {version} '
            f'already exists in releases.xml, skipping...{Clr.RST}'
        )
        return

    # Create new release element
    new_release = ET.Element('release')
    new_release.set('version', version)
    new_release.set('date', release_date)
    new_release.set('urgency', 'low')
    new_release.set('type', 'stable')

    # Add description
    description = ET.SubElement(new_release, 'description')
    changelog_list = get_version_changelog(
        version, projroot=str(pcommand.PROJROOT)
    )
    ul = ET.SubElement(description, 'ul')
    for line in changelog_list:
        li = ET.SubElement(ul, 'li')
        li.text = line

    # Add URL element for release page
    release_url = ET.SubElement(new_release, 'url')
    release_url.text = (
        f'https://github.com/{github_repo}/releases/tag/v{version}'
    )

    # Add artifacts section with binary information
    artifacts = ET.SubElement(new_release, 'artifacts')

    # Add source artifact
    source_artifact = ET.SubElement(artifacts, 'artifact')
    source_artifact.set('type', 'source')

    source_location = ET.SubElement(source_artifact, 'location')
    source_location.text = (
        f'https://github.com/{github_repo}/archive/refs/tags/v{version}.tar.gz'
    )

    # Insert the new release at the beginning (after the root element)
    root.insert(0, new_release)

    # Format the XML with proper indentation
    def _indent(elem: ET.Element[str], level: int = 0) -> None:
        """Add pretty-printing indentation to XML tree."""
        indent_str = '\n' + ('    ' * level)
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent_str + '    '
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent_str
            child: ET.Element | None = None
            for child in elem:
                _indent(child, level + 1)
            if child and (not child.tail or not child.tail.strip()):
                child.tail = indent_str
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent_str

    _indent(root)

    # Write back to file
    try:
        tree.write(releases_xml_path, encoding='utf-8', xml_declaration=True)
        print(
            f'{Clr.GRN}Added release {version} to'
            f' {releases_xml_path}.{Clr.RST}'
        )
    except Exception as e:
        raise CleanError(f'Failed to write releases.xml: {e}') from e


def gen_pyembed() -> None:
    """Gen a pyembed .inc file using compiled bytecode.

    Args: <in_path> <out_path> [encrypt={0,1}] [ctx=<var_name>]

    Replaces gen_encrypted_python_code (encrypt=1) and
    gen_flat_data_code (encrypt=0) for pyembed modules.
    """
    from efro.error import CleanError
    from batools.codegen import gen_pyembed as gen

    if len(sys.argv) < 4:
        raise CleanError(
            'Expected at least 2 args: <in_path> <out_path> '
            '[encrypt={0,1}] [ctx=<var>]'
        )

    encrypt = True
    ctx_var = 'internal_py_context'
    for arg in sys.argv[4:]:
        if arg.startswith('encrypt='):
            encrypt = arg.removeprefix('encrypt=') == '1'
        elif arg.startswith('ctx='):
            ctx_var = arg.removeprefix('ctx=')
        else:
            raise CleanError(f'Unrecognized arg: {arg!r}')

    gen(
        projroot=str(pcommand.PROJROOT),
        in_path=sys.argv[2],
        out_path=sys.argv[3],
        encrypt=encrypt,
        ctx_var=ctx_var,
    )


def require_unsandboxed() -> None:
    """Fail right away if running inside Claude Code's command sandbox.

    args: a short description of what is being attempted (for the
    error message).

    For build targets that cannot produce a correct result there:
    release archives and anything that uploads. Gradle is forced
    offline in the sandbox, so steps that need the network (Crashlytics
    mapping/symbol uploads, dependency fetches) fail or are skipped --
    and a release artifact that merely *looks* built is worse than no
    artifact. Failing in the first second, with the reason, beats
    finding out after a full build (or after shipping it).
    """
    from efro.error import CleanError
    from batools.build import in_claude_sandbox

    if len(sys.argv) != 3:
        raise CleanError('Expected 1 arg: a description of the task.')
    if in_claude_sandbox():
        raise CleanError(
            f"Refusing to run {sys.argv[2]} inside Claude Code's command"
            ' sandbox: Gradle has no network access there (it is forced'
            ' offline), so this cannot produce a correct result. Run it'
            ' from a normal shell instead.'
        )
