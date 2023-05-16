# Released under the MIT License. See LICENSE for details.
# Where most of our python-c++ binding happens.
# Python objects should be added here along with their associated c++ enum.
# Run make update to update the project after editing this..
# pylint: disable=missing-module-docstring, line-too-long
from __future__ import annotations

import babase
from babase import _language
from babase import _apputils
from babase._mgen import enums
from babase import _hooks

# The C++ layer looks for this variable:
values = [
    babase.app,  # kApp
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
    _apputils.handle_v1_cloud_log,  # kHandleV1CloudLogCall
    _hooks.language_test_toggle,  # kLanguageTestToggleCall
    _hooks.award_in_control_achievement,  # kAwardInControlAchievementCall
    _hooks.award_dual_wielding_achievement,  # kAwardDualWieldingAchievementCall
    _apputils.print_corrupt_file_error,  # kPrintCorruptFileErrorCall
    _hooks.play_gong_sound,  # kPlayGongSoundCall
    _hooks.launch_coop_game,  # kLaunchCoopGameCall
    _hooks.purchases_restored_message,  # kPurchasesRestoredMessageCall
    _hooks.dismiss_wii_remotes_window,  # kDismissWiiRemotesWindowCall
    _hooks.unavailable_message,  # kUnavailableMessageCall
    _hooks.set_last_ad_network,  # kSetLastAdNetworkCall
    _hooks.no_game_circle_message,  # kNoGameCircleMessageCall
    _hooks.google_play_purchases_not_available_message,  # kGooglePlayPurchasesNotAvailableMessageCall
    _hooks.google_play_services_not_available_message,  # kGooglePlayServicesNotAvailableMessageCall
    _hooks.empty_call,  # kEmptyCall
    _hooks.print_trace,  # kPrintTraceCall
    _hooks.toggle_fullscreen,  # kToggleFullscreenCall
    _hooks.read_config,  # kReadConfigCall
    _hooks.ui_remote_press,  # kUIRemotePressCall
    _hooks.remove_in_game_ads_message,  # kRemoveInGameAdsMessageCall
    _hooks.on_app_pause,  # kOnAppPauseCall
    _hooks.on_app_resume,  # kOnAppResumeCall
    _hooks.do_quit,  # kQuitCall
    _hooks.shutdown,  # kShutdownCall
    _hooks.show_post_purchase_message,  # kShowPostPurchaseMessageCall
    _hooks.on_app_bootstrapping_complete,  # kOnAppBootstrappingCompleteCall
    babase.app.handle_deep_link,  # kDeepLinkCall
    babase.app.lang.get_resource,  # kGetResourceCall
    babase.app.lang.translate,  # kTranslateCall
    babase.Lstr,  # kLStrClass
    babase.Call,  # kCallClass
    _apputils.garbage_collect_session_end,  # kGarbageCollectSessionEndCall
    babase.ContextError,  # kContextError
    babase.NotFoundError,  # kNotFoundError
    babase.NodeNotFoundError,  # kNodeNotFoundError
    babase.SessionTeamNotFoundError,  # kSessionTeamNotFoundError
    babase.InputDeviceNotFoundError,  # kInputDeviceNotFoundError
    babase.DelegateNotFoundError,  # kDelegateNotFoundError
    babase.SessionPlayerNotFoundError,  # kSessionPlayerNotFoundError
    babase.WidgetNotFoundError,  # kWidgetNotFoundError
    babase.ActivityNotFoundError,  # kActivityNotFoundError
    babase.SessionNotFoundError,  # kSessionNotFoundError
    enums.TimeFormat,  # kTimeFormatClass
    enums.TimeType,  # kTimeTypeClass
    enums.InputType,  # kInputTypeClass
    enums.Permission,  # kPermissionClass
    enums.SpecialChar,  # kSpecialCharClass
    _language.Lstr.from_json,  # kLstrFromJsonCall
    _hooks.uuid_str,  # kUUIDStrCall
    _hooks.hash_strings,  # kHashStringsCall
    _hooks.have_account_v2_credentials,  # kHaveAccountV2CredentialsCall
    _hooks.implicit_sign_in,  # kImplicitSignInCall
    _hooks.implicit_sign_out,  # kImplicitSignOutCall
    _hooks.login_adapter_get_sign_in_token_response,  # kLoginAdapterGetSignInTokenResponseCall
    _hooks.open_url_with_webbrowser_module,  # kOpenURLWithWebBrowserModuleCall
    _apputils.on_too_many_file_descriptors,  # kOnTooManyFileDescriptorsCall
]
