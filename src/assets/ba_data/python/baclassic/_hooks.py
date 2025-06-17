# Released under the MIT License. See LICENSE for details.
#
"""Hooks for C++ layer to use for ClassicAppMode."""
from __future__ import annotations

import logging

import babase


def on_engine_will_reset() -> None:
    """Called just before classic resets the engine."""
    from baclassic._appmode import ClassicAppMode

    appmode = babase.app.mode

    # Just pass this along to our mode instance for handling.
    if isinstance(appmode, ClassicAppMode):
        appmode.on_engine_will_reset()
    else:
        logging.error(
            'on_engine_will_reset called without ClassicAppMode active.'
        )


def on_engine_did_reset() -> None:
    """Called just after classic resets the engine."""
    from baclassic._appmode import ClassicAppMode

    appmode = babase.app.mode

    # Just pass this along to our mode instance for handling.
    if isinstance(appmode, ClassicAppMode):
        appmode.on_engine_did_reset()
    else:
        logging.error(
            'on_engine_did_reset called without ClassicAppMode active.'
        )


def request_main_ui() -> None:
    """Called to bring up in-game menu."""

    if babase.app.classic is None:
        logging.exception('Classic not present.')
        return

    babase.app.classic.request_main_ui()
