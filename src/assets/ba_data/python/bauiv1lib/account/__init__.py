# Released under the MIT License. See LICENSE for details.
#
"""UI functionality related to accounts."""

from __future__ import annotations

import bauiv1 as bui


def show_sign_in_prompt() -> None:
    """Bring up a prompt telling the user they must sign in."""
    from bauiv1lib.confirm import ConfirmWindow
    from bauiv1lib.account.settings import AccountSettingsWindow

    ConfirmWindow(
        bui.Lstr(resource='notSignedInErrorText'),
        lambda: AccountSettingsWindow(modal=True, close_once_signed_in=True),
        ok_text=bui.Lstr(resource='accountSettingsWindow.signInText'),
        width=460,
        height=130,
    )
