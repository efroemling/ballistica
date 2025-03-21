# Released under the MIT License. See LICENSE for details.
#
"""Provides the TemplateFs App-Subsystem."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class TemplateFsAppSubsystem:
    """Subsystem for TemplateFs functionality in the app.

    If 'has_python_app_subsystem' is enabled for our feature-set, the
    single shared instance of this class can be accessed at
    'ba*.app.template_fs'.
    """
