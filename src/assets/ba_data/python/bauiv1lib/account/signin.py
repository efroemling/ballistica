# Released under the MIT License. See LICENSE for details.
#
"""UI functionality related to accounts."""

from __future__ import annotations

import bauiv1 as bui


def show_sign_in_prompt() -> None:
    """Bring up a prompt telling the user they must sign in."""
    from bauiv1lib.confirm import ConfirmWindow

    ConfirmWindow(
        bui.Lstr(resource='notSignedInErrorText'),
        _show_account_settings,
        ok_text=bui.Lstr(resource='accountSettingsWindow.signInText'),
        width=460,
        height=130,
    )


def _show_account_settings() -> None:
    from bauiv1lib.account.settings import AccountSettingsWindow

    # NOTE TO USERS: The code below is not the proper way to do things;
    # whenever possible one should use a MainWindow's
    # main_window_replace() or main_window_back() methods. We just need
    # to do things a bit more manually in this case.

    prev_main_window = bui.app.ui_v1.get_main_window()

    # Special-case: If it seems we're already in the account window, do
    # nothing.
    if isinstance(prev_main_window, AccountSettingsWindow):
        return

    # Set our new main window.
    bui.app.ui_v1.set_main_window(
        AccountSettingsWindow(
            close_once_signed_in=True,
            origin_widget=bui.get_special_widget('account_button'),
        ),
        from_window=False,
        is_auxiliary=True,
        suppress_warning=True,
    )

    # Transition out any previous main window.
    if prev_main_window is not None:
        prev_main_window.main_window_close()
