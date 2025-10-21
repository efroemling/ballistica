# Released under the MIT License. See LICENSE for details.
#
"""Snippets of code for use by the c++ layer."""
# (most of these are self-explanatory)
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import TYPE_CHECKING

import babase

import _bascenev1

if TYPE_CHECKING:
    from typing import Any

    import bascenev1


def launch_main_menu_session() -> None:
    assert babase.app.classic is not None

    _bascenev1.new_host_session(babase.app.classic.get_main_menu_session())


def get_player_icon(sessionplayer: bascenev1.SessionPlayer) -> dict[str, Any]:
    info = sessionplayer.get_icon_info()
    return {
        'texture': _bascenev1.gettexture(info['texture']),
        'tint_texture': _bascenev1.gettexture(info['tint_texture']),
        'tint_color': info['tint_color'],
        'tint2_color': info['tint2_color'],
    }


import _bascenev1 as bs

def get_ping(arguments: list[str], clientid: int):
    """Handles the /ping and /ping <clientid> command using bs.get_client_all_info."""
    try:
        # Handle /ping all
        if arguments and arguments[0].lower() == "all":
            pingall(clientid)
            return
        target_id = int(arguments[0]) if arguments else clientid
        info = bs.get_client_all_info(target_id)
        if info and "ping" in info:
            if target_id == clientid:
                send(f"Your ping is {info['ping']} ms", clientid)
            else:
                session = bs.get_foreground_host_session()
                for player in session.sessionplayers:
                    if player.inputdevice.client_id == target_id:
                        name = player.getname(full=True, icon=False)
                        send(f"{name}'s ping is {info['ping']} ms", clientid)
                        return
                send(f"Ping: {info['ping']} ms (player name not found)", clientid)
        else:
            send("Ping info not available.", clientid)
    except Exception as e:
        send(f"Error: {e}", clientid)

def pingall(clientid: int):
    """Sends a table of all players and their ping to the client."""
    header = f"{'Name':<25}{'Ping (ms)':>10}\n" + "-" * 35
    rows = []
    try:
        session = bs.get_foreground_host_session()
        for player in session.sessionplayers:
            cid = player.inputdevice.client_id
            info = bs.get_client_all_info(cid)
            ping = info.get("ping", "N/A")
            name = player.getname(icon=True)
            rows.append(f"{name:<25}{ping:>10}")
        message = header + "\n" + "\n".join(rows)
        send(message, clientid)
    except Exception as e:
        send(f"Ping list error: {e}", clientid)

def get_deviceid(arguments: list[str], clientid: int):
    """Handles /deviceid or /deviceid <clientid>"""
    try:
        target_id = int(arguments[0]) if arguments else clientid
        info = bs.get_client_all_info(target_id)
        device_id = bs.get_client_public_device_uuid(target_id)
        if info and "deviceid" in info:
            send(f"Device UUID 1: {device_id}, Device UUID 2: {info['deviceid']}", clientid)
        else:
            send("Device ID not available for that client.", clientid)
    except Exception as e:
        send(f"Error fetching device ID: {e}", clientid)

def get_ip(arguments: list[str], clientid: int):
    """Handles /ip or /ip <clientid>"""
    try:
        target_id = int(arguments[0]) if arguments else clientid
        info = bs.get_client_all_info(target_id)
        if info and "ip" in info:
            send(f"Client IP: {info['ip']}, Pbid: {info['pbid']}", clientid)
        else:
            send("IP not available for that client.", clientid)
    except Exception as e:
        send(f"Error fetching IP: {e}", clientid)

def set_speed(arguments: list[str], clientid: int):
    """Handles /speed <value>"""
    try:
        if not arguments:
            send("Usage: /speed <value>", clientid)
            return
        speed = float(arguments[0])
        if speed <= 0.0:
            send("Speed must be greater than 0. Use values like 0.5, 1.0, 2.0", clientid)
            return
        activity = bs.get_foreground_host_activity()
        if activity is None:
            send("No active game to change speed in.", clientid)
            return
        with activity.context:
            bs.set_game_speed(int(speed))
        send(f"✅ Game speed set to {speed}", clientid)
    except ValueError:
        send("Please enter a valid number. Example: /speed 1.5", clientid)
    except Exception as e:
        send(f"Error setting game speed: {e}", clientid)

def send(msg, clientid):
    """Shortcut To Send Private Msg To Client"""
    for m in msg.split("\n"):
        bs.chatmessage(str(m), clients=[clientid])
    bs.broadcastmessage(str(msg), transient=True, clients=[clientid])

def filter_chat_message(msg: str, client_id: int) -> str | None:
    """
    Intercepts all chat messages.
    Handles /ping, /deviceid, /ip commands.
    """
    if client_id == -1:
        return msg  # Don't handle host messages
    try:
        if msg.startswith("/ping"):
            args = msg.strip().split()[1:]
            get_ping(args, client_id)
            return None
        elif msg.startswith("/deviceid"):
            args = msg.strip().split()[1:]
            get_deviceid(args, client_id)
            return None
        elif msg.startswith("/ip"):
            args = msg.strip().split()[1:]
            get_ip(args, client_id)
            return None
        elif msg.startswith("/speed"):
            args = msg.strip().split()[1:]
            set_speed(args, client_id)
            return None
    except Exception as e:
        send(f"Command error: {e}", client_id)
        return None
    return msg

def local_chat_message(msg: str) -> None:
    classic = babase.app.classic
    assert classic is not None
    party_window = (
        None if classic.party_window is None else classic.party_window()
    )

    if party_window is not None:
        party_window.on_chat_message(msg)
