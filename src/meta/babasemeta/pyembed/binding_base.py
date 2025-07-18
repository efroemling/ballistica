# Released under the MIT License. See LICENSE for details.
# Where most of our python-c++ binding happens.
# Python objects should be added here along with their associated c++ enum.
# pylint: disable=useless-suppression, missing-module-docstring, line-too-long
from __future__ import annotations

from bacommon.app import AppArchitecture, AppPlatform, AppVariant
from babase._mgen import enums

# noinspection PyProtectedMember
from babase import _language, _apputils, _hooks, _env, _error, _general, _ui

# The C++ layer looks for this variable:
values = [
    _hooks.reset_to_main_menu,  # kResetToMainMenuCall
    _hooks.store_config_fullscreen_on,  # kStoreConfigFullscreenOnCall
    _hooks.store_config_fullscreen_off,  # kStoreConfigFullscreenOffCall
    _hooks.set_config_fullscreen_on,  # kSetConfigFullscreenOnCall
    _hooks.set_config_fullscreen_off,  # kSetConfigFullscreenOffCall
    _hooks.not_signed_in_screen_message,  # kNotSignedInScreenMessageCall
    _hooks.rejecting_invite_already_in_party_message,  # kRejectingInviteAlreadyInPartyMessageCall
    _hooks.connection_failed_message,  # kConnectionFailedMessageCall
    _hooks.temporarily_unavailable_message,  # kTemporarilyUnavailableMessageCall
    _hooks.in_progress_message,  # kInProgressMessageCall
    _hooks.error_message,  # kErrorMessageCall
    _hooks.success_message,  # kSuccessMessageCall
    _hooks.purchase_not_valid_error,  # kPurchaseNotValidErrorCall
    _hooks.purchase_already_in_progress_error,  # kPurchaseAlreadyInProgressErrorCall
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
    _hooks.unavailable_message,  # kUnavailableMessageCall
    _hooks.set_last_ad_network,  # kSetLastAdNetworkCall
    _hooks.google_play_purchases_not_available_message,  # kGooglePlayPurchasesNotAvailableMessageCall
    _hooks.google_play_services_not_available_message,  # kGooglePlayServicesNotAvailableMessageCall
    _hooks.empty_call,  # kEmptyCall
    _hooks.print_trace,  # kPrintTraceCall
    _hooks.toggle_fullscreen,  # kToggleFullscreenCall
    _hooks.ui_remote_press,  # kUIRemotePressCall
    _hooks.remove_in_game_ads_message,  # kRemoveInGameAdsMessageCall
    _hooks.do_quit,  # kQuitCall
    _hooks.show_post_purchase_message,  # kShowPostPurchaseMessageCall
    _hooks.string_edit_adapter_can_be_replaced,  # kStringEditAdapterCanBeReplacedCall
    _hooks.get_dev_console_tab_names,  # kGetDevConsoleTabNamesCall
    _hooks.unsupported_controller_message,  # kUnsupportedControllerMessageCall
    _hooks.get_v2_account_id,  # kGetV2AccountIdCall
    _hooks.copy_dev_console_history,  # kCopyDevConsoleHistoryCall
    _language.Lstr,  # kLStrClass
    _general.Call,  # kCallClass
    _error.ContextError,  # kContextError
    _error.NotFoundError,  # kNotFoundError
    _error.NodeNotFoundError,  # kNodeNotFoundError
    _error.SessionTeamNotFoundError,  # kSessionTeamNotFoundError
    _error.InputDeviceNotFoundError,  # kInputDeviceNotFoundError
    _error.DelegateNotFoundError,  # kDelegateNotFoundError
    _error.SessionPlayerNotFoundError,  # kSessionPlayerNotFoundError
    _error.WidgetNotFoundError,  # kWidgetNotFoundError
    _error.ActivityNotFoundError,  # kActivityNotFoundError
    _error.SessionNotFoundError,  # kSessionNotFoundError
    enums.QuitType,  # kQuitTypeClass
    enums.InputType,  # kInputTypeClass
    enums.Permission,  # kPermissionClass
    enums.SpecialChar,  # kSpecialCharClass
    _language.Lstr.from_json,  # kLstrFromJsonCall
    _hooks.hash_strings,  # kHashStringsCall
    _hooks.have_account_v2_credentials,  # kHaveAccountV2CredentialsCall
    _hooks.implicit_sign_in,  # kImplicitSignInCall
    _hooks.implicit_sign_out,  # kImplicitSignOutCall
    _hooks.login_adapter_get_sign_in_token_response,  # kLoginAdapterGetSignInTokenResponseCall
    _hooks.open_url_with_webbrowser_module,  # kOpenURLWithWebBrowserModuleCall
    _env.on_native_module_import,  # kEnvOnNativeModuleImportCall
    _env.on_main_thread_start_app,  # kOnMainThreadStartAppCall
    _ui.DevConsoleStringEditAdapter,  # kDevConsoleStringEditAdapterClass
    AppArchitecture,  # kAppArchitectureType
    AppPlatform,  # kAppPlatformType
    AppVariant,  # kAppVariantType
]
