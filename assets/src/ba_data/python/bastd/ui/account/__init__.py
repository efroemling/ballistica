# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
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
            lambda: settings.AccountSettingsWindow(modal=True,
                                                   close_once_signed_in=True),
            ok_text=ba.Lstr(resource='accountSettingsWindow.signInText'),
            width=460,
            height=130)
