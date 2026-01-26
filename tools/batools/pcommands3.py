# Released under the MIT License. See LICENSE for details.
#
"""A nice collection of ready-to-use pcommands for this package."""

from __future__ import annotations

# Note: import as little as possible here at the module level to
# keep launch times fast for small snippets.
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


# pylint: disable=too-many-locals,too-many-statements
def generate_flathub_manifest() -> None:
    """Generate a Flathub manifest for Ballistica and push to submodule.
    This function is intended to be run within a GitHub Actions workflow.

    This function:
    1. Copies files from config/flatpak/ to config/flatpak/flathub
    2. Generates the manifest from template using latest GitHub release info
    """
    import json
    import os
    import shutil
    import urllib.request
    import subprocess

    from efro.error import CleanError
    from efro.terminal import Clr

    pcommand.disallow_in_batch()
    try:
        github_repo = os.environ['GITHUB_REPOSITORY']
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
            github_repo = (
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

    # Paths
    flatpak_src_dir = os.path.join(pcommand.PROJROOT, 'config', 'flatpak')
    flathub_dir = os.path.join(pcommand.PROJROOT, 'build', 'flathub')
    template_path = os.path.join(
        flatpak_src_dir, 'net.froemling.bombsquad.yml.template'
    )
    os.makedirs(flathub_dir, exist_ok=True)
    manifest_path = os.path.join(flathub_dir, 'net.froemling.bombsquad.yml')

    print(f'{Clr.BLD}Generating Flathub manifest...{Clr.RST}')

    # Step 1: Copy files from config/flatpak/ to config/flatpak/flathub
    print(
        f'{Clr.BLD}Copying files from {flatpak_src_dir} to '
        f'{flathub_dir}...{Clr.RST}'
    )

    # List of files to copy (skip the flathub directory itself)
    files_to_copy = [
        'net.froemling.bombsquad.appdata.xml',
        'net.froemling.bombsquad.desktop',
        'net.froemling.bombsquad.releases.xml',
    ]

    for filename in files_to_copy:
        src = os.path.join(flatpak_src_dir, filename)
        dst = os.path.join(flathub_dir, filename)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f'  Copied {filename}')
        else:
            print(f'  Warning: {filename} not found at {src}')

    # Step 2: Get latest release information from GitHub
    print(f'{Clr.BLD}Fetching latest GitHub release info...{Clr.RST}')

    try:
        api_url = f'https://api.github.com/repos/{github_repo}/releases/latest'
        req = urllib.request.Request(api_url)

        with urllib.request.urlopen(req) as response:
            release_data = json.loads(response.read().decode())

        # Find the linux_build_env.tar asset
        asset: dict = {}
        asset_url = None
        asset_name = 'linux_build_env.tar'

        for asset in release_data.get('assets', []):
            if asset['name'] == asset_name:
                asset_url = asset['browser_download_url']
                break

        if not asset_url:
            raise CleanError(
                f'Could not find {asset_name} in latest release assets'
            )

        print(f'  Found asset: {asset_url}')

        # Extract version from release tag
        version = release_data.get('tag_name', '').lstrip('v')
        if not version:
            raise CleanError('Could not extract version from release tag')
        print(f'  Release version: {version}')

        # Extract release date from published_at field
        release_date = release_data.get('published_at', '')
        if not release_date:
            raise CleanError('Could not extract release date from API')
        # Convert ISO format date (e.g., '2026-01-25T12:34:56Z')
        # to YYYY-MM-DD
        release_date = release_date.split('T')[0]
        print(f'  Release date: {release_date}')

        print(f'{Clr.BLD}Getting SHA256 checksum...{Clr.RST}')
        digest = asset.get('digest')
        if not digest or not digest.startswith('sha256:'):
            msg = 'No SHA256 digest found in GitHub release asset'
            raise CleanError(msg)
        checksum = digest.split(':', 1)[1]

    except Exception as e:
        raise CleanError(f'Failed to fetch release info: {e}') from e

    print(f'{Clr.BLD}Generating manifest from template...{Clr.RST}')

    with open(template_path, 'r', encoding='utf-8') as infile:
        template = infile.read()

    def _remove_comments_from_xml_template(content: str) -> str:
        import re

        # Pattern matches lines that start with optional spaces/tabs then '#'
        # This removes the entire line including the newline
        pattern = r'^\s*#.*$\n?'
        result = re.sub(pattern, '', content, flags=re.MULTILINE)

        return result

    template = _remove_comments_from_xml_template(template)
    # Replace placeholders
    manifest_content = template.replace('{ ARCHIVE_URL }', asset_url)
    manifest_content = manifest_content.replace('{ SHA256_CHECKSUM }', checksum)

    with open(manifest_path, 'w', encoding='utf-8') as outfile:
        outfile.write(manifest_content)

    print(f'  Generated manifest at {manifest_path}')

    # Call generate_flatpak_release_manifest with
    # the extracted version, repo URL, and date
    print(f'{Clr.BLD}Generating Flatpak release manifest...{Clr.RST}')
    generate_flatpak_release_manifest(
        version, asset_url, checksum, github_repo, release_date
    )

    print(f'{Clr.BLD}{Clr.GRN}Flathub manifest generation complete!{Clr.RST}')


