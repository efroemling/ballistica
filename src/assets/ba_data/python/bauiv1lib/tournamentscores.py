# Released under the MIT License. See LICENSE for details.
#
"""Provides a popup for viewing tournament scores."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from bauiv1lib.popup import PopupWindow
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any, Sequence, Callable

    import bascenev1 as bs


class TournamentScoresWindow(PopupWindow):
    """Window for viewing tournament scores."""

    def __init__(
        self,
        tournament_id: str,
        *,
        position: tuple[float, float] = (0.0, 0.0),
    ):
        plus = bui.app.plus
        assert plus is not None

        self._tournament_id = tournament_id
        self._subcontainer: bui.Widget | None = None
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        scale = (
            2.3
            if uiscale is bui.UIScale.SMALL
            else 1.65 if uiscale is bui.UIScale.MEDIUM else 1.23
        )
        self._transitioning_out = False

        self._width = 400
        self._height = (
            300
            if uiscale is bui.UIScale.SMALL
            else 370 if uiscale is bui.UIScale.MEDIUM else 450
        )

        bg_color = (0.5, 0.4, 0.6)

        # Creates our _root_widget.
        super().__init__(
            position=position,
            size=(self._width, self._height),
            scale=scale,
            bg_color=bg_color,
        )

        self._cancel_button = bui.buttonwidget(
            parent=self.root_widget,
            position=(50, self._height - 30),
            size=(50, 50),
            scale=0.5,
            label='',
            color=bg_color,
            on_activate_call=self._on_cancel_press,
            autoselect=True,
            icon=bui.gettexture('crossOut'),
            iconscale=1.2,
        )

        self._title_text = bui.textwidget(
            parent=self.root_widget,
            position=(self._width * 0.5, self._height - 20),
            size=(0, 0),
            h_align='center',
            v_align='center',
            scale=0.6,
            text=bui.Lstr(resource='tournamentStandingsText'),
            maxwidth=200,
            color=bui.app.ui_v1.title_color,
        )

        self._scrollwidget = bui.scrollwidget(
            parent=self.root_widget,
            size=(self._width - 60, self._height - 70),
            position=(30, 30),
            highlight=False,
            simple_culling_v=10,
            border_opacity=0.4,
        )
        bui.widget(edit=self._scrollwidget, autoselect=True)

        self._loading_spinner = bui.spinnerwidget(
            parent=self.root_widget,
            position=(self._width * 0.5, self._height * 0.5),
            style='bomb',
            size=48,
        )
        self._loading_text = bui.textwidget(
            parent=self._scrollwidget,
            scale=0.5,
            text='',
            size=(self._width - 60, 100),
            h_align='center',
            v_align='center',
        )

        bui.containerwidget(
            edit=self.root_widget, cancel_button=self._cancel_button
        )

        plus.tournament_query(
            args={
                'tournamentIDs': [tournament_id],
                'numScores': 50,
                'source': 'scores window',
            },
            callback=bui.WeakCall(self._on_tournament_query_response),
        )

    def _on_tournament_query_response(
        self, data: dict[str, Any] | None
    ) -> None:
        if data is not None:
            # This used to be the whole payload.
            data_t: list[dict[str, Any]] = data['t']

            # Kill our loading text if we've got scores; otherwise just
            # replace it with 'no scores yet'.
            bui.spinnerwidget(edit=self._loading_spinner, visible=False)
            if data_t[0]['scores']:
                self._loading_text.delete()
            else:
                bui.textwidget(
                    edit=self._loading_text,
                    text=bui.Lstr(resource='noScoresYetText'),
                )
            incr = 30
            sub_width = self._width - 90
            sub_height = 30 + len(data_t[0]['scores']) * incr
            self._subcontainer = bui.containerwidget(
                parent=self._scrollwidget,
                size=(sub_width, sub_height),
                background=False,
            )
            for i, entry in enumerate(data_t[0]['scores']):
                bui.textwidget(
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

                bui.textwidget(
                    parent=self._subcontainer,
                    position=(sub_width * 0.25 - 2, sub_height - 20 - incr * i),
                    maxwidth=sub_width * 0.24,
                    color=(0.9, 1.0, 0.9),
                    flatness=1.0,
                    shadow=0.0,
                    scale=0.6,
                    text=(
                        bui.timestring(
                            (entry[0] * 10) / 1000.0,
                            centi=True,
                        )
                        if data_t[0]['scoreType'] == 'time'
                        else str(entry[0])
                    ),
                    size=(0, 0),
                    h_align='center',
                    v_align='center',
                )

                txt = bui.textwidget(
                    parent=self._subcontainer,
                    position=(
                        sub_width * 0.25,
                        sub_height - 20 - incr * i - (0.5 / 0.7) * incr,
                    ),
                    maxwidth=sub_width * 0.6,
                    scale=0.7,
                    flatness=1.0,
                    shadow=0.0,
                    text=bui.Lstr(value=entry[1]),
                    selectable=True,
                    click_activate=True,
                    autoselect=True,
                    extra_touch_border_scale=0.0,
                    size=((sub_width * 0.6) / 0.7, incr / 0.7),
                    h_align='left',
                    v_align='center',
                )

                bui.textwidget(
                    edit=txt,
                    on_activate_call=bui.Call(
                        self._show_player_info, entry, txt
                    ),
                )
                if i == 0:
                    bui.widget(edit=txt, up_widget=self._cancel_button)

    def _show_player_info(self, entry: Any, textwidget: bui.Widget) -> None:
        from bauiv1lib.account.viewer import AccountViewerWindow

        # For the moment we only work if a single player-info is
        # present.
        if len(entry[2]) != 1:
            bui.getsound('error').play()
            return
        bui.getsound('swish').play()
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
            bui.containerwidget(edit=self.root_widget, transition='out_scale')

    @override
    def on_popup_cancel(self) -> None:
        bui.getsound('swish').play()
        self._transition_out()
