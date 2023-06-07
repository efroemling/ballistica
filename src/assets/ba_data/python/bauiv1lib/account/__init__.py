# Released under the MIT License. See LICENSE for details.
#
"""UI functionality related to accounts."""

from __future__ import annotations

import bauiv1 as bui


def show_sign_in_prompt(account_type: str | None = None) -> None:
    """Bring up a prompt telling the user they must sign in."""
    from bauiv1lib.confirm import ConfirmWindow
    from bauiv1lib.account import settings

    if account_type == 'Google Play':

        def _do_sign_in() -> None:
            plus = bui.app.plus
            assert plus is not None
            plus.sign_in_v1('Google Play')

        ConfirmWindow(
            bui.Lstr(resource='notSignedInGooglePlayErrorText'),
            _do_sign_in,
            ok_text=bui.Lstr(resource='accountSettingsWindow.signInText'),
            width=460,
            height=130,
        )
    else:
        ConfirmWindow(
            bui.Lstr(resource='notSignedInErrorText'),
            lambda: settings.AccountSettingsWindow(
                modal=True, close_once_signed_in=True
            ),
            ok_text=bui.Lstr(resource='accountSettingsWindow.signInText'),
            width=460,
            height=130,
        )
