# Released under the MIT License. See LICENSE for details.
#
"""Auxiliary-window navigation (see UIV1AppSubsystem)."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable

    import bauiv1
    from bauiv1._appsubsystem import UIV1AppSubsystem


def auxiliary_window_activate(
    ui: UIV1AppSubsystem,
    win_type: type[bauiv1.MainWindow],
    win_create_call: Callable[[], bauiv1.MainWindow],
    win_extra_type_id: str,
) -> None:
    """Implements UIV1AppSubsystem.auxiliary_window_activate()."""
    # pylint: disable=unidiomatic-typecheck

    current_main_window = ui.get_main_window()

    # With no main window up at all (mid-game, with just an overlay such
    # as the party window showing), we simply become the top-level one;
    # backing out of us then closes the ui.
    if current_main_window is None:
        ui.set_main_window(
            win_create_call(),
            from_window=False,  # Disable from-check.
            back_state=None,
            suppress_warning=True,
            is_top_level=True,
            is_auxiliary=True,
            extra_type_id=win_extra_type_id,
        )
        return

    # Scan our ancestors for auxiliary states matching our type as
    # well as auxiliary states in general.
    aux_matching_state: bauiv1.MainWindowState | None = None
    aux_state: bauiv1.MainWindowState | None = None
    state = current_main_window.main_window_back_state
    while state is not None:
        assert state.window_type is not None
        assert state.extra_type_id is not None
        if state.is_auxiliary:
            if (
                state.window_type is win_type
                and state.extra_type_id == win_extra_type_id
            ):
                aux_matching_state = state
            else:
                aux_state = state

        state = state.parent

    # If there's an ancestor auxiliary window-state matching our type,
    # back out past it (example: poking settings, navigating down a
    # level or two, and then poking settings again should back out of
    # settings). If it was top-level, there's nothing past it.
    if aux_matching_state is not None:
        if aux_matching_state.is_top_level:
            ui.clear_main_window()
            return
        current_main_window.main_window_back_state = aux_matching_state.parent
        current_main_window.main_window_back()
        return

    # If there's an ancestor auxiliary state *not* matching our type,
    # crop the state and swap in our new auxiliary UI (example: poking
    # settings, then poking account, then poking back should end up
    # where things were before the settings poke). We take over its
    # top-level-ness.
    if aux_state is not None:
        # Blow away the window stack and build a fresh one.
        ui.clear_main_window()
        ui.set_main_window(
            win_create_call(),
            from_window=False,  # Disable from-check.
            back_state=aux_state.parent,
            suppress_warning=True,
            is_top_level=bool(aux_state.is_top_level),
            is_auxiliary=True,
            extra_type_id=win_extra_type_id,
        )
        return

    # Ok, no auxiliary states found. Now if current window is auxiliary
    # and the type/extra-id matches, simply do a back.
    if (
        current_main_window.main_window_is_auxiliary
        and type(current_main_window) is win_type
        and current_main_window.main_window_extra_type_id == win_extra_type_id
    ):
        current_main_window.main_window_back()
        return

    # If current window is auxiliary but type/extra-id doesn't match,
    # swap it out for our new auxiliary UI (taking over its
    # top-level-ness).
    if current_main_window.main_window_is_auxiliary:
        ui.clear_main_window()
        ui.set_main_window(
            win_create_call(),
            from_window=False,  # Disable from-check.
            back_state=current_main_window.main_window_back_state,
            suppress_warning=True,
            is_top_level=current_main_window.main_window_is_top_level,
            is_auxiliary=True,
            extra_type_id=win_extra_type_id,
        )
        return

    # Ok, no existing auxiliary stuff was found period. Just navigate
    # forward to this UI.
    new_main_win = current_main_window.main_window_replace(
        win_create_call,
        is_auxiliary=True,
        extra_type_id=win_extra_type_id,
    )

    # We should always be allowed to replace the main win in this case.
    assert new_main_win is not None

    # Make sure what got made exactly matches the type we were passed.
    assert type(new_main_win) is win_type
