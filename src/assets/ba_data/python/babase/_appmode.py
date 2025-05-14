# Released under the MIT License. See LICENSE for details.
#
"""Provides AppMode functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from babase import AppIntent


class AppMode:
    """A low level mode the app can be in.

    App-modes fundamentally change app behavior related to input
    handling, networking, graphics, and more. In a way, different
    app-modes can almost be considered different apps.
    """

    @classmethod
    def can_handle_intent(cls, intent: AppIntent) -> bool:
        """Override this to define indent handling for an app-mode."""
        raise NotImplementedError('AppMode subclasses must override this.')

    def handle_intent(self, intent: AppIntent) -> None:
        """Handle an intent."""
        raise NotImplementedError('AppMode subclasses must override this.')

    def on_activate(self) -> None:
        """Called when the mode is becoming the active one fro the app."""

    def on_deactivate(self) -> None:
        """Called when the mode stops being the active one for the app.

        On platforms where the app is explicitly exited (such as desktop
        PC) this will also be called at app shutdown.

        To best cover both mobile and desktop style platforms, actions
        such as saving state should generally happen in response to both
        :meth:`on_deactivate()` and :meth:`on_app_active_changed()`
        (when active is False).
        """

    def on_app_active_changed(self) -> None:
        """Called when the app's active state changes while in this app-mode.

        This corresponds to the app's :attr:`~babase.App.active` attr.
        App-active state becomes false when the app is hidden,
        minimized, backgrounded, etc. The app-mode may want to take
        action such as pausing a running game or saving state when this
        occurs.

        On platforms such as mobile where apps get suspended and later
        silently terminated by the OS, this is likely to be the last
        reliable place to save state/etc.

        To best cover both mobile and desktop style platforms, actions
        such as saving state should generally happen in response to both
        :meth:`on_deactivate()` and :meth:`on_app_active_changed()`
        (when active is False).
        """

    def on_purchase_process_begin(
        self, item_id: str, user_initiated: bool
    ) -> None:
        """Called when in-app-purchase processing is beginning.

        This call happens after a purchase has been completed locally
        but before its receipt/info is sent to the master-server to
        apply to the account.

        :meta private:
        """
        # pylint: disable=cyclic-import
        import babase

        del item_id  # Unused.

        # Show nothing for stuff not directly kicked off by the user.
        if not user_initiated:
            return

        babase.screenmessage(
            babase.Lstr(resource='updatingAccountText'),
            color=(0, 1, 0),
        )
        # Ick; we can be called early in the bootstrapping process
        # before we're allowed to load assets. Guard against that.
        if babase.asset_loads_allowed():
            babase.getsimplesound('click01').play()

    def on_purchase_process_end(
        self, item_id: str, user_initiated: bool, applied: bool
    ) -> None:
        """Called when in-app-purchase processing completes.

        Each call to :meth:`on_purchase_process_begin()` will be
        followed up by a call to this method. If the purchase was found
        to be valid and was applied to the account, applied will be
        True. In the case of redundant or invalid purchases or
        communication failures it will be False.

        :meta private:
        """
        # pylint: disable=cyclic-import
        import babase

        # Ignore this; we want to announce newly applied stuff even if
        # it was from a different launch or client or whatever.
        del user_initiated

        # If the purchase wasn't applied, do nothing. This likely means it
        # was redundant or something else harmless.
        if not applied:
            return

        # By default just announce the item id we got. Real app-modes
        # probably want to do something more specific based on item-id.
        babase.screenmessage(
            babase.Lstr(
                translate=('serverResponses', 'You got a ${ITEM}!'),
                subs=[('${ITEM}', item_id)],
            ),
            color=(0, 1, 0),
        )
        if babase.asset_loads_allowed():
            babase.getsimplesound('cashRegister').play()
