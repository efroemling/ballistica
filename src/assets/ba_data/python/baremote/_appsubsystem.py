# Released under the MIT License. See LICENSE for details.
#
"""Provides the Remote App-Subsystem."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class RemoteAppSubsystem:
    """Subsystem for Remote functionality in the app.

    If :attr:`~batools.featureset.FeatureSet.has_python_app_subsystem`
    is enabled for our feature-set, the single shared instance of this
    class can be accessed as `remote` on the :class:`~babase.App`
    instance.
    """
