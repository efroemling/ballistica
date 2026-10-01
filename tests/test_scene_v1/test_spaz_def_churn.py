# Released under the MIT License. See LICENSE for details.
#
"""Spaz definitions must leave the session when nothing refs them.

Spaz defs churn per spawn inside a live scene (unlike materials, which
come and go at activity boundaries), so a long-running server would
accumulate stream state if a definition ever outlived its last
reference. This boots a headless host, creates and destroys spaz
definitions and the spaz nodes referencing them from inside the
main-menu activity, and checks after every cycle that the host
stream's live spaz-def table returns to its baseline once the last
Python and node references are gone (the wrapper type has no weakref
support; the stream count is the ground truth anyway).

Nodes are driven directly (not through the Spaz actor) so the native
node-level reference is what gets exercised. Design:
docs/initiatives/character-skins.md.
"""

import re

import pytest

from batools import apprun

pytestmark = pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)

_CYCLES = 30
_PER_CYCLE = 4

# Runs inside the engine via --exec; schedules itself once the
# main-menu host activity is up, then reports a single result line.
_EXEC_CODE = f'''
import gc
import logging

import babase
import bascenev1 as bs
import _bascenev1


def _spaz(character_json: str) -> str:
    spaz = bs.split_character(character_json).spaz
    assert spaz is not None
    return spaz


def _churn() -> None:
    from bascenev1lib.actor._spazcharacters import CHARACTERS

    act = bs.get_foreground_host_activity()
    assert act is not None
    names = sorted(CHARACTERS)
    problems: list[str] = []
    with act.context:
        baseline = _bascenev1.get_spaz_def_count()
        if baseline < 0:
            problems.append(f'not hosting (count={{baseline}})')
        peak = baseline
        for cycle in range({_CYCLES}):
            chars = []
            nodes = []
            for i in range({_PER_CYCLE}):
                name = names[(cycle * {_PER_CYCLE} + i) % len(names)]
                char = bs.SpazDef(_spaz(CHARACTERS[name]))
                node = bs.newnode('spaz', attrs={{'spaz_def': char}})
                # Read-back must hand out a live wrapper for the same
                # native object even though ours is still alive.
                if node.spaz_def is None:
                    problems.append(f'cycle {{cycle}}: attr read None')
                chars.append(char)
                nodes.append(node)
            del char, node  # Loop leftovers would keep the last one alive.
            count = _bascenev1.get_spaz_def_count()
            peak = max(peak, count)
            if count != baseline + {_PER_CYCLE}:
                problems.append(
                    f'cycle {{cycle}}: expected {{baseline + {_PER_CYCLE}}}'
                    f' live, got {{count}}'
                )
            # Drop Python refs first; nodes still hold the natives.
            del chars
            gc.collect()
            if _bascenev1.get_spaz_def_count() != baseline + {_PER_CYCLE}:
                problems.append(
                    f'cycle {{cycle}}: spaz def died while a node held it'
                )
            for node in nodes:
                node.delete()
            del nodes
            gc.collect()
            count = _bascenev1.get_spaz_def_count()
            if count != baseline:
                problems.append(
                    f'cycle {{cycle}}: {{count - baseline}} leaked after'
                    ' nodes died'
                )
        # One more: a node created and deleted while the Python ref is
        # gone before the node is (the actor's normal shape).
        node = bs.newnode(
            'spaz', attrs={{'spaz_def': bs.SpazDef(_spaz(CHARACTERS['Spaz']))}}
        )
        gc.collect()
        if _bascenev1.get_spaz_def_count() != baseline + 1:
            problems.append('node-only ref: spaz def not alive')
        wrap = node.spaz_def
        node.delete()
        del node
        gc.collect()
        if _bascenev1.get_spaz_def_count() != baseline + 1:
            problems.append('read-back wrapper did not keep spaz def')
        del wrap
        gc.collect()
        if _bascenev1.get_spaz_def_count() != baseline:
            problems.append('spaz def leaked after wrapper dropped')
    if problems:
        logging.warning('CHARCHURN fail: %s', '; '.join(problems))
    else:
        logging.warning('CHARCHURN ok peak=%d baseline=%d', peak, baseline)
    babase.quit()


babase.apptimer(4.0, _churn)
'''


def test_spaz_def_churn() -> None:
    """Spaz defs come and go with their references; nothing leaks."""
    proc = apprun.run_headless_capture(
        purpose='spaz def churn test',
        exec_code=_EXEC_CODE,
        timeout=60.0,
        stop_pattern=re.compile(r'CHARCHURN (ok|fail)'),
    )
    output = proc.stdout.decode(errors='replace')
    match = re.search(r'CHARCHURN (ok|fail)(.*)', output)
    assert match is not None, f'no result line in output:\n{output[-3000:]}'
    assert match.group(1) == 'ok', match.group(0)
