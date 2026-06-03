{
// Python code from babasemeta/pyembed/binding_base.py:
const char* bindcode =
  "# Released under the MIT License. See LICENSE for details.\n"
  "# Where most of our python-c++ binding happens.\n"
  "# Python objects should be added here along with their associated c++ enum.\n"
  "# pylint: disable=useless-suppression, missing-module-docstring, line-too-long\n"
  "from __future__ import annotations\n"
  "\n"
  "from bacommon.app import AppArchitecture, AppPlatform, AppVariant\n"
  "from babase._mgen import enums\n"
  "\n"
  "from babase import _language, _apputils, _hooks, _env, _error, _general, _ui\n"
  "\n"
  "# The C++ layer looks for this variable:\n"
  "values = [\n"
  "    _hooks.reset_to_main_menu,  # kResetToMainMenuCall\n"
  "    _hooks.store_config_fullscreen_on,  # kStoreConfigFullscreenOnCall\n"
  "    _hooks.store_config_fullscreen_off,  # kStoreConfigFullscreenOffCall\n"
  "    _hooks.set_config_fullscreen_on,  # kSetConfigFullscreenOnCall\n"
  "    _hooks.set_config_fullscreen_off,  # kSetConfigFullscreenOffCall\n"
  "    _hooks.not_signed_in_screen_message,  # kNotSignedInScreenMessageCall\n"
  "    _hooks.rejecting_invite_already_in_party_message,  # kRejectingInviteAlreadyInPartyMessageCall\n"
  "    _hooks.connection_failed_message,  # kConnectionFailedMessageCall\n"
  "    _hooks.temporarily_unavailable_message,  # kTemporarilyUnavailableMessageCall\n"
  "    _hooks.in_progress_message,  # kInProgressMessageCall\n"
  "    _hooks.error_message,  # kErrorMessageCall\n"
  "    _hooks.success_message,  # kSuccessMessageCall\n"
  "    _hooks.purchase_not_valid_error,  # kPurchaseNotValidErrorCall\n"
  "    _hooks.purchase_already_in_progress_error,  # kPurchaseAlreadyInProgressErrorCall\n"
  "    _hooks.orientation_reset_cb_message,  # kVROrientationResetCBMessageCall\n"
  "    _hooks.orientation_reset_message,  # kVROrientationResetMessageCall\n"
  "    _apputils.handle_v1_cloud_log,  # kHandleV1CloudLogCall\n"
  "    _hooks.language_test_toggle,  # kLanguageTestToggleCall\n"
  "    _hooks.award_in_control_achievement,  # kAwardInControlAchievementCall\n"
  "    _hooks.award_dual_wielding_achievement,  # kAwardDualWieldingAchievementCall\n"
  "    _apputils.print_corrupt_file_error,  # kPrintCorruptFileErrorCall\n"
  "    _hooks.play_gong_sound,  # kPlayGongSoundCall\n"
  "    _hooks.launch_coop_game,  # kLaunchCoopGameCall\n"
  "    _hooks.purchases_restored_message,  # kPurchasesRestoredMessageCall\n"
  "    _hooks.unavailable_message,  # kUnavailableMessageCall\n"
  "    _hooks.set_last_ad_network,  # kSetLastAdNetworkCall\n"
  "    _hooks.google_play_purchases_not_available_message,  # kGooglePlayPurchasesNotAvailableMessageCall\n"
  "    _hooks.google_play_services_not_available_message,  # kGooglePlayServicesNotAvailableMessageCall\n"
  "    _hooks.empty_call,  # kEmptyCall\n"
  "    _hooks.print_trace,  # kPrintTraceCall\n"
  "    _hooks.toggle_fullscreen,  # kToggleFullscreenCall\n"
  "    _hooks.ui_remote_press,  # kUIRemotePressCall\n"
  "    _hooks.remove_in_game_ads_message,  # kRemoveInGameAdsMessageCall\n"
  "    _hooks.do_quit,  # kQuitCall\n"
  "    _hooks.show_post_purchase_message,  # kShowPostPurchaseMessageCall\n"
  "    _hooks.string_edit_adapter_can_be_replaced,  # kStringEditAdapterCanBeReplacedCall\n"
  "    _hooks.get_dev_console_tab_names,  # kGetDevConsoleTabNamesCall\n"
  "    _hooks.unsupported_controller_message,  # kUnsupportedControllerMessageCall\n"
  "    _hooks.get_v2_account_id,  # kGetV2AccountIdCall\n"
  "    _hooks.copy_dev_console_history,  # kCopyDevConsoleHistoryCall\n"
  "    _language.Lstr,  # kLStrClass\n"
  "    _general.CallPartial,  # kCallPartialClass\n"
  "    _error.ContextError,  # kContextError\n"
  "    _error.NotFoundError,  # kNotFoundError\n"
  "    _error.NodeNotFoundError,  # kNodeNotFoundError\n"
  "    _error.SessionTeamNotFoundError,  # kSessionTeamNotFoundError\n"
  "    _error.InputDeviceNotFoundError,  # kInputDeviceNotFoundError\n"
  "    _error.DelegateNotFoundError,  # kDelegateNotFoundError\n"
  "    _error.SessionPlayerNotFoundError,  # kSessionPlayerNotFoundError\n"
  "    _error.WidgetNotFoundError,  # kWidgetNotFoundError\n"
  "    _error.ActivityNotFoundError,  # kActivityNotFoundError\n"
  "    _error.SessionNotFoundError,  # kSessionNotFoundError\n"
  "    enums.QuitType,  # kQuitTypeClass\n"
  "    enums.InputType,  # kInputTypeClass\n"
  "    enums.Permission,  # kPermissionClass\n"
  "    enums.SpecialChar,  # kSpecialCharClass\n"
  "    _language.Lstr.from_json,  # kLstrFromJsonCall\n"
  "    _hooks.hash_strings,  # kHashStringsCall\n"
  "    _hooks.have_account_v2_credentials,  # kHaveAccountV2CredentialsCall\n"
  "    _hooks.implicit_sign_in,  # kImplicitSignInCall\n"
  "    _hooks.implicit_sign_out,  # kImplicitSignOutCall\n"
  "    _hooks.discord_auth_received,  # kDiscordAuthReceivedCall\n"
  "    _hooks.discord_sign_in_token_response,  # kDiscordSignInTokenResponseCall\n"
  "    _hooks.login_adapter_get_sign_in_token_response,  # kLoginAdapterGetSignInTokenResponseCall\n"
  "    _hooks.open_url_with_webbrowser_module,  # kOpenURLWithWebBrowserModuleCall\n"
  "    _env.on_native_module_import,  # kEnvOnNativeModuleImportCall\n"
  "    _env.on_main_thread_start_app,  # kOnMainThreadStartAppCall\n"
  "    _ui.DevConsoleStringEditAdapter,  # kDevConsoleStringEditAdapterClass\n"
  "    AppArchitecture,  # kAppArchitectureType\n"
  "    AppPlatform,  # kAppPlatformType\n"
  "    AppVariant,  # kAppVariantType\n"
  "    _hooks.v2_auth_request,  # kV2AuthRequestCall\n"
  "    _hooks.v2_auth_data,  # kV2AuthDataCall\n"
  "    _hooks.start_native_repl,  # kStartNativeReplCall\n"
  "]\n";

// Exec the Python code in an empty context.
auto ctx = PythonRef::Stolen(PyDict_New());
bool success = PythonCommand(bindcode, "binding_base.py").Exec(true, *ctx, *ctx);
if (!success) {
  FatalError("Error fetching required Python objects.");
}

// Grab the 'values' list that the binding code created.
auto bindvals = ctx.DictGetItem("values");
if (!bindvals.exists() || !PyList_Check(*bindvals)) {
  FatalError("Error binding required Python objects.");
}

// Pull our various obj_ values from the values list.
objs_.StoreCallable(ObjID::kResetToMainMenuCall, PyList_GET_ITEM(bindvals.get(), 0));
objs_.StoreCallable(ObjID::kStoreConfigFullscreenOnCall, PyList_GET_ITEM(bindvals.get(), 1));
objs_.StoreCallable(ObjID::kStoreConfigFullscreenOffCall, PyList_GET_ITEM(bindvals.get(), 2));
objs_.StoreCallable(ObjID::kSetConfigFullscreenOnCall, PyList_GET_ITEM(bindvals.get(), 3));
objs_.StoreCallable(ObjID::kSetConfigFullscreenOffCall, PyList_GET_ITEM(bindvals.get(), 4));
objs_.StoreCallable(ObjID::kNotSignedInScreenMessageCall, PyList_GET_ITEM(bindvals.get(), 5));
objs_.StoreCallable(ObjID::kRejectingInviteAlreadyInPartyMessageCall, PyList_GET_ITEM(bindvals.get(), 6));
objs_.StoreCallable(ObjID::kConnectionFailedMessageCall, PyList_GET_ITEM(bindvals.get(), 7));
objs_.StoreCallable(ObjID::kTemporarilyUnavailableMessageCall, PyList_GET_ITEM(bindvals.get(), 8));
objs_.StoreCallable(ObjID::kInProgressMessageCall, PyList_GET_ITEM(bindvals.get(), 9));
objs_.StoreCallable(ObjID::kErrorMessageCall, PyList_GET_ITEM(bindvals.get(), 10));
objs_.StoreCallable(ObjID::kSuccessMessageCall, PyList_GET_ITEM(bindvals.get(), 11));
objs_.StoreCallable(ObjID::kPurchaseNotValidErrorCall, PyList_GET_ITEM(bindvals.get(), 12));
objs_.StoreCallable(ObjID::kPurchaseAlreadyInProgressErrorCall, PyList_GET_ITEM(bindvals.get(), 13));
objs_.StoreCallable(ObjID::kVROrientationResetCBMessageCall, PyList_GET_ITEM(bindvals.get(), 14));
objs_.StoreCallable(ObjID::kVROrientationResetMessageCall, PyList_GET_ITEM(bindvals.get(), 15));
objs_.StoreCallable(ObjID::kHandleV1CloudLogCall, PyList_GET_ITEM(bindvals.get(), 16));
objs_.StoreCallable(ObjID::kLanguageTestToggleCall, PyList_GET_ITEM(bindvals.get(), 17));
objs_.StoreCallable(ObjID::kAwardInControlAchievementCall, PyList_GET_ITEM(bindvals.get(), 18));
objs_.StoreCallable(ObjID::kAwardDualWieldingAchievementCall, PyList_GET_ITEM(bindvals.get(), 19));
objs_.StoreCallable(ObjID::kPrintCorruptFileErrorCall, PyList_GET_ITEM(bindvals.get(), 20));
objs_.StoreCallable(ObjID::kPlayGongSoundCall, PyList_GET_ITEM(bindvals.get(), 21));
objs_.StoreCallable(ObjID::kLaunchCoopGameCall, PyList_GET_ITEM(bindvals.get(), 22));
objs_.StoreCallable(ObjID::kPurchasesRestoredMessageCall, PyList_GET_ITEM(bindvals.get(), 23));
objs_.StoreCallable(ObjID::kUnavailableMessageCall, PyList_GET_ITEM(bindvals.get(), 24));
objs_.StoreCallable(ObjID::kSetLastAdNetworkCall, PyList_GET_ITEM(bindvals.get(), 25));
objs_.StoreCallable(ObjID::kGooglePlayPurchasesNotAvailableMessageCall, PyList_GET_ITEM(bindvals.get(), 26));
objs_.StoreCallable(ObjID::kGooglePlayServicesNotAvailableMessageCall, PyList_GET_ITEM(bindvals.get(), 27));
objs_.StoreCallable(ObjID::kEmptyCall, PyList_GET_ITEM(bindvals.get(), 28));
objs_.StoreCallable(ObjID::kPrintTraceCall, PyList_GET_ITEM(bindvals.get(), 29));
objs_.StoreCallable(ObjID::kToggleFullscreenCall, PyList_GET_ITEM(bindvals.get(), 30));
objs_.StoreCallable(ObjID::kUIRemotePressCall, PyList_GET_ITEM(bindvals.get(), 31));
objs_.StoreCallable(ObjID::kRemoveInGameAdsMessageCall, PyList_GET_ITEM(bindvals.get(), 32));
objs_.StoreCallable(ObjID::kQuitCall, PyList_GET_ITEM(bindvals.get(), 33));
objs_.StoreCallable(ObjID::kShowPostPurchaseMessageCall, PyList_GET_ITEM(bindvals.get(), 34));
objs_.StoreCallable(ObjID::kStringEditAdapterCanBeReplacedCall, PyList_GET_ITEM(bindvals.get(), 35));
objs_.StoreCallable(ObjID::kGetDevConsoleTabNamesCall, PyList_GET_ITEM(bindvals.get(), 36));
objs_.StoreCallable(ObjID::kUnsupportedControllerMessageCall, PyList_GET_ITEM(bindvals.get(), 37));
objs_.StoreCallable(ObjID::kGetV2AccountIdCall, PyList_GET_ITEM(bindvals.get(), 38));
objs_.StoreCallable(ObjID::kCopyDevConsoleHistoryCall, PyList_GET_ITEM(bindvals.get(), 39));
objs_.StoreCallable(ObjID::kLStrClass, PyList_GET_ITEM(bindvals.get(), 40));
objs_.StoreCallable(ObjID::kCallPartialClass, PyList_GET_ITEM(bindvals.get(), 41));
objs_.Store(ObjID::kContextError, PyList_GET_ITEM(bindvals.get(), 42));
objs_.Store(ObjID::kNotFoundError, PyList_GET_ITEM(bindvals.get(), 43));
objs_.Store(ObjID::kNodeNotFoundError, PyList_GET_ITEM(bindvals.get(), 44));
objs_.Store(ObjID::kSessionTeamNotFoundError, PyList_GET_ITEM(bindvals.get(), 45));
objs_.Store(ObjID::kInputDeviceNotFoundError, PyList_GET_ITEM(bindvals.get(), 46));
objs_.Store(ObjID::kDelegateNotFoundError, PyList_GET_ITEM(bindvals.get(), 47));
objs_.Store(ObjID::kSessionPlayerNotFoundError, PyList_GET_ITEM(bindvals.get(), 48));
objs_.Store(ObjID::kWidgetNotFoundError, PyList_GET_ITEM(bindvals.get(), 49));
objs_.Store(ObjID::kActivityNotFoundError, PyList_GET_ITEM(bindvals.get(), 50));
objs_.Store(ObjID::kSessionNotFoundError, PyList_GET_ITEM(bindvals.get(), 51));
objs_.StoreCallable(ObjID::kQuitTypeClass, PyList_GET_ITEM(bindvals.get(), 52));
objs_.StoreCallable(ObjID::kInputTypeClass, PyList_GET_ITEM(bindvals.get(), 53));
objs_.StoreCallable(ObjID::kPermissionClass, PyList_GET_ITEM(bindvals.get(), 54));
objs_.StoreCallable(ObjID::kSpecialCharClass, PyList_GET_ITEM(bindvals.get(), 55));
objs_.StoreCallable(ObjID::kLstrFromJsonCall, PyList_GET_ITEM(bindvals.get(), 56));
objs_.StoreCallable(ObjID::kHashStringsCall, PyList_GET_ITEM(bindvals.get(), 57));
objs_.StoreCallable(ObjID::kHaveAccountV2CredentialsCall, PyList_GET_ITEM(bindvals.get(), 58));
objs_.StoreCallable(ObjID::kImplicitSignInCall, PyList_GET_ITEM(bindvals.get(), 59));
objs_.StoreCallable(ObjID::kImplicitSignOutCall, PyList_GET_ITEM(bindvals.get(), 60));
objs_.StoreCallable(ObjID::kDiscordAuthReceivedCall, PyList_GET_ITEM(bindvals.get(), 61));
objs_.StoreCallable(ObjID::kDiscordSignInTokenResponseCall, PyList_GET_ITEM(bindvals.get(), 62));
objs_.StoreCallable(ObjID::kLoginAdapterGetSignInTokenResponseCall, PyList_GET_ITEM(bindvals.get(), 63));
objs_.StoreCallable(ObjID::kOpenURLWithWebBrowserModuleCall, PyList_GET_ITEM(bindvals.get(), 64));
objs_.StoreCallable(ObjID::kEnvOnNativeModuleImportCall, PyList_GET_ITEM(bindvals.get(), 65));
objs_.StoreCallable(ObjID::kOnMainThreadStartAppCall, PyList_GET_ITEM(bindvals.get(), 66));
objs_.StoreCallable(ObjID::kDevConsoleStringEditAdapterClass, PyList_GET_ITEM(bindvals.get(), 67));
objs_.Store(ObjID::kAppArchitectureType, PyList_GET_ITEM(bindvals.get(), 68));
objs_.Store(ObjID::kAppPlatformType, PyList_GET_ITEM(bindvals.get(), 69));
objs_.Store(ObjID::kAppVariantType, PyList_GET_ITEM(bindvals.get(), 70));
objs_.StoreCallable(ObjID::kV2AuthRequestCall, PyList_GET_ITEM(bindvals.get(), 71));
objs_.StoreCallable(ObjID::kV2AuthDataCall, PyList_GET_ITEM(bindvals.get(), 72));
objs_.StoreCallable(ObjID::kStartNativeReplCall, PyList_GET_ITEM(bindvals.get(), 73));
}
