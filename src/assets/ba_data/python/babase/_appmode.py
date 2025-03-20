# Released under the MIT License. See LICENSE for details.
#
"""Provides AppMode functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bacommon.app import AppExperience
    from babase._appintent import AppIntent


class AppMode:
    """A high level mode for the app.

    Category: **App Classes**
    """

    @classmethod
    def get_app_experience(cls) -> AppExperience:
        """Return the overall experience provided by this mode."""
        raise NotImplementedError('AppMode subclasses must override this.')

    @classmethod
    def can_handle_intent(cls, intent: AppIntent) -> bool:
        """Return whether this mode can handle the provided intent.

        For this to return True, the AppMode must claim to support the
        provided intent (via its _can_handle_intent() method) AND the
        AppExperience associated with the AppMode must be supported by
        the current app and runtime environment.
        """
        # TODO: check AppExperience against current environment.
        return cls._can_handle_intent(intent)

    @classmethod
    def _can_handle_intent(cls, intent: AppIntent) -> bool:
        """Return whether our mode can handle the provided intent.

        AppModes should override this to communicate what they can
        handle. Note that AppExperience does not have to be considered
        here; that is handled automatically by the can_handle_intent()
        call.
        """
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
        on_deactivate() and on_app_active_changed() (when active is
        False).
        """

    def on_app_active_changed(self) -> None:
        """Called when ba*.app.active changes while in this app-mode.

        App-active state becomes false when the app is hidden,
        minimized, backgrounded, etc. The app-mode may want to take
        action such as pausing a running game or saving state when this
        occurs.

        On platforms such as mobile where apps get suspended and later
        silently terminated by the OS, this is likely to be the last
        reliable place to save state/etc.

        To best cover both mobile and desktop style platforms, actions
        such as saving state should generally happen in response to both
        on_deactivate() and on_app_active_changed() (when active is
        False).
        """

    def on_purchase_process_begin(
        self, item_id: str, user_initiated: bool
    ) -> None:
        """Called when in-app-purchase processing is beginning.

        This call happens after a purchase has been completed locally
        but before its receipt/info is sent to the master-server to
        apply to the account.
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

        Each call to on_purchase_process_begin will be followed up by a
        call to this method. If the purchase was found to be valid and
        was applied to the account, applied will be True. In the case of
        redundant or invalid purchases or communication failures it will
        be False.
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
