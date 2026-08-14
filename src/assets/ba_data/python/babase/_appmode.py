# Released under the MIT License. See LICENSE for details.
#
"""Provides AppMode functionality."""

from enum import Enum
from typing import TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from collections.abc import Callable

    from babase import AppIntent, DevConsoleButtonDef


class ControlPermission(Enum):
    """An app-mode's answer to a request to control the app."""

    #: The user (or policy) allows it.
    ALLOW = 'allow'

    #: The user (or policy) refuses it. This is sticky -- the
    #: requester is turned away for a while without asking again,
    #: so a repeated request can't wear someone down.
    DENY = 'deny'

    #: No answer is possible *right now* -- this mode has no way to
    #: ask. Distinct from DENY on purpose, because a request
    #: arriving during bring-up should be held and put to the user
    #: once a mode that can ask becomes active, not refused.
    CANNOT_ASK = 'cannot_ask'


@dataclass
class ControlPermissionRequest:
    """Someone asking for permission to control this app."""

    #: Display name of whoever is asking -- an account tag, vouched
    #: for by the master server, so it can be shown as fact rather
    #: than as a claim. ``None`` when it couldn't be established.
    #:
    #: Classic deliberately does not show this: today's only caller
    #: (the cloud console) can reach a device only by owning it, so
    #: the tag is always the viewer's own and naming it says nothing.
    #: Kept because that is a property of the current caller, not of
    #: this request -- anything reachable by someone else would need
    #: it back.
    requester_name: str | None = None

    #: Opaque stable id for the requester, the same across their
    #: sessions. A remembered grant hangs off this. ``None`` means
    #: this requester can't be recognized again, so any allowance
    #: must apply to this request alone.
    requester_key: str | None = None


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

    def on_control_permission_request(
        self,
        request: ControlPermissionRequest,
        on_result: Callable[[ControlPermission], None],
    ) -> None:
        """Ask the user whether something may control the app.

        'Control' is deliberately broad: running commands, reading
        this app's log, and whatever that grows into. Answer via
        ``on_result``, which may be called later (from a dialog) or
        immediately (from policy).

        The default answers ``CANNOT_ASK``, which is the honest
        answer for a mode with no way to prompt -- the request is
        then held and re-put once a mode that can ask activates.
        An app-mode with a UI should override this; one running
        without a user present (a dedicated server) should answer
        ``ALLOW``, since nobody is there to ask and the operator
        already owns the account.
        """
        del request  # Unused.
        on_result(ControlPermission.CANNOT_ASK)

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

        from babase import builtinassets

        del item_id  # Unused.

        # Show nothing for stuff not directly kicked off by the user.
        if not user_initiated:
            return

        babase.screenmessage(
            builtinassets.strings.account.updating_account,
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
        from babase import builtinassets

        babase.screenmessage(
            builtinassets.strings.account.you_got_item(item=item_id),
            color=(0, 1, 0),
        )
        if babase.asset_loads_allowed():
            babase.getsimplesound('cashRegister').play()

    def get_dev_console_ui_tab_buttons(self) -> list[DevConsoleButtonDef]:
        """Define buttons to show up in the UI dev console.

        This can be useful for exposing UI code examples or debugging
        functionality.
        """
        return []
