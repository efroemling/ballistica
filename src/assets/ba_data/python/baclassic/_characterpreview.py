# Released under the MIT License. See LICENSE for details.
#
"""Showing a character someone is working on, in a session of its own.

Someone building a character in an asset workspace's web ui can ask to
try it in their running game. The master server builds a dev version
of their package and sends us the character; :class:`CharacterPreview`
makes sure we have that package (downloading it behind the usual
progress dialog if we must, so nobody sees a stand-in while it
arrives) and then starts a :class:`CharacterPreviewSession`: a
free-for-all session of one Death Match on Rampage whose lobby offers
that character and nothing else, plus editing its profile (the cloud's
profile editor aimed at it; see ``bauiv1lib.characterpreviewui``).

The server asks repeatedly, with the same request id, until we say we
are done or have failed (see ``CharacterPreviewShowMessage``); the
first ask starts the work and the rest just report on it.
"""

import asyncio
import logging
from enum import Enum
from typing import TYPE_CHECKING, override

import babase
import bascenev1

if TYPE_CHECKING:
    from typing import Any

    from bacommon.assetpackage import ApverNum

logger = logging.getLogger('ba.classic')


class CharacterPreviewState(Enum):
    """How a showing is going; values are what the server is told."""

    WORKING = 'working'
    DONE = 'done'
    FAILED = 'failed'


class CharacterPreviewSession(bascenev1.FreeForAllSession):
    """A session for trying out one character.

    One Death Match on Rampage, round after round, with a lobby that
    offers only the character being previewed (no random profile, none
    of the player's own): whoever joins plays as it. The lobby's edit
    entry opens the profile editor for that character, as someone who
    picks it for a profile of theirs will see it; what is saved there
    is what the session offers from then on.
    """

    @override
    def get_fixed_playlist(self) -> list[dict[str, Any]] | None:
        return [
            {
                'type': 'bascenev1lib.game.deathmatch.DeathMatchGame',
                'settings': {'map': 'Rampage'},
            }
        ]

    @override
    def allows_tutorial(self) -> bool:
        # (Someone previewing a character has not come to learn to play.)
        return False

    @override
    def get_fixed_profiles(self) -> list[str] | None:
        classic = babase.app.classic
        assert classic is not None
        return list(classic.character_preview.characters)

    @override
    def can_edit_fixed_profiles(self) -> bool:
        # Half of trying a character is seeing how its profile editor
        # comes out.
        return True

    @override
    def edit_fixed_profiles(self) -> None:
        classic = babase.app.classic
        assert classic is not None
        classic.character_preview.edit()


