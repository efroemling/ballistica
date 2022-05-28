# Released under the MIT License. See LICENSE for details.
#
"""Account related functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional


class AccountV2Subsystem:
    """Subsystem for modern account handling in the app.

    Category: **App Classes**

    Access the single shared instance of this class at 'ba.app.accounts_v2'.
    """

    def on_app_launch(self) -> None:
        """Should be called at standard on_app_launch time."""

    def set_primary_credentials(self, credentials: Optional[str]) -> None:
        """Set credentials for the primary app account."""
        raise RuntimeError('This should be overridden.')

    def have_primary_credentials(self) -> bool:
        """Are credentials currently set for the primary app account?

        Note that this does not mean these credentials are currently valid;
        only that they exist. If/when credentials are validated, the 'primary'
        account handle will be set.
        """
        raise RuntimeError('This should be overridden.')

    @property
    def primary(self) -> Optional[AccountV2Handle]:
        """The primary account for the app, or None if not logged in."""
        return None

    def get_primary(self) -> Optional[AccountV2Handle]:
        """Internal - should be overridden by subclass."""
        return None


class AccountV2Handle:
    """Handle for interacting with a v2 account."""

    def __init__(self) -> None:
        self.tag = '?'
