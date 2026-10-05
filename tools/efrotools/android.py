# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to android builds."""

import pathlib
import subprocess
import sys
from typing import TYPE_CHECKING
from dataclasses import dataclass

from efro.error import CleanError

if TYPE_CHECKING:
    pass


def push_apk_to_archive(
    root: pathlib.Path,
    apk_path: pathlib.Path,
    archive_id: str,
) -> None:
    """Publish an already-built apk as a new bamaster archive version.

    The android analogue of :func:`efrotools.ios.push_ipa_to_archive`,
    minus the ipa construction -- gradle has already produced the apk,
    so this only stages it alongside a small ``install_meta.json``
    sidecar and publishes the pair as a single archive version. The
    version arg is omitted so the archive system auto-assigns the next
    integer after the latest published one.

    There is deliberately no manifest counterpart to the ios OTA plist:
    android installs from a plain https download of the apk, so the
    sidecar carries only what the installs page displays.
    """
    import json
    import shutil
    import socket
    import tempfile

    if not apk_path.is_file():
        raise CleanError(f"Apk not found at '{apk_path}'.")

    meta = {
        'title': 'BallisticaKit',
        'apk_filename': apk_path.name,
        # Which machine actually produced this build. Same reasoning as
        # the ios sidecar's build_host: with more than one build host
        # publishing here, nothing else tells two versions apart.
        'build_host': socket.gethostname(),
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copy2(apk_path, pathlib.Path(tmpdir, apk_path.name))
        with pathlib.Path(tmpdir, 'install_meta.json').open(
            'w', encoding='utf-8'
        ) as outfile:
            json.dump(meta, outfile)

        print(f'Publishing {archive_id} to archive...')
        sys.stdout.flush()
        subprocess.run(
            [
                str(pathlib.Path(root, 'tools', 'bacloud')),
                'admin',
                'archive',
                'publish',
                archive_id,
                tmpdir,
            ],
            check=True,
        )

    print('Android build published to archive successfully!')


@dataclass
class GradleFilterSection:
    """Filtered section of gradle file."""

    tag: str
    firstline: int
    lastline: int


def filter_gradle_file(buildfilename: str, enabled_tags: set[str]) -> None:
    """Filter ``EFRO_IF`` sections in a gradle file."""

    sections: list[GradleFilterSection] = []

    with open(buildfilename, encoding='utf-8') as infile:
        original = infile.read()
    lines = original.splitlines()

    current_section: GradleFilterSection | None = None
    for i, line in enumerate(lines):
        if line.strip().startswith('// EFRO_IF'):
            if current_section is not None:
                raise RuntimeError('Malformed gradle file')
            current_section = GradleFilterSection(
                tag=line.split()[2], firstline=i, lastline=i
            )
        elif line.strip().startswith('// EFRO_ENDIF'):
            if current_section is None:
                raise RuntimeError('Malformed gradle file')
            current_section.lastline = i
            sections.append(current_section)
            current_section = None
    if current_section is not None:
        raise RuntimeError('Malformed gradle file')

    for section in sections:
        for lineno in range(section.firstline + 1, section.lastline):
            enable = section.tag in enabled_tags
            line = lines[lineno]
            leading = ''
            while line.startswith(' '):
                leading += ' '
                line = line[1:]
            if not enable and not line.startswith('// '):
                line = '// ' + line
            if enable and line.startswith('// '):
                line = line[3:]
            lines[lineno] = leading + line

    # Only write if its changed (potentially avoid triggering builds).
    out = '\n'.join(lines) + '\n'
    if out != original:
        with open(buildfilename, 'w', encoding='utf-8') as outfile:
            outfile.write(out)