class CharacterPreview:
    """Shows characters at the master server's request.

    One lives at ``app.classic.character_preview``.
    """

    def __init__(self) -> None:
        #: What the current (or next) preview session's lobby offers:
        #: the characters' jsons, as cloud profiles' arrive. Read by
        #: :class:`CharacterPreviewSession` as it starts.
        self.characters: list[str] = []

        self._request_id: str | None = None
        self._state = CharacterPreviewState.DONE
        self._error: str | None = None
        self._task: asyncio.Task[None] | None = None

    def show(
        self, request_id: str, apvernum: ApverNum, character: str
    ) -> tuple[CharacterPreviewState, str | None]:
        """Start showing a character, or say how showing it is going.

        Returns ``(state, error)``. The first call with a given
        ``request_id`` starts on it; later ones with the same id only
        report. A new id replaces whatever was under way. Logic thread.
        """
        assert babase.in_logic_thread()
        if request_id != self._request_id:
            if self._task is not None:
                self._task.cancel()
                self._task = None
            self._request_id = request_id
            self._error = self._why_not(character)
            if self._error is not None:
                self._state = CharacterPreviewState.FAILED
            else:
                self._state = CharacterPreviewState.WORKING
                babase.app.create_async_task(
                    self._run(request_id, apvernum, character),
                    name='character preview',
                )
        return self._state, self._error

    def edit(self) -> None:
        """Open the profile editor for the character being previewed.

        The cloud's editor, aimed at the previewed character (it goes
        by the id the character was sent under); saving there comes
        back through :meth:`apply_edit`. Logic thread.
        """
        # pylint: disable=cyclic-import
        from bauiv1lib.characterpreviewui import show_character_preview_editor

        assert babase.in_logic_thread()
        if self._request_id is None:
            return
        show_character_preview_editor(self._request_id)

    def apply_edit(self, request_id: str, character: str) -> None:
        """Carry on with a previewed character as its editor saved it.

        Ignored unless it is for the preview that is up now (a window
        left open across a newer preview, say). Logic thread.
        """
        assert babase.in_logic_thread()
        if (
            request_id != self._request_id
            or self._state is not CharacterPreviewState.DONE
        ):
            return
        session = bascenev1.get_foreground_host_session()
        if not isinstance(session, CharacterPreviewSession):
            return
        parts = bascenev1.split_character(character)
        if parts.spaz is None or parts.icon is None:
            logger.warning('Ignoring incomplete edited preview character.')
            return

        # The lobby asks the session for its profiles again on hearing
        # they changed. (Whoever is already playing keeps the look they
        # joined with until they next come through the lobby.)
        self.characters = [character]
        session.handlemessage(bascenev1.PlayerProfilesChangedMessage())

    @staticmethod
    def _why_not(character: str) -> str | None:
        """Why a character can't be shown right now (None: it can).

        Text for the person who asked, who is looking at a web page
        and not at us.
        """
        # pylint: disable=cyclic-import
        from baclassic._appmode import ClassicAppMode
        from bascenev1lib.mainmenu import MainMenuSession

        # Only classic mode has the sessions and lobby this is made
        # of. (Not expected to come up yet; once another mode can be
        # the active one, this is where switching to classic, or
        # showing the character that mode's way, goes.)
        try:
            mode = babase.app.mode
        except ValueError:
            mode = None
        if not isinstance(mode, ClassicAppMode):
            return (
                'The game is not in a mode that can show characters'
                ' right now.'
            )

        # Starting a session ends whatever one is running. Fine for
        # the main menu, and for a preview already up (trying the
        # character again after changing it); not for a game someone
        # is in the middle of.
        session = bascenev1.get_foreground_host_session()
        if session is not None and not isinstance(
            session, (MainMenuSession, CharacterPreviewSession)
        ):
            return (
                'The game is in the middle of something. Return to its'
                ' main menu and try again.'
            )

        parts = bascenev1.split_character(character)
        if parts.spaz is None or parts.icon is None:
            return 'The character sent to the game is incomplete.'
        return None

    async def _run(
        self, request_id: str, apvernum: ApverNum, character: str
    ) -> None:
        if request_id != self._request_id:
            return  # (Replaced before it got going.)
        # (Kept so a newer request can call this one off.)
        self._task = asyncio.current_task()
        try:
            error = await self._prepare_and_launch(apvernum, character)
        except asyncio.CancelledError:
            # (Replaced by a newer request, or the download dialog's
            # cancel button.)
            error = 'Cancelled in the game.'
        except Exception:
            logger.exception('Error showing a character preview.')
            error = 'The game hit an error showing the character.'
        # (Only if this is still the request anyone is asking about.)
        if request_id == self._request_id:
            self._task = None
            self._error = error
            self._state = (
                CharacterPreviewState.DONE
                if error is None
                else CharacterPreviewState.FAILED
            )

    async def _prepare_and_launch(
        self, apvernum: ApverNum, character: str
    ) -> str | None:
        """Get the package, then start the session. Returns an error."""
        # Have the character's package here before anything shows:
        # otherwise the session would come up with a stand-in drawn
        # in its place until the real look had downloaded.
        if not await bascenev1.resolve_asset_packages_with_dialog(
            [apvernum],
            task=asyncio.current_task(),
            context='character preview',
        ):
            return (
                "The game could not download the character's assets"
                ' (see the game for details).'
            )

        # Things may have moved on while that was downloading.
        error = self._why_not(character)
        if error is not None:
            return error

        self.characters = [character]
        launched: asyncio.Future[str | None] = (
            asyncio.get_running_loop().create_future()
        )

        def _fade_end() -> None:
            # pylint: disable=cyclic-import
            from bascenev1lib.mainmenu import MainMenuSession

            babase.unlock_all_input()
            try:
                bascenev1.new_host_session(CharacterPreviewSession)
            except Exception:
                logger.exception('Error starting character preview session.')
                bascenev1.new_host_session(MainMenuSession)
                if not launched.done():
                    launched.set_result(
                        'The game could not start a session for the'
                        ' character.'
                    )
                return
            if not launched.done():
                launched.set_result(None)

        # Save where we are in the UI to come back to when done.
        classic = babase.app.classic
        assert classic is not None
        classic.save_ui_state()
        babase.fade_screen(False, endcall=_fade_end)
        babase.lock_all_input()
        return await launched
