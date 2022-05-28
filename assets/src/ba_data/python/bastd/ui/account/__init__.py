# Released under the MIT License. See LICENSE for details.
#
"""UI functionality related to accounts."""

from __future__ import annotations

import _ba
import ba


def show_sign_in_prompt(account_type: str = None) -> None:
    """Bring up a prompt telling the user they must sign in."""
    from bastd.ui.confirm import ConfirmWindow
    from bastd.ui.account import settings
    if account_type == 'Google Play':
        ConfirmWindow(
            ba.Lstr(resource='notSignedInGooglePlayErrorText'),
            lambda: _ba.sign_in_v1('Google Play'),
            ok_text=ba.Lstr(resource='accountSettingsWindow.signInText'),
            width=460,
            height=130)
    else:
        ConfirmWindow(
            ba.Lstr(resource='notSignedInErrorText'),
            lambda: settings.AccountSettingsWindow(modal=True,
                                                   close_once_signed_in=True),
            ok_text=ba.Lstr(resource='accountSettingsWindow.signInText'),
            width=460,
            height=130)
