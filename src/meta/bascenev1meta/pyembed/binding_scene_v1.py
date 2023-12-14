# Released under the MIT License. See LICENSE for details.
# Where most of our python-c++ binding happens.
# Python objects should be added here along with their associated c++ enum.
# pylint: disable=useless-suppression, missing-module-docstring, line-too-long
from __future__ import annotations

from bascenev1 import _messages
from bascenev1 import _hooks
from bascenev1._player import Player
from bascenev1._dependency import AssetPackage
from bascenev1._activity import Activity
from bascenev1._session import Session
from bascenev1._net import HostInfo
import _bascenev1

# The C++ layer looks for this variable:
values = [
    _hooks.launch_main_menu_session,  # kLaunchMainMenuSessionCall
    _hooks.get_player_icon,  # kGetPlayerIconCall
    _hooks.filter_chat_message,  # kFilterChatMessageCall
    _hooks.local_chat_message,  # kHandleLocalChatMessageCall
    _bascenev1.client_info_query_response,  # kClientInfoQueryResponseCall
    _messages.ShouldShatterMessage,  # kShouldShatterMessageClass
    _messages.ImpactDamageMessage,  # kImpactDamageMessageClass
    _messages.PickedUpMessage,  # kPickedUpMessageClass
    _messages.DroppedMessage,  # kDroppedMessageClass
    _messages.OutOfBoundsMessage,  # kOutOfBoundsMessageClass
    _messages.PickUpMessage,  # kPickUpMessageClass
    _messages.DropMessage,  # kDropMessageClass
    Player,  # kPlayerClass
    AssetPackage,  # kAssetPackageClass
    Activity,  # kActivityClass
    Session,  # kSceneV1SessionClass
    HostInfo,  # kHostInfoClass
]
