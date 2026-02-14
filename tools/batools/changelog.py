# Released under the MIT License. See LICENSE for details.
#
"""Generates a pretty html changelog from our markdown."""

import os
import subprocess


def get_version_changelog(version: str, projroot: str) -> list[str]:
    """Get changelog text for a given version from CHANGELOG.md."""
    import re
    from efro.error import CleanError

    changelog_path = os.path.join(projroot, 'CHANGELOG.md')
    if not os.path.exists(changelog_path):
        raise CleanError(f'CHANGELOG.md not found at {changelog_path}')

    with open(changelog_path, 'r', encoding='utf-8') as infile:
        changelog_content = infile.read()

    # Regex to find the section for the given version
    pattern = rf'^###\s+{re.escape(version)}\b.*?\n(.*?)(?=^###\s+|\Z)'
    match = re.search(pattern, changelog_content, re.DOTALL | re.MULTILINE)
    if not match:
        raise CleanError(f'Changelog entry for version {version} not found.')

    section_text = match.group(1).rstrip()

    # Convert changelog section into a list of bullet entries,
    # preserving internal newlines and indentation.
    lines = section_text.splitlines()
    entries: list[str] = []
    current_entry: list[str] = []

    for line in lines:
        if line.startswith('- '):
            # Save previous entry if present
            if current_entry:
                entries.append('\n'.join(current_entry).rstrip())
                current_entry = []

            # Strip "- " but preserve rest exactly
            current_entry.append(line[2:])
        else:
            # Continuation line (including indentation or blank lines)
            if current_entry:
                current_entry.append(line)

    # Add final entry
    if current_entry:
        entries.append('\n'.join(current_entry).rstrip())

    changelog_list = entries

    return changelog_list


def generate(projroot: str) -> None:
    """Main script entry point."""

    # Make sure we start from root dir (one above this script).
    os.chdir(projroot)

    out_path = 'build/changelog.html'
    out_path_tmp = out_path + '.md'

    # Do some filtering of our raw changelog.
    with open('CHANGELOG.md', encoding='utf-8') as infile:
        lines = infile.read().splitlines()

    # Strip out anything marked internal.
    lines = [
        line for line in lines if not line.strip().startswith('- (internal)')
    ]

    with open(out_path_tmp, 'w', encoding='utf-8') as outfile:
        outfile.write('\n'.join(lines))

    subprocess.run(
        f'pandoc -f markdown {out_path_tmp}  > {out_path}',
        shell=True,
        check=True,
    )
    print(f'Generated changelog at \'{out_path}\'.')
    os.unlink(out_path_tmp)
