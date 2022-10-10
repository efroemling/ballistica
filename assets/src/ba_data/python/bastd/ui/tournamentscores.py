# Released under the MIT License. See LICENSE for details.
#
"""Provides a popup for viewing tournament scores."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
import ba.internal
from bastd.ui import popup as popup_ui

if TYPE_CHECKING:
    from typing import Any, Sequence, Callable


class TournamentScoresWindow(popup_ui.PopupWindow):
    """Window for viewing tournament scores."""

    def __init__(
        self,
        tournament_id: str,
        tournament_activity: ba.GameActivity | None = None,
        position: tuple[float, float] = (0.0, 0.0),
        scale: float | None = None,
        offset: tuple[float, float] = (0.0, 0.0),
        tint_color: Sequence[float] = (1.0, 1.0, 1.0),
        tint2_color: Sequence[float] = (1.0, 1.0, 1.0),
        selected_character: str | None = None,
        on_close_call: Callable[[], Any] | None = None,
    ):

        del tournament_activity  # unused arg
        del tint_color  # unused arg
        del tint2_color  # unused arg
        del selected_character  # unused arg
        self._tournament_id = tournament_id
        self._subcontainer: ba.Widget | None = None
        self._on_close_call = on_close_call
        uiscale = ba.app.ui.uiscale
        if scale is None:
            scale = (
                2.3
                if uiscale is ba.UIScale.SMALL
                else 1.65
                if uiscale is ba.UIScale.MEDIUM
                else 1.23
            )
        self._transitioning_out = False

        self._width = 400
        self._height = (
            300
            if uiscale is ba.UIScale.SMALL
            else 370
            if uiscale is ba.UIScale.MEDIUM
            else 450
        )

        bg_color = (0.5, 0.4, 0.6)

        # creates our _root_widget
        super().__init__(
            position=position,
            size=(self._width, self._height),
            scale=scale,
            bg_color=bg_color,
            offset=offset,
        )

        # app = ba.app

        self._cancel_button = ba.buttonwidget(
            parent=self.root_widget,
            position=(50, self._height - 30),
            size=(50, 50),
            scale=0.5,
            label='',
            color=bg_color,
            on_activate_call=self._on_cancel_press,
            autoselect=True,
            icon=ba.gettexture('crossOut'),
            iconscale=1.2,
        )

        self._title_text = ba.textwidget(
            parent=self.root_widget,
            position=(self._width * 0.5, self._height - 20),
            size=(0, 0),
            h_align='center',
            v_align='center',
            scale=0.6,
            text=ba.Lstr(resource='tournamentStandingsText'),
            maxwidth=200,
            color=(1, 1, 1, 0.4),
        )

        self._scrollwidget = ba.scrollwidget(
            parent=self.root_widget,
            size=(self._width - 60, self._height - 70),
            position=(30, 30),
            highlight=False,
            simple_culling_v=10,
        )
        ba.widget(edit=self._scrollwidget, autoselect=True)

        self._loading_text = ba.textwidget(
            parent=self._scrollwidget,
            scale=0.5,
            text=ba.Lstr(
                value='${A}...',
                subs=[('${A}', ba.Lstr(resource='loadingText'))],
            ),
            size=(self._width - 60, 100),
            h_align='center',
            v_align='center',
        )

        ba.containerwidget(
            edit=self.root_widget, cancel_button=self._cancel_button
        )

        ba.internal.tournament_query(
            args={
                'tournamentIDs': [tournament_id],
                'numScores': 50,
                'source': 'scores window',
            },
            callback=ba.WeakCall(self._on_tournament_query_response),
        )

    def _on_tournament_query_response(
        self, data: dict[str, Any] | None
    ) -> None:
        if data is not None:
            # this used to be the whole payload
            data_t: list[dict[str, Any]] = data['t']
            # kill our loading text if we've got scores.. otherwise just
            # replace it with 'no scores yet'
            if data_t[0]['scores']:
                self._loading_text.delete()
            else:
                ba.textwidget(
                    edit=self._loading_text,
                    text=ba.Lstr(resource='noScoresYetText'),
                )
            incr = 30
            sub_width = self._width - 90
            sub_height = 30 + len(data_t[0]['scores']) * incr
            self._subcontainer = ba.containerwidget(
                parent=self._scrollwidget,
                size=(sub_width, sub_height),
                background=False,
            )
            for i, entry in enumerate(data_t[0]['scores']):

                ba.textwidget(
                    parent=self._subcontainer,
                    position=(sub_width * 0.1 - 5, sub_height - 20 - incr * i),
                    maxwidth=20,
                    scale=0.5,
                    color=(0.6, 0.6, 0.7),
                    flatness=1.0,
                    shadow=0.0,
                    text=str(i + 1),
                    size=(0, 0),
                    h_align='right',
                    v_align='center',
                )

                ba.textwidget(
                    parent=self._subcontainer,
                    position=(sub_width * 0.25 - 2, sub_height - 20 - incr * i),
                    maxwidth=sub_width * 0.24,
                    color=(0.9, 1.0, 0.9),
                    flatness=1.0,
                    shadow=0.0,
                    scale=0.6,
                    text=(
                        ba.timestring(
                            entry[0] * 10,
                            centi=True,
                            timeformat=ba.TimeFormat.MILLISECONDS,
                        )
                        if data_t[0]['scoreType'] == 'time'
                        else str(entry[0])
                    ),
                    size=(0, 0),
                    h_align='center',
                    v_align='center',
                )

                txt = ba.textwidget(
                    parent=self._subcontainer,
                    position=(
                        sub_width * 0.25,
                        sub_height - 20 - incr * i - (0.5 / 0.7) * incr,
                    ),
                    maxwidth=sub_width * 0.6,
                    scale=0.7,
                    flatness=1.0,
                    shadow=0.0,
                    text=ba.Lstr(value=entry[1]),
                    selectable=True,
                    click_activate=True,
                    autoselect=True,
                    extra_touch_border_scale=0.0,
                    size=((sub_width * 0.6) / 0.7, incr / 0.7),
                    h_align='left',
                    v_align='center',
                )

                ba.textwidget(
                    edit=txt,
                    on_activate_call=ba.Call(
                        self._show_player_info, entry, txt
                    ),
                )
                if i == 0:
                    ba.widget(edit=txt, up_widget=self._cancel_button)

    def _show_player_info(self, entry: Any, textwidget: ba.Widget) -> None:
        from bastd.ui.account.viewer import AccountViewerWindow

        # for the moment we only work if a single player-info is present..
        if len(entry[2]) != 1:
            ba.playsound(ba.getsound('error'))
            return
        ba.playsound(ba.getsound('swish'))
        AccountViewerWindow(
            account_id=entry[2][0].get('a', None),
            profile_id=entry[2][0].get('p', None),
            position=textwidget.get_screen_space_center(),
        )
        self._transition_out()

    def _on_cancel_press(self) -> None:
        self._transition_out()

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            ba.containerwidget(edit=self.root_widget, transition='out_scale')
            if self._on_close_call is not None:
                self._on_close_call()

    def on_popup_cancel(self) -> None:
        ba.playsound(ba.getsound('swish'))
        self._transition_out()
