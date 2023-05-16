// Copyright (c) 2011-2022 Eric Froemling

#if BA_OSTYPE_ANDROID
#include "ballistica/base/platform/android/base_platform_android.h"

#include "ballistica/core/platform/android/android_utils.h"
#include "ballistica/core/platform/android/core_platform_android.h"

namespace ballistica::base {

BasePlatformAndroid::BasePlatformAndroid() {}

void BasePlatformAndroid::LoginAdapterGetSignInToken(
    const std::string& login_type, int attempt_id) {
  core::CorePlatformAndroid::Get(g_core)->PushAndroidCommand3(
      "LOGIN_ADAPTER_GET_SIGN_IN_TOKEN", login_type.c_str(),
      std::to_string(attempt_id).c_str());
}

void BasePlatformAndroid::LoginAdapterBackEndActiveChange(
    const std::string& login_type, bool active) {
  core::CorePlatformAndroid::Get(g_core)->PushAndroidCommand3(
      "LOGIN_ADAPTER_BACK_END_ACTIVE_CHANGE", login_type.c_str(),
      active ? "1" : "0");
}

void BasePlatformAndroid::DoPurchase(const std::string& item) {
  core::CorePlatformAndroid::Get(g_core)->PushAndroidCommand2("PURCHASE",
                                                              item.c_str());
}

void BasePlatformAndroid::PurchaseAck(const std::string& purchase,
                                      const std::string& order_id) {
  core::CorePlatformAndroid::Get(g_core)->PushAndroidCommand3(
      "PURCHASE_ACK", purchase.c_str(), order_id.c_str());
}

void BasePlatformAndroid::DoOpenURL(const std::string& url) {
  JNIEnv* env = core::CorePlatformAndroid::Get(g_core)->GetEnv();
  core::ScopedJNIReferenceFrame refs(env);
  auto context_class{core::CorePlatformAndroid::ContextClass()};
  jmethodID mid{env->GetStaticMethodID(context_class, "fromNativeOpenURL",
                                       "(Ljava/lang/String;)V")};
  assert(mid);
  if (mid) {
    jstring jurl = core::CorePlatformAndroid::NewJString(env, url);
    env->CallStaticVoidMethod(context_class, mid, jurl);
    env->DeleteLocalRef(jurl);
  }
}

}  // namespace ballistica::base

#endif  // BA_OSTYPE_ANDROID
