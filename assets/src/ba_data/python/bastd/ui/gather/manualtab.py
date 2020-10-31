# Released under the MIT License. See LICENSE for details.
#
"""Defines the manual tab in the gather UI."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, cast

import _ba
import ba
from bastd.ui.gather.bases import GatherTab

if TYPE_CHECKING:
    from typing import Callable, Optional, Any, Union, Dict
    from bastd.ui.gather import GatherWindow


def _safe_set_text(txt: Optional[ba.Widget],
                   val: Union[str, ba.Lstr],
                   success: bool = True) -> None:
    if txt:
        ba.textwidget(edit=txt,
                      text=val,
                      color=(0, 1, 0) if success else (1, 1, 0))


class _HostLookupThread(threading.Thread):
    """Thread to fetch an addr."""

    def __init__(self, name: str, port: int,
                 call: Callable[[Optional[str], int], Any]):
        super().__init__()
        self._name = name
        self._port = port
        self._call = call

    def run(self) -> None:
        result: Optional[str]
        try:
            import socket
            result = socket.gethostbyname(self._name)
        except Exception:
            result = None
        ba.pushcall(lambda: self._call(result, self._port),
                    from_other_thread=True)


class ManualGatherTab(GatherTab):
    """The manual tab in the gather UI"""

    def __init__(self, window: GatherWindow) -> None:
        super().__init__(window)
        self._check_button: Optional[ba.Widget] = None
        self._doing_access_check: Optional[bool] = None
        self._access_check_count: Optional[int] = None
        self._t_addr: Optional[ba.Widget] = None
        self._t_accessible: Optional[ba.Widget] = None
        self._t_accessible_extra: Optional[ba.Widget] = None
        self._access_check_timer: Optional[ba.Timer] = None
        self._checking_state_text: Optional[ba.Widget] = None
        self._container: Optional[ba.Widget] = None

    def on_activate(
        self,
        parent_widget: ba.Widget,
        tab_button: ba.Widget,
        region_width: float,
        region_height: float,
        region_left: float,
        region_bottom: float,
    ) -> ba.Widget:

        c_width = region_width
        c_height = 380
        last_addr = ba.app.config.get('Last Manual Party Connect Address', '')

        self._container = ba.containerwidget(
            parent=parent_widget,
            position=(region_left,
                      region_bottom + (region_height - c_height) * 0.5),
            size=(c_width, c_height),
            background=False,
            selection_loops_to_parent=True)
        v = c_height - 30
        ba.textwidget(parent=self._container,
                      position=(c_width * 0.5, v),
                      color=(0.6, 1.0, 0.6),
                      scale=1.3,
                      size=(0, 0),
                      maxwidth=c_width * 0.9,
                      h_align='center',
                      v_align='center',
                      text=ba.Lstr(resource='gatherWindow.'
                                   'manualDescriptionText'))
        v -= 30
        v -= 70
        ba.textwidget(parent=self._container,
                      position=(c_width * 0.5 - 260 - 50, v),
                      color=(0.6, 1.0, 0.6),
                      scale=1.0,
                      size=(0, 0),
                      maxwidth=130,
                      h_align='right',
                      v_align='center',
                      text=ba.Lstr(resource='gatherWindow.'
                                   'manualAddressText'))
        txt = ba.textwidget(parent=self._container,
                            editable=True,
                            description=ba.Lstr(resource='gatherWindow.'
                                                'manualAddressText'),
                            position=(c_width * 0.5 - 240 - 50, v - 30),
                            text=last_addr,
                            autoselect=True,
                            v_align='center',
                            scale=1.0,
                            size=(420, 60))
        ba.textwidget(parent=self._container,
                      position=(c_width * 0.5 - 260 + 490, v),
                      color=(0.6, 1.0, 0.6),
                      scale=1.0,
                      size=(0, 0),
                      maxwidth=80,
                      h_align='right',
                      v_align='center',
                      text=ba.Lstr(resource='gatherWindow.'
                                   'portText'))
        txt2 = ba.textwidget(parent=self._container,
                             editable=True,
                             description=ba.Lstr(resource='gatherWindow.'
                                                 'portText'),
                             text='43210',
                             autoselect=True,
                             max_chars=5,
                             position=(c_width * 0.5 - 240 + 490, v - 30),
                             v_align='center',
                             scale=1.0,
                             size=(170, 60))

        v -= 110

        btn = ba.buttonwidget(parent=self._container,
                              size=(300, 70),
                              label=ba.Lstr(resource='gatherWindow.'
                                            'manualConnectText'),
                              position=(c_width * 0.5 - 150, v),
                              autoselect=True,
                              on_activate_call=ba.Call(self._connect, txt,
                                                       txt2))
        ba.widget(edit=txt, up_widget=tab_button)
        ba.textwidget(edit=txt, on_return_press_call=btn.activate)
        ba.textwidget(edit=txt2, on_return_press_call=btn.activate)
        v -= 45

        self._check_button = ba.textwidget(
            parent=self._container,
            size=(250, 60),
            text=ba.Lstr(resource='gatherWindow.'
                         'showMyAddressText'),
            v_align='center',
            h_align='center',
            click_activate=True,
            position=(c_width * 0.5 - 125, v - 30),
            autoselect=True,
            color=(0.5, 0.9, 0.5),
            scale=0.8,
            selectable=True,
            on_activate_call=ba.Call(self._on_show_my_address_button_press, v,
                                     self._container, c_width))
        return self._container

    def on_deactivate(self) -> None:
        self._access_check_timer = None

    def _connect(self, textwidget: ba.Widget,
                 port_textwidget: ba.Widget) -> None:
        addr = cast(str, ba.textwidget(query=textwidget))
        if addr == '':
            ba.screenmessage(
                ba.Lstr(resource='internal.invalidAddressErrorText'),
                color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return
        try:
            port = int(cast(str, ba.textwidget(query=port_textwidget)))
        except ValueError:
            # EWWWW; this exception causes a dependency loop that won't
            # go away until the next cyclical collection, which can
            # keep us alive. Perhaps should rethink our garbage
            # collection strategy, but for now just explicitly running
            # a cycle.
            ba.pushcall(ba.garbage_collect)
            port = -1
        if port > 65535 or port < 0:
            ba.screenmessage(ba.Lstr(resource='internal.invalidPortErrorText'),
                             color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return

        _HostLookupThread(name=addr,
                          port=port,
                          call=ba.WeakCall(self._host_lookup_result)).start()

    def _host_lookup_result(self, resolved_address: Optional[str],
                            port: int) -> None:
        if resolved_address is None:
            ba.screenmessage(
                ba.Lstr(resource='internal.unableToResolveHostText'),
                color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
        else:
            # Store for later.
            config = ba.app.config
            config['Last Manual Party Connect Address'] = resolved_address
            config.commit()
            _ba.connect_to_party(resolved_address, port=port)

    def _run_addr_fetch(self) -> None:
        try:
            # FIXME: Update this to work with IPv6.
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(('8.8.8.8', 80))
            val = sock.getsockname()[0]
            sock.close()
            ba.pushcall(
                ba.Call(
                    _safe_set_text,
                    self._checking_state_text,
                    val,
                ),
                from_other_thread=True,
            )
        except Exception as exc:
            err_str = str(exc)

            # FIXME: Should look at exception types here,
            #  not strings.
            if 'Network is unreachable' in err_str:
                ba.pushcall(ba.Call(
                    _safe_set_text, self._checking_state_text,
                    ba.Lstr(resource='gatherWindow.'
                            'noConnectionText'), False),
                            from_other_thread=True)
            else:
                ba.pushcall(ba.Call(
                    _safe_set_text, self._checking_state_text,
                    ba.Lstr(resource='gatherWindow.'
                            'addressFetchErrorText'), False),
                            from_other_thread=True)
                ba.pushcall(ba.Call(ba.print_error,
                                    'error in AddrFetchThread: ' + str(exc)),
                            from_other_thread=True)

    def _on_show_my_address_button_press(self, v2: float,
                                         container: Optional[ba.Widget],
                                         c_width: float) -> None:
        if not container:
            return

        tscl = 0.85
        tspc = 25

        ba.playsound(ba.getsound('swish'))
        ba.textwidget(parent=container,
                      position=(c_width * 0.5 - 10, v2),
                      color=(0.6, 1.0, 0.6),
                      scale=tscl,
                      size=(0, 0),
                      maxwidth=c_width * 0.45,
                      flatness=1.0,
                      h_align='right',
                      v_align='center',
                      text=ba.Lstr(resource='gatherWindow.'
                                   'manualYourLocalAddressText'))
        self._checking_state_text = ba.textwidget(
            parent=container,
            position=(c_width * 0.5, v2),
            color=(0.5, 0.5, 0.5),
            scale=tscl,
            size=(0, 0),
            maxwidth=c_width * 0.45,
            flatness=1.0,
            h_align='left',
            v_align='center',
            text=ba.Lstr(resource='gatherWindow.'
                         'checkingText'))

        threading.Thread(target=self._run_addr_fetch).start()

        v2 -= tspc
        ba.textwidget(parent=container,
                      position=(c_width * 0.5 - 10, v2),
                      color=(0.6, 1.0, 0.6),
                      scale=tscl,
                      size=(0, 0),
                      maxwidth=c_width * 0.45,
                      flatness=1.0,
                      h_align='right',
                      v_align='center',
                      text=ba.Lstr(resource='gatherWindow.'
                                   'manualYourAddressFromInternetText'))

        t_addr = ba.textwidget(parent=container,
                               position=(c_width * 0.5, v2),
                               color=(0.5, 0.5, 0.5),
                               scale=tscl,
                               size=(0, 0),
                               maxwidth=c_width * 0.45,
                               h_align='left',
                               v_align='center',
                               flatness=1.0,
                               text=ba.Lstr(resource='gatherWindow.'
                                            'checkingText'))
        v2 -= tspc
        ba.textwidget(parent=container,
                      position=(c_width * 0.5 - 10, v2),
                      color=(0.6, 1.0, 0.6),
                      scale=tscl,
                      size=(0, 0),
                      maxwidth=c_width * 0.45,
                      flatness=1.0,
                      h_align='right',
                      v_align='center',
                      text=ba.Lstr(resource='gatherWindow.'
                                   'manualJoinableFromInternetText'))

        t_accessible = ba.textwidget(parent=container,
                                     position=(c_width * 0.5, v2),
                                     color=(0.5, 0.5, 0.5),
                                     scale=tscl,
                                     size=(0, 0),
                                     maxwidth=c_width * 0.45,
                                     flatness=1.0,
                                     h_align='left',
                                     v_align='center',
                                     text=ba.Lstr(resource='gatherWindow.'
                                                  'checkingText'))
        v2 -= 28
        t_accessible_extra = ba.textwidget(parent=container,
                                           position=(c_width * 0.5, v2),
                                           color=(1, 0.5, 0.2),
                                           scale=0.7,
                                           size=(0, 0),
                                           maxwidth=c_width * 0.9,
                                           flatness=1.0,
                                           h_align='center',
                                           v_align='center',
                                           text='')

        self._doing_access_check = False
        self._access_check_count = 0  # Cap our refreshes eventually.
        self._access_check_timer = ba.Timer(
            10.0,
            ba.WeakCall(self._access_check_update, t_addr, t_accessible,
                        t_accessible_extra),
            repeat=True,
            timetype=ba.TimeType.REAL)

        # Kick initial off.
        self._access_check_update(t_addr, t_accessible, t_accessible_extra)
        if self._check_button:
            self._check_button.delete()

    def _access_check_update(self, t_addr: ba.Widget, t_accessible: ba.Widget,
                             t_accessible_extra: ba.Widget) -> None:
        from ba.internal import master_server_get

        # If we don't have an outstanding query, start one..
        assert self._doing_access_check is not None
        assert self._access_check_count is not None
        if not self._doing_access_check and self._access_check_count < 100:
            self._doing_access_check = True
            self._access_check_count += 1
            self._t_addr = t_addr
            self._t_accessible = t_accessible
            self._t_accessible_extra = t_accessible_extra
            master_server_get('bsAccessCheck', {'b': ba.app.build_number},
                              callback=ba.WeakCall(
                                  self._on_accessible_response))

    def _on_accessible_response(self, data: Optional[Dict[str, Any]]) -> None:
        t_addr = self._t_addr
        t_accessible = self._t_accessible
        t_accessible_extra = self._t_accessible_extra
        self._doing_access_check = False
        color_bad = (1, 1, 0)
        color_good = (0, 1, 0)
        if data is None or 'address' not in data or 'accessible' not in data:
            if t_addr:
                ba.textwidget(edit=t_addr,
                              text=ba.Lstr(resource='gatherWindow.'
                                           'noConnectionText'),
                              color=color_bad)
            if t_accessible:
                ba.textwidget(edit=t_accessible,
                              text=ba.Lstr(resource='gatherWindow.'
                                           'noConnectionText'),
                              color=color_bad)
            if t_accessible_extra:
                ba.textwidget(edit=t_accessible_extra,
                              text='',
                              color=color_bad)
            return
        if t_addr:
            ba.textwidget(edit=t_addr, text=data['address'], color=color_good)
        if t_accessible:
            if data['accessible']:
                ba.textwidget(edit=t_accessible,
                              text=ba.Lstr(resource='gatherWindow.'
                                           'manualJoinableYesText'),
                              color=color_good)
                if t_accessible_extra:
                    ba.textwidget(edit=t_accessible_extra,
                                  text='',
                                  color=color_good)
            else:
                ba.textwidget(
                    edit=t_accessible,
                    text=ba.Lstr(resource='gatherWindow.'
                                 'manualJoinableNoWithAsteriskText'),
                    color=color_bad,
                )
                if t_accessible_extra:
                    ba.textwidget(
                        edit=t_accessible_extra,
                        text=ba.Lstr(resource='gatherWindow.'
                                     'manualRouterForwardingText',
                                     subs=[('${PORT}',
                                            str(_ba.get_game_port()))]),
                        color=color_bad,
                    )
