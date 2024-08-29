# Released under the MIT License. See LICENSE for details.
#
"""Provides the TemplateFs App-Subsystem."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class TemplateFsAppSubsystem:
    """Subsystem for TemplateFs functionality in the app.

    The single shared instance of this class can be accessed at
    ba*.app.templatefs. Note that it is possible for ba*.app.templatefs
    to be None if the TemplateFs feature-set is not enabled, and code
    should handle that case gracefully.
    """
