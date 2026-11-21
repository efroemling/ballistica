# Released under the MIT License. See LICENSE for details.
#
"""Provides the Squads App-Subsystem."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class SquadsAppSubsystem:
    """Subsystem for Squads functionality in the app.

    If :attr:`~batools.featureset.FeatureSet.has_python_app_subsystem`
    is enabled for our feature-set, the single shared instance of this
    class can be accessed as `squads` on the :class:`~babase.App`
    instance.
    """
