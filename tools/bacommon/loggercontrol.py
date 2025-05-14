# Released under the MIT License. See LICENSE for details.
#
"""System for managing loggers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated
from dataclasses import dataclass, field

from efro.dataclassio import ioprepped, IOAttrs

if TYPE_CHECKING:
    from typing import Self, Sequence


@ioprepped
@dataclass
class LoggerControlConfig:
    """A logging level configuration that applies to all loggers.

    Any loggers not explicitly contained in the configuration will be
    set to NOTSET.
    """

    # Logger names mapped to log-level values (from system logging
    # module).
    levels: Annotated[dict[str, int], IOAttrs('l', store_default=False)] = (
        field(default_factory=dict)
    )

    def apply(
        self,
        *,
        warn_unexpected_loggers: bool = False,
        warn_missing_loggers: bool = False,
        ignore_log_prefixes: list[str] | None = None,
    ) -> None:
        """Apply the config to all Python loggers.

        If 'warn_unexpected_loggers' is True, warnings will be issues for
        any loggers not explicitly covered by the config. This is useful
        to help ensure controls for all possible loggers are present in
        a UI/etc.

        If 'warn_missing_loggers' is True, warnings will be issued for
        any loggers present in the config that are not found at apply time.
        This can be useful for pruning settings for no longer used loggers.

        Warnings for any log names beginning with any strings in
        'ignore_log_prefixes' will be suppressed. This can allow
        ignoring loggers associated with submodules for a given package
        and instead presenting only a top level logger (or none at all).
        """
        if ignore_log_prefixes is None:
            ignore_log_prefixes = []

        existinglognames = (
            set(['root']) | logging.root.manager.loggerDict.keys()
        )

        # First issue any warnings they want.
        if warn_unexpected_loggers:
            for logname in sorted(existinglognames):
                if logname not in self.levels and not any(
                    logname.startswith(pre) for pre in ignore_log_prefixes
                ):
                    logging.warning(
                        'Found a logger not covered by LoggerControlConfig:'
                        " '%s'.",
                        logname,
                    )
        if warn_missing_loggers:
            for logname in sorted(self.levels.keys()):
                if logname not in existinglognames and not any(
                    logname.startswith(pre) for pre in ignore_log_prefixes
                ):
                    logging.warning(
                        'Logger covered by LoggerControlConfig does not exist:'
                        ' %s.',
                        logname,
                    )

        # First, update levels for all existing loggers.
        for logname in existinglognames:
            logger = logging.getLogger(logname)
            level = self.levels.get(logname)
            if level is None:
                level = logging.NOTSET
            logger.setLevel(level)

        # Next, assign levels to any loggers that don't exist.
        for logname, level in self.levels.items():
            if logname not in existinglognames:
                logging.getLogger(logname).setLevel(level)

    def sanity_check_effective_levels(self) -> None:
        """Checks existing loggers to make sure they line up with us.

        This can be called periodically to ensure that a control-config
        is properly driving log levels and that nothing else is changing
        them behind our back.
        """

        existinglognames = (
            set(['root']) | logging.root.manager.loggerDict.keys()
        )
        for logname in existinglognames:
            logger = logging.getLogger(logname)
            if logger.getEffectiveLevel() != self.get_effective_level(logname):
                logging.error(
                    'loggercontrol effective-level sanity check failed;'
                    ' expected logger %s to have effective level %s'
                    ' but it has %s.',
                    logname,
                    logging.getLevelName(self.get_effective_level(logname)),
                    logging.getLevelName(logger.getEffectiveLevel()),
                )

    def get_effective_level(self, logname: str) -> int:
        """Given a log name, predict its level if this config is applied."""
        splits = logname.split('.')

        splen = len(splits)
        for i in range(splen):
            subname = '.'.join(splits[: splen - i])
            thisval = self.levels.get(subname)
            if thisval is not None and thisval != logging.NOTSET:
                return thisval

        # Haven't found anything; just return root value.
        thisval = self.levels.get('root')
        return (
            logging.DEBUG
            if thisval is None
            else logging.DEBUG if thisval == logging.NOTSET else thisval
        )

    def would_make_changes(self) -> bool:
        """Return whether calling apply would change anything."""

        existinglognames = (
            set(['root']) | logging.root.manager.loggerDict.keys()
        )

        # Return True if we contain any nonexistent loggers. Even if
        # we wouldn't change their level, the fact that we'd create
        # them still counts as a difference.
        if any(
            logname not in existinglognames for logname in self.levels.keys()
        ):
            return True

        # Now go through all existing loggers and return True if we
        # would change their level.
        for logname in existinglognames:
            logger = logging.getLogger(logname)
            level = self.levels.get(logname)
            if level is None:
                level = logging.NOTSET
            if logger.level != level:
                return True

        return False

    def diff(self, baseconfig: LoggerControlConfig) -> LoggerControlConfig:
        """Return a config containing only changes compared to a base config.

        Note that this omits all NOTSET values that resolve to NOTSET in
        the base config.

        This diffed config can later be used with apply_diff() against the
        base config to recreate the state represented by self.
        """
        cls = type(self)
        config = cls()
        for loggername, level in self.levels.items():
            baselevel = baseconfig.levels.get(loggername, logging.NOTSET)
            if level != baselevel:
                config.levels[loggername] = level
        return config

    def apply_diff(
        self, diffconfig: LoggerControlConfig
    ) -> LoggerControlConfig:
        """Apply a diff config to ourself.

        Note that values that resolve to NOTSET are left intact in the
        output config. This is so all loggers expected by either the
        base or diff config to exist can be created if desired/etc.
        """
        cls = type(self)

        # Create a new config (with an indepenent levels dict copy).
        config = cls(levels=dict(self.levels))

        # Overlay the diff levels dict onto our new one.
        config.levels.update(diffconfig.levels)

        # Note: we do NOT prune NOTSET values here. This is so all
        # loggers mentioned in the base config get created if we are
        # applied, even if they are assigned a default level.
        return config

    @classmethod
    def from_current_loggers(cls) -> Self:
        """Build a config from the current set of loggers."""
        lognames = ['root'] + sorted(logging.root.manager.loggerDict)
        config = cls()
        for logname in lognames:
            config.levels[logname] = logging.getLogger(logname).level
        return config
