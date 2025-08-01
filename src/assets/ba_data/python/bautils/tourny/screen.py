# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to teams sessions."""

from __future__ import annotations

from typing import TYPE_CHECKING, override
from abc import ABC, abstractmethod
from dataclasses import dataclass

import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any


@dataclass
class NextScreenActivityMessage:
    """_summary_

    Raises:
        TypeError: _description_

    Returns:
        _type_: _description_
    """

    index: int | None = None

    def __post__init__(self) -> None:
        if self.index is not None:
            return
        self.index = (
            TournamentScreenActivities.get_next_screen_act().get_screen_index()
        )


class TournamentScreenActivities:
    """_summary_"""

    screens: list[type[TournamentScreenActivity]] = []
    current_screen: type[TournamentScreenActivity] | None = None

    @classmethod
    def register_activity(cls, act: type[TournamentScreenActivity]) -> None:
        """_summary_

        Args:
            act (_type_): _description_
        """
        cls.screens.append(act)

    @classmethod
    def get_next_screen_act(
        cls, msg: NextScreenActivityMessage | None = None
    ) -> type[TournamentScreenActivity]:
        """_summary_

        Args:
            act (_type_): _description_
        """
        first_scr = min(
            cls.screens, key=lambda s: s.get_screen_index(), default=None
        )

        if msg is not None:
            for scr in cls.screens:
                if scr.get_screen_index() == msg.index:
                    return scr
            raise IndexError(f"No Screen Found with index {msg.index}")

        if first_scr is None:
            raise RuntimeError("No ScreenActivity Registered.")

        if cls.current_screen is None:
            cls.current_screen = first_scr
            return cls.current_screen
        next_scr = min(
            (
                scr
                for scr in cls.screens
                if scr.get_screen_index()
                > cls.current_screen.get_screen_index()
            ),
            key=lambda scr: scr.get_screen_index(),
            default=first_scr,
        )
        return next_scr


def register_screen_activity(
    cls: type[TournamentScreenActivity],
) -> type[TournamentScreenActivity]:
    """_summary_

    Args:
        cls (type[TournamentScreenActivity]): _description_

    Raises:
        TypeError: _description_

    Returns:
        type[TournamentScreenActivity]: _description_
    """
    if not issubclass(cls, TournamentScreenActivity):
        raise TypeError(
            "@register_screen_activity must be used on "
            "TournamentScreenActivity subclasses"
        )

    TournamentScreenActivities.register_activity(cls)
    return cls


class TournamentScreenActivity(ABC, bs.Activity[bs.Player, bs.Team]):
    """_summary_

    Args:
        ABC (_type_): _description_
        bs (_type_): _description_
    """

    def __init__(self, settings: dict) -> None:
        """Set up playlists & launch a bascenev1.Activity to accept joiners."""
        super().__init__(settings=settings)

    @staticmethod
    @abstractmethod
    def get_screen_index() -> int:
        """_summary_

        Returns:
            int: _description_
        """

    @classmethod
    def register_screen(cls) -> None:
        """_summary_"""
        TournamentScreenActivities.register_activity(cls)

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, NextScreenActivityMessage):
            self.session.setactivity(
                bs.newactivity(
                    TournamentScreenActivities.get_next_screen_act(msg)
                )
            )
        else:
            super().handlemessage(msg)
