# Released under the MIT License. See LICENSE for details.
#
"""Golden test pinning scene_v1 node-type and attr wire ordering.

Scene streams address node types by numeric id and node attrs by their
index in the type's attr table, so both orderings are part of the
scene_v1 wire protocol: a shifted index breaks compatibility with every
older server, client, and replay file (see the protocol-changes list in
src/ballistica/scene_v1/scene_v1.h, entries 42/43, for a real instance
of this). This test compares the live tables against a checked-in
golden file so any shift shows up as a CI failure with a precise diff
instead of as players getting kicked on live servers.

If a diff here is deliberate (a new node type or attr), it requires a
protocol version bump in scene_v1.h; regenerate the golden file by
running this test with BA_UPDATE_GOLDEN=1 set.
"""

import json
import os
import tempfile

import pytest

from batools import apprun

FAST_MODE = os.environ.get('BA_TEST_FAST_MODE') == '1'

GOLDEN_PATH = os.path.join(
    os.path.dirname(__file__), 'node_attr_tables_golden.json'
)


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_node_attr_tables() -> None:
    """Compare live node type/attr wire tables against the golden file."""

    with tempfile.TemporaryDirectory() as tmpdir:
        outpath = os.path.join(tmpdir, 'tables.json')
        apprun.python_command(
            'import json, _bascenev1;'
            f' open({outpath!r}, "w").write('
            'json.dumps(_bascenev1.get_node_attr_tables()))',
            purpose='node attr table golden check',
        )
        with open(outpath, encoding='utf-8') as infile:
            live = json.load(infile)

    if os.environ.get('BA_UPDATE_GOLDEN') == '1':
        with open(GOLDEN_PATH, 'w', encoding='utf-8') as outfile:
            json.dump(live, outfile, indent=1)
            outfile.write('\n')
        print(f'Regenerated {GOLDEN_PATH}.')
        return

    with open(GOLDEN_PATH, encoding='utf-8') as infile:
        golden = json.load(infile)

    problems: list[str] = []

    # Node-type *order* is wire-relevant (types are addressed by id).
    if list(golden) != list(live):
        problems.append(
            f'node type id order changed:'
            f' golden={list(golden)} live={list(live)}'
        )

    # And each type's attr table order assigns wire indices.
    for tname in golden:
        if tname not in live:
            problems.append(f"node type '{tname}' removed")
            continue
        gattrs = golden[tname]
        lattrs = live[tname]
        for idx, gattr in enumerate(gattrs):
            lattr = lattrs[idx] if idx < len(lattrs) else None
            if gattr != lattr:
                problems.append(
                    f"node type '{tname}' attr index {idx} changed:"
                    f' golden={gattr} live={lattr}'
                )
        for idx in range(len(gattrs), len(lattrs)):
            problems.append(
                f"node type '{tname}' gained attr index {idx}:"
                f' {lattrs[idx]}'
            )
    for tname in live:
        if tname not in golden:
            problems.append(f"new node type '{tname}'")

    assert not problems, (
        'scene_v1 wire tables diverge from the golden file:\n  '
        + '\n  '.join(problems)
        + '\nThese orderings are part of the scene_v1 wire protocol.'
        ' If this change is deliberate, bump the protocol version'
        ' (src/ballistica/scene_v1/scene_v1.h), ensure existing indices'
        ' are preserved (base-type appends need the _LATE attr macros;'
        ' see protocol notes 42/43), and regenerate the golden file by'
        ' running this test with BA_UPDATE_GOLDEN=1.'
    )
