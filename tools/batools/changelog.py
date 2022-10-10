# Released under the MIT License. See LICENSE for details.
#
"""Generates a pretty html changelog from our markdown."""

import os
import subprocess


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
