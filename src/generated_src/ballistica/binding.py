# Released under the MIT License. See LICENSE for details.
# Where most of our python-c++ binding happens.
# Python objects should be added here along with their associated c++ enum.
# Run make update to update the project after editing this..
# pylint: disable=missing-module-docstring, missing-function-docstring
# pylint: disable=line-too-long
def get_binding_values() -> object:
    from ba import _hooks
    import _ba
    import json
    import copy
    import ba
    from ba import _lang
    from ba import _music
    from ba import _input
    from ba import _apputils
    from ba import _account
    from ba import _dependency
    from ba import _enums
    from ba import _player
    # FIXME: There should be no bastd in here;
    #  should pull in bases from ba which get overridden by bastd (or other).
    from bastd.ui.onscreenkeyboard import OnScreenKeyboardWindow
    from bastd.ui import party
    return (
        _ba.client_info_query_response,  # kClientInfoQueryResponseCall
        _hooks.reset_to_main_menu,  # kResetToMainMenuCall
        _hooks.set_config_fullscreen_on,  # kSetConfigFullscreenOnCall
        _hooks.set_config_fullscreen_off,  # kSetConfigFullscreenOffCall
        _hooks.not_signed_in_screen_message,  # kNotSignedInScreenMessageCall
        _hooks.connecting_to_party_message,  # kConnectingToPartyMessageCall
        _hooks.rejecting_invite_already_in_party_message,  # kRejectingInviteAlreadyInPartyMessageCall
        _hooks.connection_failed_message,  # kConnectionFailedMessageCall
        _hooks.temporarily_unavailable_message,  # kTemporarilyUnavailableMessageCall
        _hooks.in_progress_message,  # kInProgressMessageCall
        _hooks.error_message,  # kErrorMessageCall
        _hooks.purchase_not_valid_error,  # kPurchaseNotValidErrorCall
        _hooks.purchase_already_in_progress_error,  # kPurchaseAlreadyInProgressErrorCall
        _hooks.gear_vr_controller_warning,  # kGearVRControllerWarningCall
        _hooks.orientation_reset_cb_message,  # kVROrientationResetCBMessageCall
        _hooks.orientation_reset_message,  # kVROrientationResetMessageCall
        _hooks.on_app_resume,  # kHandleAppResumeCall
        _apputils.handle_log,  # kHandleLogCall
        _hooks.launch_main_menu_session,  # kLaunchMainMenuSessionCall
        _hooks.language_test_toggle,  # kLanguageTestToggleCall
        _hooks.award_in_control_achievement,  # kAwardInControlAchievementCall
        _hooks.award_dual_wielding_achievement,  # kAwardDualWieldingAchievementCall
        _apputils.print_corrupt_file_error,  # kPrintCorruptFileErrorCall
        _hooks.play_gong_sound,  # kPlayGongSoundCall
        _hooks.launch_coop_game,  # kLaunchCoopGameCall
        _hooks.purchases_restored_message,  # kPurchasesRestoredMessageCall
        _hooks.dismiss_wii_remotes_window,  # kDismissWiiRemotesWindowCall
        _hooks.unavailable_message,  # kUnavailableMessageCall
        _hooks.submit_analytics_counts,  # kSubmitAnalyticsCountsCall
        _hooks.set_last_ad_network,  # kSetLastAdNetworkCall
        _hooks.no_game_circle_message,  # kNoGameCircleMessageCall
        _hooks.empty_call,  # kEmptyCall
        _hooks.level_icon_press,  # kLevelIconPressCall
        _hooks.trophy_icon_press,  # kTrophyIconPressCall
        _hooks.coin_icon_press,  # kCoinIconPressCall
        _hooks.ticket_icon_press,  # kTicketIconPressCall
        _hooks.back_button_press,  # kBackButtonPressCall
        _hooks.friends_button_press,  # kFriendsButtonPressCall
        _hooks.print_trace,  # kPrintTraceCall
        _hooks.toggle_fullscreen,  # kToggleFullscreenCall
        _hooks.party_icon_activate,  # kPartyIconActivateCall
        _hooks.read_config,  # kReadConfigCall
        _hooks.ui_remote_press,  # kUIRemotePressCall
        _hooks.quit_window,  # kQuitWindowCall
        _hooks.remove_in_game_ads_message,  # kRemoveInGameAdsMessageCall
        _hooks.telnet_access_request,  # kTelnetAccessRequestCall
        _hooks.on_app_pause,  # kOnAppPauseCall
        _hooks.do_quit,  # kQuitCall
        _hooks.shutdown,  # kShutdownCall
        _hooks.gc_disable,  # kGCDisableCall
        _account.show_post_purchase_message,  # kShowPostPurchaseMessageCall
        _hooks.device_menu_press,  # kDeviceMenuPressCall
        _hooks.show_url_window,  # kShowURLWindowCall
        _hooks.party_invite_revoke,  # kHandlePartyInviteRevokeCall
        _hooks.filter_chat_message,  # kFilterChatMessageCall
        _hooks.local_chat_message,  # kHandleLocalChatMessageCall
        ba.ShouldShatterMessage,  # kShouldShatterMessageClass
        ba.ImpactDamageMessage,  # kImpactDamageMessageClass
        ba.PickedUpMessage,  # kPickedUpMessageClass
        ba.DroppedMessage,  # kDroppedMessageClass
        ba.OutOfBoundsMessage,  # kOutOfBoundsMessageClass
        ba.PickUpMessage,  # kPickUpMessageClass
        ba.DropMessage,  # kDropMessageClass
        ba.app.on_app_launch,  # kOnAppLaunchCall
        _input.get_device_value,  # kGetDeviceValueCall
        _input.get_last_player_name_from_input_device,  # kGetLastPlayerNameFromInputDeviceCall
        copy.deepcopy,  # kDeepCopyCall
        copy.copy,  # kShallowCopyCall
        ba.Activity,  # kActivityClass
        ba.Session,  # kSessionClass
        json.dumps,  # kJsonDumpsCall
        json.loads,  # kJsonLoadsCall
        OnScreenKeyboardWindow,  # kOnScreenKeyboardClass
        party.handle_party_invite,  # kHandlePartyInviteCall
        _music.do_play_music,  # kDoPlayMusicCall
        ba.app.handle_deep_link,  # kDeepLinkCall
        _lang.get_resource,  # kGetResourceCall
        _lang.translate,  # kTranslateCall
        ba.Lstr,  # kLStrClass
        ba.Call,  # kCallClass
        _apputils.garbage_collect,  # kGarbageCollectCall
        ba.ContextError,  # kContextError
        ba.NotFoundError,  # kNotFoundError
        ba.NodeNotFoundError,  # kNodeNotFoundError
        ba.SessionTeamNotFoundError,  # kSessionTeamNotFoundError
        ba.InputDeviceNotFoundError,  # kInputDeviceNotFoundError
        ba.DelegateNotFoundError,  # kDelegateNotFoundError
        ba.SessionPlayerNotFoundError,  # kSessionPlayerNotFoundError
        ba.WidgetNotFoundError,  # kWidgetNotFoundError
        ba.ActivityNotFoundError,  # kActivityNotFoundError
        ba.SessionNotFoundError,  # kSessionNotFoundError
        _dependency.AssetPackage,  # kAssetPackageClass
        _enums.TimeFormat,  # kTimeFormatClass
        _enums.TimeType,  # kTimeTypeClass
        _enums.InputType,  # kInputTypeClass
        _enums.Permission,  # kPermissionClass
        _enums.SpecialChar,  # kSpecialCharClass
        _player.Player,  # kPlayerClass
        _hooks.get_player_icon,  # kGetPlayerIconCall
        _lang.Lstr.from_json,  # kLstrFromJsonCall
    )  # yapf: disable
