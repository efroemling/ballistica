# Released under the MIT License. See LICENSE for details.
#
"""Provides the TemplateFs subsystem."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class TemplateFsSubsystem:
    """Subsystem for TemplateFs functionality in the app.

    The single shared instance of this app can be accessed at
    babase.app.templatefs. Note that it is possible for babase.app.templatefs
    to be None if the TemplateFs feature-set is not enabled, and code
    should handle that case gracefully.
    """
