# Copyright (c) 2011-2019 Eric Froemling
"""UI functionality related to accounts."""

from __future__ import annotations

import _ba
import ba


def show_sign_in_prompt(account_type: str = None) -> None:
    """Bring up a prompt telling the user they must sign in."""
    from bastd.ui import confirm
    from bastd.ui.account import settings
    if account_type == 'Google Play':
        confirm.ConfirmWindow(
            ba.Lstr(resource='notSignedInGooglePlayErrorText'),
            lambda: _ba.sign_in('Google Play'),
            ok_text=ba.Lstr(resource='accountSettingsWindow.signInText'),
            width=460,
            height=130)
    else:
        confirm.ConfirmWindow(
            ba.Lstr(resource='notSignedInErrorText'),
            ba.Call(settings.AccountSettingsWindow,
                    modal=True,
                    close_once_signed_in=True),
            ok_text=ba.Lstr(resource='accountSettingsWindow.signInText'),
            width=460,
            height=130)