# pylint: disable=too-many-locals,too-many-statements
def generate_flatpak_release_manifest(
    version: str,
    asset_url: str,
    checksum: str,
    github_repo: str,
    release_date: str,
) -> None:
    """Generate a Flatpak release manifest for Ballistica.

    This function:
    1. Adds a new release entry to net.froemling.bombsquad.releases.xml
    2. Updates the net.froemling.bombsquad.releases.xml file with the
       new release information

    Args:
        version: Version string from GitHub release (e.g., '1.7.60')
        asset_url: URL to the release asset
        checksum: SHA256 checksum of the release asset
        github_repo: GitHub repository in format 'owner/repo'
        release_date: Release date in YYYY-MM-DD format
    """
    import os
    from xml.etree import ElementTree as ET

    from efro.error import CleanError
    from efro.terminal import Clr

    pcommand.disallow_in_batch()

    # Paths
    flathub_dir = os.path.join(pcommand.PROJROOT, 'build', 'flathub')
    releases_xml_path = os.path.join(
        flathub_dir, 'net.froemling.bombsquad.releases.xml'
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
    p = ET.SubElement(description, 'p')
    p.text = get_changelog(version)

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

    # Add binary artifact for linux
    binary_artifact = ET.SubElement(artifacts, 'artifact')
    binary_artifact.set('type', 'source')
    binary_artifact.set('platform', 'x86_64-linux-gnu')

    binary_location = ET.SubElement(binary_artifact, 'location')
    binary_location.text = asset_url

    binary_checksum = ET.SubElement(binary_artifact, 'checksum')
    binary_checksum.set('type', 'sha256')
    binary_checksum.text = checksum

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
        print(f'  Added release {version} to releases.xml')
        print(f'  Generated flatpak release manifest at {releases_xml_path}')
        print(
            f'{Clr.BLD}{Clr.GRN}Flatpak release manifest '
            f'generation complete!{Clr.RST}'
        )
    except Exception as e:
        raise CleanError(f'Failed to write releases.xml: {e}') from e


def get_changelog(version: str | None = None) -> str:
    """Get changelog text for a given version from CHANGELOG.md."""
    import re
    import os
    from efro.error import CleanError
    from efro.terminal import Clr

    called_from_other_function = version is not None
    pcommand.disallow_in_batch()
    if version is None:
        args = pcommand.get_args()
        if len(args) != 1:
            raise CleanError('Expected 1 arg: version')
        version = args[0]
    changelog_path = os.path.join(pcommand.PROJROOT, 'CHANGELOG.md')
    if not os.path.exists(changelog_path):
        raise CleanError(f'CHANGELOG.md not found at {changelog_path}')

    with open(changelog_path, 'r', encoding='utf-8') as infile:
        changelog_content = infile.read()

    # Regex to find the section for the given version
    pattern = rf'^###\s+{re.escape(version)}\b.*?\n(.*?)(?=^###\s+|\Z)'
    match = re.search(pattern, changelog_content, re.DOTALL | re.MULTILINE)
    if not match:
        raise CleanError(f'Changelog entry for version {version} not found.')

    changelog_text = match.group(1).strip()
    if not called_from_other_function:
        print(
            f'{Clr.BLD}Changelog for version '
            f'{version}:{Clr.RST}\n{changelog_text}'
        )
    return changelog_text
