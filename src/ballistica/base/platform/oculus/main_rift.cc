// Copyright (c) 2011-2022 Eric Froemling
// Derived from code licensed as follows:

/*****************************************************************************

Filename    :   main.cpp
Content     :   Simple minimal VR demo
Created     :   December 1, 2014
Author      :   Tom Heath
Copyright   :   Copyright 2012 Oculus, Inc. All Rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

*****************************************************************************/
/// This sample has not yet been fully assimilated into the framework
/// and also the GL support is not quite fully there yet, hence the VR
/// is not that great!

#if BA_RIFT_BUILD

// #include "..OculusRoomTiny_Advanced/Common/Win32_GLAppUtil.h"
#include "external/oculus/OculusSDK/Samples/OculusRoomTiny_Advanced/Common/Win32_GLAppUtil.h"

// Include the Oculus SDK
#include "OVR_CAPI_Audio.h"
#include "OVR_CAPI_GL.h"

#if defined(_WIN32)
#include <dxgi.h>  // for GetDefaultAdapterLuid
#pragma comment(lib, "dxgi.lib")
#endif

#include <mmdeviceapi.h>

#include <algorithm>

#include "Functiondiscoverykeys_devpkey.h"
#include "ballistica/base/app/app_vr.h"
#include "ballistica/base/input/device/joystick_input.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/core/core.h"
#include "ballistica/core/platform/oculus/oculus_utils.h"
#include "ballistica/core/platform/support/min_sdl.h"
#include "ballistica/core/support/core_config.h"
#include "ballistica/shared/ballistica.h"

// Keeping this around just to see what we changed.
#define OLD_STUFF 0

#define OUR_GLOBALS_NAMESPACE ballistica::base

using namespace OVR;

struct OculusTextureBuffer {
  ovrSession Session;
  ovrTextureSwapChain ColorTextureChain;
  ovrTextureSwapChain DepthTextureChain;
  GLuint fboId;
  Sizei texSize;

  OculusTextureBuffer(ovrSession session, Sizei size, int sampleCount)
      : Session(session),
        ColorTextureChain(nullptr),
        DepthTextureChain(nullptr),
        fboId(0),
        texSize(0, 0) {
    assert(sampleCount
           <= 1);  // The code doesn't currently handle MSAA textures.

    texSize = size;

    // This texture isn't necessarily going to be a rendertarget, but it usually
    // is.
    assert(session);  // No HMD? A little odd.

    ovrTextureSwapChainDesc desc = {};
    desc.Type = ovrTexture_2D;
    desc.ArraySize = 1;
    desc.Width = size.w;
    desc.Height = size.h;
    desc.MipLevels = 1;
    desc.Format = OVR_FORMAT_R8G8B8A8_UNORM_SRGB;
    desc.SampleCount = sampleCount;
    desc.StaticImage = ovrFalse;

    {
      ovrResult result =
          ovr_CreateTextureSwapChainGL(Session, &desc, &ColorTextureChain);

      int length = 0;
      ovr_GetTextureSwapChainLength(session, ColorTextureChain, &length);

      if (OVR_SUCCESS(result)) {
        for (int i = 0; i < length; ++i) {
          GLuint chainTexId;
          ovr_GetTextureSwapChainBufferGL(Session, ColorTextureChain, i,
                                          &chainTexId);
          glBindTexture(GL_TEXTURE_2D, chainTexId);

          glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
          glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
          glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
          glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        }
      }
    }

    desc.Format = OVR_FORMAT_D32_FLOAT;

    {
      ovrResult result =
          ovr_CreateTextureSwapChainGL(Session, &desc, &DepthTextureChain);

      int length = 0;
      ovr_GetTextureSwapChainLength(session, DepthTextureChain, &length);

      if (OVR_SUCCESS(result)) {
        for (int i = 0; i < length; ++i) {
          GLuint chainTexId;
          ovr_GetTextureSwapChainBufferGL(Session, DepthTextureChain, i,
                                          &chainTexId);
          glBindTexture(GL_TEXTURE_2D, chainTexId);

          glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
          glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
          glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
          glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        }
      }
    }

    glGenFramebuffers(1, &fboId);
  }

  ~OculusTextureBuffer() {
    if (ColorTextureChain) {
      ovr_DestroyTextureSwapChain(Session, ColorTextureChain);
      ColorTextureChain = nullptr;
    }
    if (DepthTextureChain) {
      ovr_DestroyTextureSwapChain(Session, DepthTextureChain);
      DepthTextureChain = nullptr;
    }
    if (fboId) {
      glDeleteFramebuffers(1, &fboId);
      fboId = 0;
    }
  }

  Sizei GetSize() const { return texSize; }

  void SetAndClearRenderSurface() {
    GLuint curColorTexId;
    GLuint curDepthTexId;
    {
      int curIndex;
      ovr_GetTextureSwapChainCurrentIndex(Session, ColorTextureChain,
                                          &curIndex);
      ovr_GetTextureSwapChainBufferGL(Session, ColorTextureChain, curIndex,
                                      &curColorTexId);
    }
    {
      int curIndex;
      ovr_GetTextureSwapChainCurrentIndex(Session, DepthTextureChain,
                                          &curIndex);
      ovr_GetTextureSwapChainBufferGL(Session, DepthTextureChain, curIndex,
                                      &curDepthTexId);
    }

    glBindFramebuffer(GL_FRAMEBUFFER, fboId);
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D,
                           curColorTexId, 0);
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D,
                           curDepthTexId, 0);

    glViewport(0, 0, texSize.w, texSize.h);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    glEnable(GL_FRAMEBUFFER_SRGB);
  }

  void UnsetRenderSurface() {
    glBindFramebuffer(GL_FRAMEBUFFER, fboId);
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D,
                           0, 0);
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D,
                           0, 0);
  }

  void Commit() {
    ovr_CommitTextureSwapChain(Session, ColorTextureChain);
    ovr_CommitTextureSwapChain(Session, DepthTextureChain);
  }
};

static ovrGraphicsLuid GetDefaultAdapterLuid() {
  ovrGraphicsLuid luid = ovrGraphicsLuid();

#if defined(_WIN32)
  IDXGIFactory* factory = nullptr;

  if (SUCCEEDED(CreateDXGIFactory(IID_PPV_ARGS(&factory)))) {
    IDXGIAdapter* adapter = nullptr;

    if (SUCCEEDED(factory->EnumAdapters(0, &adapter))) {
      DXGI_ADAPTER_DESC desc;

      adapter->GetDesc(&desc);
      memcpy(&luid, &desc.AdapterLuid, sizeof(luid));
      adapter->Release();
    }

    factory->Release();
  }
#endif

  return luid;
}

static int Compare(const ovrGraphicsLuid& lhs, const ovrGraphicsLuid& rhs) {
  return memcmp(&lhs, &rhs, sizeof(ovrGraphicsLuid));
}

static bool inited_ballistica = false;

namespace ballistica::base {
std::string g_rift_audio_device_name;
}

// From windows sample code: scans through audio output devices to find
// one with a certain guid and returns its name.
// (OpenAL lets us pick devices by name so that's what we're after)
#define EXIT_ON_ERROR(hres) \
  if (FAILED(hres)) {       \
    goto Exit;              \
  }
#define SAFE_RELEASE(punk) \
  if ((punk) != NULL) {    \
    (punk)->Release();     \
    (punk) = NULL;         \
  }

const CLSID CLSID_MMDeviceEnumerator = __uuidof(MMDeviceEnumerator);
const IID IID_IMMDeviceEnumerator = __uuidof(IMMDeviceEnumerator);

std::string GetAudioDeviceNameFromGUID(WCHAR* guid) {
  std::string val;
  HRESULT hr = S_OK;
  IMMDeviceEnumerator* pEnumerator = NULL;
  IMMDeviceCollection* pCollection = NULL;
  IMMDevice* pEndpoint = NULL;
  IPropertyStore* pProps = NULL;
  LPWSTR pwszID = NULL;

  hr = CoCreateInstance(CLSID_MMDeviceEnumerator, NULL, CLSCTX_ALL,
                        IID_IMMDeviceEnumerator, (void**)&pEnumerator);
  EXIT_ON_ERROR(hr);

  hr = pEnumerator->EnumAudioEndpoints(eRender, DEVICE_STATE_ACTIVE,
                                       &pCollection);
  EXIT_ON_ERROR(hr);

  UINT count;
  hr = pCollection->GetCount(&count);
  EXIT_ON_ERROR(hr);

  // Each loop prints the name of an endpoint device.
  for (ULONG i = 0; i < count; i++) {
    // Get pointer to endpoint number i.
    hr = pCollection->Item(i, &pEndpoint);
    EXIT_ON_ERROR(hr);

    // Get the endpoint ID string.
    hr = pEndpoint->GetId(&pwszID);
    EXIT_ON_ERROR(hr);

    hr = pEndpoint->OpenPropertyStore(STGM_READ, &pProps);
    EXIT_ON_ERROR(hr);

    PROPVARIANT varName;

    // Initialize container for property value.
    PropVariantInit(&varName);

    // Get the endpoint's friendly-name property.
    hr = pProps->GetValue(PKEY_Device_FriendlyName, &varName);
    EXIT_ON_ERROR(hr);

    // Print endpoint friendly name and endpoint ID.
    // printf("Endpoint %d: \"%S\" (%S)\n",
    // i, varName.pwszVal, pwszID);

    // Ff we find the one we're looking for, return its name.
    if (!wcscmp(guid, pwszID)) {
      std::wstring ws = varName.pwszVal;
      val.assign(ws.begin(), ws.end());
    }
    CoTaskMemFree(pwszID);
    pwszID = NULL;
    PropVariantClear(&varName);
    SAFE_RELEASE(pProps);
    SAFE_RELEASE(pEndpoint);
  }
  SAFE_RELEASE(pEnumerator);
  SAFE_RELEASE(pCollection);
  return val;

Exit:
  ballistica::Log(ballistica::LogLevel::kError,
                  "Error enumerating audio devices.");
  CoTaskMemFree(pwszID);
  SAFE_RELEASE(pEnumerator);
  SAFE_RELEASE(pCollection);
  SAFE_RELEASE(pEndpoint);
  SAFE_RELEASE(pProps);
  return val;
}

// Return true to retry later (e.g. after display lost).
static bool MainLoop(bool retryCreate) {
  OculusTextureBuffer* eyeRenderTexture[2] = {nullptr, nullptr};
  // DepthBuffer* eyeDepthBuffer[2] = {nullptr, nullptr};
  ovrMirrorTexture mirrorTexture = nullptr;
  GLuint mirrorFBO = 0;

#if OLD_STUFF
  Scene* roomScene = nullptr;
#endif

  bool isVisible = true;
  long long frameIndex = 0;

  ovrSession session;
  ovrGraphicsLuid luid;
  ovrResult result = ovr_Create(&session, &luid);
  if (!OVR_SUCCESS(result)) return retryCreate;

  if (Compare(luid,
              GetDefaultAdapterLuid()))  // If luid that the Rift is on is
                                         // not the default adapter LUID...
  {
    VALIDATE(false, "OpenGL supports only the default graphics adapter.");
  }

  ovrHmdDesc hmdDesc = ovr_GetHmdDesc(session);

  // Setup Window and Graphics.
  // Note: the mirror window can be any size, for this sample we use 1/2 the HMD
  // resolution.
  ovrSizei windowSize = {hmdDesc.Resolution.w / 2, hmdDesc.Resolution.h / 2};
  if (!Platform.InitDevice(windowSize.w, windowSize.h,
                           reinterpret_cast<LUID*>(&luid)))
    goto Done;

  // Make eye render buffers.
  for (int eye = 0; eye < 2; ++eye) {
    ovrSizei idealTextureSize = ovr_GetFovTextureSize(
        session, ovrEyeType(eye), hmdDesc.DefaultEyeFov[eye], 1);
    eyeRenderTexture[eye] =
        new OculusTextureBuffer(session, idealTextureSize, 1);
    if (!eyeRenderTexture[eye]->ColorTextureChain
        || !eyeRenderTexture[eye]->DepthTextureChain) {
      if (retryCreate) goto Done;
      VALIDATE(false, "Failed to create texture.");
    }
    // eyeRenderTexture[eye] =
    //     new TextureBuffer(session, true, true, idealTextureSize, 1, NULL, 1);
    // eyeDepthBuffer[eye] = new DepthBuffer(eyeRenderTexture[eye]->GetSize(),
    // 0);
    // if (!eyeRenderTexture[eye]->TextureChain) {
    //   if (retryCreate) goto Done;
    //   VALIDATE(false, "Failed to create texture.");
    // }
  }

  ovrMirrorTextureDesc desc;
  memset(&desc, 0, sizeof(desc));
  desc.Width = windowSize.w;
  desc.Height = windowSize.h;
  desc.Format = OVR_FORMAT_R8G8B8A8_UNORM_SRGB;

  // Create mirror texture and an FBO used to copy mirror texture to back buffer
  result = ovr_CreateMirrorTextureWithOptionsGL(session, &desc, &mirrorTexture);
  if (!OVR_SUCCESS(result)) {
    if (retryCreate) goto Done;
    VALIDATE(false, "Failed to create mirror texture.");
  }
  // Create mirror texture and an FBO used to copy mirror texture to back
  // buffer.
  // result = ovr_CreateMirrorTextureGL(session, &desc, &mirrorTexture);
  // if (!OVR_SUCCESS(result)) {
  //   if (retryCreate) goto Done;
  //   VALIDATE(false, "Failed to create mirror texture.");
  // }

  // Configure the mirror read buffer.
  GLuint texId;
  ovr_GetMirrorTextureBufferGL(session, mirrorTexture, &texId);

  glGenFramebuffers(1, &mirrorFBO);
  glBindFramebuffer(GL_READ_FRAMEBUFFER, mirrorFBO);
  glFramebufferTexture2D(GL_READ_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                         GL_TEXTURE_2D, texId, 0);
  glFramebufferRenderbuffer(GL_READ_FRAMEBUFFER, GL_DEPTH_ATTACHMENT,
                            GL_RENDERBUFFER, 0);
  glBindFramebuffer(GL_READ_FRAMEBUFFER, 0);

  // Turn off vsync to let the compositor do its magic.
  wglSwapIntervalEXT(0);

  // Figure out which audio device is the rift
  // (we'll use this when bringing up the ballistica audio context).
  {
    WCHAR buffer[OVR_AUDIO_MAX_DEVICE_STR_SIZE];
    ovr_GetAudioDeviceOutGuidStr(buffer);
    ballistica::base::g_rift_audio_device_name =
        GetAudioDeviceNameFromGUID(buffer);
  }

  if (!inited_ballistica) {
    // Ok, fire up ballistica in vr mode.
    auto config = ballistica::core::CoreConfig();
    config.vr_mode = true;
    ballistica::MonolithicMain(config);
    assert(OUR_GLOBALS_NAMESPACE::g_core
           && OUR_GLOBALS_NAMESPACE::g_core->vr_mode);
    inited_ballistica = true;
  }

  // Inform ballistica of our draw size.
  ballistica::base::AppVR::get()->VRSetDrawDimensions(
      eyeRenderTexture[0]->GetSize().w, eyeRenderTexture[0]->GetSize().h);

#if OLD_STUFF
  // Make scene - can simplify further if needed
  roomScene = new Scene(false);
#endif

  // FloorLevel will give tracking poses where the floor height is 0
  // ovr_SetTrackingOriginType(session, ovrTrackingOrigin_FloorLevel);
  ovr_SetTrackingOriginType(session, ovrTrackingOrigin_EyeLevel);

  // ericf: it's recommended with eye-level origin we call this when the user is
  // in a comfortable position.. hmm; when should we do that?...
  ovr_RecenterTrackingOrigin(session);

  // Add our custom controller.
  ballistica::base::JoystickInput* joystick =
      ballistica::Object::NewDeferred<ballistica::base::JoystickInput>(
          -1,              // not an sdl joystick
          "Oculus-Input",  // device name
          false,           // dont allow configuring
          false);  // no calibration; oculus api handles dead-zones and whatnot

  // We don't bother retaining this shared pointer; g_input will retain it
  // and it'll be nicely killed when we tell it to remove it from their list.

  joystick->SetStandardExtendedButtons();
  joystick->SetStartButtonActivatesDefaultWidget(
      false);  // xbone controller is more of a 'menu' button
  static bool a_pressed = false;
  static bool b_pressed = false;
  static bool x_pressed = false;
  static bool y_pressed = false;
  static bool menu_pressed = false;
  static bool left_pressed = false;
  static bool right_pressed = false;
  static bool up_pressed = false;
  static bool down_pressed = false;
  static float touch_thumbstick_x = 0.0f;
  static float touch_thumbstick_y = 0.0f;
  static float xbox_thumbstick_x = 0.0f;
  static float xbox_thumbstick_y = 0.0f;
  static bool touch_stickbutton_right_pressed = false;
  static bool touch_stickbutton_left_pressed = false;
  static bool touch_stickbutton_up_pressed = false;
  static bool touch_stickbutton_down_pressed = false;
  static bool xbox_lshoulder_pressed = false;
  static bool xbox_rshoulder_pressed = false;
  static float xbox_trigger_l = 0.0f;
  static float xbox_trigger_r = 0.0f;
  static float touch_trigger_l = 0.0f;
  static float touch_trigger_r = 0.0f;
  static bool back_pressed = false;
  static bool remote_enter_pressed = false;
  static bool touch_controllers_present = false;

  const float touch_stickbutton_threshold = 0.5f;

  assert(OUR_GLOBALS_NAMESPACE::g_base && OUR_GLOBALS_NAMESPACE::g_base->input);
  OUR_GLOBALS_NAMESPACE::g_base->input->PushAddInputDeviceCall(joystick, true);

  // Main loop
  while (Platform.HandleMessages()) {
    ovrInputState input_state_xbox;
    ovrInputState input_state_remote;
    ovrInputState input_state_touch;

    ovrSessionStatus session_status;
    ovr_GetSessionStatus(session, &session_status);

    // If either we can't get controller/remote state or aren't foregrounded,
    // just act as if nothing is pressed.

    if (!OVR_SUCCESS(ovr_GetInputState(session, ovrControllerType_XBox,
                                       &input_state_xbox))
        || !session_status.IsVisible) {
      input_state_xbox.Buttons = 0;
      input_state_xbox.IndexTrigger[0] = 0.0f;
      input_state_xbox.IndexTrigger[1] = 0.0f;
      input_state_xbox.Thumbstick[0].x = 0.0f;
      input_state_xbox.Thumbstick[0].y = 0.0f;
    }
    if (!OVR_SUCCESS(ovr_GetInputState(session, ovrControllerType_Remote,
                                       &input_state_remote))
        || !session_status.IsVisible) {
      input_state_remote.Buttons = 0;
    }
    if (!OVR_SUCCESS(ovr_GetInputState(session, ovrControllerType_Touch,
                                       &input_state_touch))
        || !session_status.IsVisible) {
      touch_controllers_present = false;
      input_state_touch.Buttons = 0;
      input_state_touch.Thumbstick[0].x = 0.0f;
      input_state_touch.Thumbstick[0].y = 0.0f;
      input_state_touch.Thumbstick[1].x = 0.0f;
      input_state_touch.Thumbstick[1].y = 0.0f;
      input_state_touch.IndexTrigger[0] = 0.0f;
      input_state_touch.IndexTrigger[1] = 0.0f;
    } else {
      touch_controllers_present = true;
    }

    // Use the right touch thumbstick as 4 fake button presses.

    // Right.
    if (!touch_stickbutton_right_pressed) {
      if (input_state_touch.Thumbstick[1].x > touch_stickbutton_threshold) {
        touch_stickbutton_right_pressed = true;
      }
    } else {
      if (input_state_touch.Thumbstick[1].x <= touch_stickbutton_threshold) {
        touch_stickbutton_right_pressed = false;
      }
    }

    // Left.
    if (!touch_stickbutton_left_pressed) {
      if (input_state_touch.Thumbstick[1].x < -touch_stickbutton_threshold) {
        touch_stickbutton_left_pressed = true;
      }
    } else {
      if (input_state_touch.Thumbstick[1].x >= -touch_stickbutton_threshold) {
        touch_stickbutton_left_pressed = false;
      }
    }

    // Up.
    if (!touch_stickbutton_up_pressed) {
      if (input_state_touch.Thumbstick[1].y > touch_stickbutton_threshold) {
        touch_stickbutton_up_pressed = true;
      }
    } else {
      if (input_state_touch.Thumbstick[1].y <= touch_stickbutton_threshold) {
        touch_stickbutton_up_pressed = false;
      }
    }

    // Down.
    if (!touch_stickbutton_down_pressed) {
      if (input_state_touch.Thumbstick[1].y < -touch_stickbutton_threshold) {
        touch_stickbutton_down_pressed = true;
      }
    } else {
      if (input_state_touch.Thumbstick[1].y >= -touch_stickbutton_threshold) {
        touch_stickbutton_down_pressed = false;
      }
    }

    {
      // Back button press/release
      if ((input_state_xbox.Buttons & ovrButton_Back)
          || (input_state_remote.Buttons & ovrButton_Back)) {
        if (!back_pressed) {
          back_pressed = true;
          SDL_Event e;
          e.type = SDL_JOYBUTTONDOWN;
          e.jbutton.button = 12;
          OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
        }
      } else if (back_pressed) {
        back_pressed = false;
        SDL_Event e;
        e.type = SDL_JOYBUTTONUP;
        e.jbutton.button = 12;
        OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
      }

      // Jump button (A on xbox, A or right-thumbstick-down on touch).
      if ((input_state_xbox.Buttons & ovrButton_A)
          || (input_state_touch.Buttons & ovrButton_A)
          || touch_stickbutton_down_pressed) {
        if (!a_pressed) {  // press
          a_pressed = true;
          SDL_Event e;
          e.type = SDL_JOYBUTTONDOWN;
          e.jbutton.button = 0;
          OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
        }
      } else if (a_pressed) {
        a_pressed = false;
        SDL_Event e;
        e.type = SDL_JOYBUTTONUP;
        e.jbutton.button = 0;
        OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
      }

      // Bomb button (B on xbox, right-thumbstick-right on touch).
      if ((input_state_xbox.Buttons & ovrButton_B)
          || touch_stickbutton_right_pressed) {
        if (!b_pressed) {  // press
          b_pressed = true;
          SDL_Event e;
          e.type = SDL_JOYBUTTONDOWN;
          e.jbutton.button = 2;
          OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
        }
      } else if (b_pressed) {  // release
        b_pressed = false;
        SDL_Event e;
        e.type = SDL_JOYBUTTONUP;
        e.jbutton.button = 2;
        OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
      }

      // Punch button (X on xbox, B or right-thumbstick-left on touch)).
      if ((input_state_xbox.Buttons & ovrButton_X)
          || (input_state_touch.Buttons & ovrButton_B)
          || touch_stickbutton_left_pressed) {  // press
        if (!x_pressed) {
          x_pressed = true;
          SDL_Event e;
          e.type = SDL_JOYBUTTONDOWN;
          e.jbutton.button = 1;
          OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
        }
      } else if (x_pressed) {  // press
        x_pressed = false;
        SDL_Event e;
        e.type = SDL_JOYBUTTONUP;
        e.jbutton.button = 1;
        OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
      }

      // Pickup button (Y on xbox, right-thumbstick-up on touch).
      if ((input_state_xbox.Buttons & ovrButton_Y)
          || touch_stickbutton_up_pressed) {  // press
        if (!y_pressed) {
          y_pressed = true;
          SDL_Event e;
          e.type = SDL_JOYBUTTONDOWN;
          e.jbutton.button = 3;
          OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
        }
      } else if (y_pressed) {  // release
        y_pressed = false;
        SDL_Event e;
        e.type = SDL_JOYBUTTONUP;
        e.jbutton.button = 3;
        OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
      }

      // Start/menu button down/up.
      if ((input_state_xbox.Buttons & ovrButton_Enter)
          || (input_state_touch.Buttons & ovrButton_Enter)) {  // press
        if (!menu_pressed) {
          menu_pressed = true;
          SDL_Event e;
          e.type = SDL_JOYBUTTONDOWN;
          e.jbutton.button = 5;
          OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
        }
      } else if (menu_pressed) {  // release
        menu_pressed = false;
        SDL_Event e;
        e.type = SDL_JOYBUTTONUP;
        e.jbutton.button = 5;
        OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
      }

      // Remote enter button.
      if (input_state_remote.Buttons & ovrButton_Enter) {
        if (!remote_enter_pressed) {
          remote_enter_pressed = true;
          SDL_Event e;
          e.type = SDL_JOYBUTTONDOWN;
          e.jbutton.button = 13;
          OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
        }
      } else if (remote_enter_pressed) {
        remote_enter_pressed = false;
        SDL_Event e;
        e.type = SDL_JOYBUTTONUP;
        e.jbutton.button = 13;
        OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
      }

      // Dpad left press/release.
      if ((input_state_xbox.Buttons & ovrButton_Left)
          || (input_state_remote.Buttons & ovrButton_Left)) {  // press
        if (!left_pressed) {
          left_pressed = true;
          SDL_Event e;
          e.type = SDL_JOYBUTTONDOWN;
          e.jbutton.button = 22;
          OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
        }
      } else if (left_pressed) {  // release
        left_pressed = false;
        SDL_Event e;
        e.type = SDL_JOYBUTTONUP;
        e.jbutton.button = 22;
        OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
      }

      // Dpad right press/release.
      if ((input_state_xbox.Buttons & ovrButton_Right)
          || (input_state_remote.Buttons & ovrButton_Right)) {  // press
        if (!right_pressed) {
          right_pressed = true;
          SDL_Event e;
          e.type = SDL_JOYBUTTONDOWN;
          e.jbutton.button = 23;
          OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
        }
      } else if (right_pressed) {  // release
        right_pressed = false;
        SDL_Event e;
        e.type = SDL_JOYBUTTONUP;
        e.jbutton.button = 23;
        OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
      }

      // Dpad up press/release.
      if ((input_state_xbox.Buttons & ovrButton_Up)
          || (input_state_remote.Buttons & ovrButton_Up)) {  // press
        if (!up_pressed) {
          up_pressed = true;
          SDL_Event e;
          e.type = SDL_JOYBUTTONDOWN;
          e.jbutton.button = 20;
          OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
        }
      } else if (up_pressed) {  // release
        up_pressed = false;
        SDL_Event e;
        e.type = SDL_JOYBUTTONUP;
        e.jbutton.button = 20;
        OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
      }

      // Dpad down press/release.
      if ((input_state_xbox.Buttons & ovrButton_Down)
          || (input_state_remote.Buttons & ovrButton_Down)) {  // press
        if (!down_pressed) {
          down_pressed = true;
          SDL_Event e;
          e.type = SDL_JOYBUTTONDOWN;
          e.jbutton.button = 21;
          OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
        }
      } else if (down_pressed) {  // release
        down_pressed = false;
        SDL_Event e;
        e.type = SDL_JOYBUTTONUP;
        e.jbutton.button = 21;
        OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
      }

      // Left shoulder press/release.
      if (input_state_xbox.Buttons & ovrButton_LShoulder) {  // press
        if (!xbox_lshoulder_pressed) {
          xbox_lshoulder_pressed = true;
          SDL_Event e;
          e.type = SDL_JOYBUTTONDOWN;
          e.jbutton.button = 30;
          OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
        }
      } else if (xbox_lshoulder_pressed) {  // release
        xbox_lshoulder_pressed = false;
        SDL_Event e;
        e.type = SDL_JOYBUTTONUP;
        e.jbutton.button = 30;
        OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
      }

      // Right shoulder press/release.
      if (input_state_xbox.Buttons & ovrButton_RShoulder) {  // press
        if (!xbox_rshoulder_pressed) {
          xbox_rshoulder_pressed = true;
          SDL_Event e;
          e.type = SDL_JOYBUTTONDOWN;
          e.jbutton.button = 31;
          OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
        }
      } else if (xbox_rshoulder_pressed) {  // release
        xbox_rshoulder_pressed = false;
        SDL_Event e;
        e.type = SDL_JOYBUTTONUP;
        e.jbutton.button = 31;
        OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
      }

      // Xbox left analog trigger.
      if (input_state_xbox.IndexTrigger[0] != xbox_trigger_l) {
        xbox_trigger_l = input_state_xbox.IndexTrigger[0];
        SDL_Event e;
        e.type = SDL_JOYAXISMOTION;
        e.jaxis.axis = 10;
        e.jaxis.value = std::max(
            0, std::min(32767, static_cast<int>(xbox_trigger_l * 32767)));
        OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
      }

      // Xbox right analog trigger.
      if (input_state_xbox.IndexTrigger[1] != xbox_trigger_r) {
        xbox_trigger_r = input_state_xbox.IndexTrigger[1];
        SDL_Event e;
        e.type = SDL_JOYAXISMOTION;
        e.jaxis.axis = 11;
        e.jaxis.value = std::max(
            0, std::min(32767, static_cast<int>(xbox_trigger_r * 32767)));
        OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
      }

      // Touch left analog trigger.
      if (input_state_touch.IndexTrigger[0] != touch_trigger_l) {
        touch_trigger_l = input_state_touch.IndexTrigger[0];
        SDL_Event e;
        e.type = SDL_JOYAXISMOTION;
        e.jaxis.axis = 10;
        e.jaxis.value = std::max(
            0, std::min(32767, static_cast<int>(touch_trigger_l * 32767)));
        OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
      }

      // Touch right analog trigger.
      if (input_state_touch.IndexTrigger[1] != touch_trigger_r) {
        touch_trigger_r = input_state_touch.IndexTrigger[1];
        SDL_Event e;
        e.type = SDL_JOYAXISMOTION;
        e.jaxis.axis = 11;
        e.jaxis.value = std::max(
            0, std::min(32767, static_cast<int>(touch_trigger_r * 32767)));
        OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
      }

      // Xbox thumbstick.
      if (input_state_xbox.Thumbstick->x != xbox_thumbstick_x) {
        xbox_thumbstick_x = input_state_xbox.Thumbstick->x;
        SDL_Event e;
        e.type = SDL_JOYAXISMOTION;
        e.jaxis.axis = 0;
        e.jaxis.value = std::max(
            -32767,
            std::min(32767, static_cast<int>(xbox_thumbstick_x * 32767)));
        OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
      }
      if (input_state_xbox.Thumbstick->y != xbox_thumbstick_y) {
        xbox_thumbstick_y = input_state_xbox.Thumbstick->y;
        SDL_Event e;
        e.type = SDL_JOYAXISMOTION;
        e.jaxis.axis = 1;
        e.jaxis.value = std::max(
            -32767,
            std::min(32767, static_cast<int>(xbox_thumbstick_y * -32767)));
        OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
      }

      // Touch thumbstick.
      if (input_state_touch.Thumbstick->x != touch_thumbstick_x) {
        touch_thumbstick_x = input_state_touch.Thumbstick->x;
        SDL_Event e;
        e.type = SDL_JOYAXISMOTION;
        e.jaxis.axis = 0;
        e.jaxis.value = std::max(
            -32767,
            std::min(32767, static_cast<int>(touch_thumbstick_x * 32767)));
        OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
      }
      if (input_state_touch.Thumbstick->y != touch_thumbstick_y) {
        touch_thumbstick_y = input_state_touch.Thumbstick->y;
        SDL_Event e;
        e.type = SDL_JOYAXISMOTION;
        e.jaxis.axis = 1;
        e.jaxis.value = std::max(
            -32767,
            std::min(32767, static_cast<int>(touch_thumbstick_y * -32767)));
        OUR_GLOBALS_NAMESPACE::g_base->input->PushJoystickEvent(e, joystick);
      }
    }

#if OLD_STUFF
    // Keyboard inputs to adjust player orientation
    static float Yaw(3.141592f);
    if (Platform.Key[VK_LEFT]) Yaw += 0.02f;
    if (Platform.Key[VK_RIGHT]) Yaw -= 0.02f;

    // Keyboard inputs to adjust player position
    static Vector3f Pos2(0.0f, 0.0f, -5.0f);
    if (Platform.Key['W'] || Platform.Key[VK_UP])
      Pos2 += Matrix4f::RotationY(Yaw).Transform(Vector3f(0, 0, -0.05f));
    if (Platform.Key['S'] || Platform.Key[VK_DOWN])
      Pos2 += Matrix4f::RotationY(Yaw).Transform(Vector3f(0, 0, +0.05f));
    if (Platform.Key['D'])
      Pos2 += Matrix4f::RotationY(Yaw).Transform(Vector3f(+0.05f, 0, 0));
    if (Platform.Key['A'])
      Pos2 += Matrix4f::RotationY(Yaw).Transform(Vector3f(-0.05f, 0, 0));

    // Animate the cube
    static float cubeClock = 0;
    roomScene->Models[0]->Pos = Vector3f(9 * (float)sinf(cubeClock), 3,
                                         9 * (float)cosf(cubeClock += 0.015f));

#endif  // OLD_STUFF

    // Call ovr_GetRenderDesc each frame to get the ovrEyeRenderDesc, as the
    // returned values (e.g. HmdToEyeOffset) may change at runtime.
    ovrEyeRenderDesc eyeRenderDesc[2];
    eyeRenderDesc[0] =
        ovr_GetRenderDesc(session, ovrEye_Left, hmdDesc.DefaultEyeFov[0]);
    eyeRenderDesc[1] =
        ovr_GetRenderDesc(session, ovrEye_Right, hmdDesc.DefaultEyeFov[1]);

    // Get eye poses, feeding in correct IPD offset
    ovrPosef EyeRenderPose[2];
    ovrPosef HmdToEyePose[2] = {eyeRenderDesc[0].HmdToEyePose,
                                eyeRenderDesc[1].HmdToEyePose};

    double sensorSampleTime;  // sensorSampleTime is fed into the layer later
    ovr_GetEyePoses(session, frameIndex, ovrTrue, HmdToEyePose, EyeRenderPose,
                    &sensorSampleTime);

    ovrTimewarpProjectionDesc posTimewarpProjectionDesc = {};

    if (isVisible) {
      double HmdFrameTiming = ovr_GetPredictedDisplayTime(session, frameIndex);
      ovrTrackingState trackState =
          ovr_GetTrackingState(session, HmdFrameTiming, ovrFalse);

      Matrix4f m = Matrix4f(trackState.HeadPose.ThePose.Orientation);
      float hRoll, hPitch, hYaw;
      m.ToEulerAngles<Axis_Y, Axis_X, Axis_Z, Rotate_CCW, Handed_R>(
          &hYaw, &hPitch, &hRoll);
      ballistica::base::AppVR::get()->VRSetHead(
          trackState.HeadPose.ThePose.Position.x,
          trackState.HeadPose.ThePose.Position.y,
          trackState.HeadPose.ThePose.Position.z, hYaw, hPitch, hRoll);

      // if it looks like we've got touch controllers, send their latest poses
      // and states to the game for drawing/etc
      if (touch_controllers_present) {
        // ew; should just be passing all this stuff in as matrices; for
        // whatever reason it was simpler to set up as euler angles though..
        Matrix4f m =
            Matrix4f(trackState.HandPoses[ovrHand_Right].ThePose.Orientation);
        float rRoll, rPitch, rYaw;
        m.ToEulerAngles<Axis_Y, Axis_X, Axis_Z, Rotate_CCW, Handed_R>(
            &rYaw, &rPitch, &rRoll);
        m = Matrix4f(trackState.HandPoses[ovrHand_Left].ThePose.Orientation);
        float lRoll, lPitch, lYaw;
        m.ToEulerAngles<Axis_Y, Axis_X, Axis_Z, Rotate_CCW, Handed_R>(
            &lYaw, &lPitch, &lRoll);

        ballistica::base::VRHandsState s;
        s.l.type = ballistica::base::VRHandType::kOculusTouchL;
        s.l.tx = trackState.HandPoses[ovrHand_Left].ThePose.Position.x;
        s.l.ty = trackState.HandPoses[ovrHand_Left].ThePose.Position.y;
        s.l.tz = trackState.HandPoses[ovrHand_Left].ThePose.Position.z;
        s.l.yaw = lYaw;
        s.l.pitch = lPitch;
        s.l.roll = lRoll;

        s.r.type = ballistica::base::VRHandType::kOculusTouchR;
        s.r.tx = trackState.HandPoses[ovrHand_Right].ThePose.Position.x;
        s.r.ty = trackState.HandPoses[ovrHand_Right].ThePose.Position.y;
        s.r.tz = trackState.HandPoses[ovrHand_Right].ThePose.Position.z;
        s.r.yaw = rYaw;
        s.r.pitch = rPitch;
        s.r.roll = rRoll;

        ballistica::base::AppVR::get()->VRSetHands(s);

      } else {
        ballistica::base::VRHandsState s;
        ballistica::base::AppVR::get()->VRSetHands(s);
      }

      ballistica::base::AppVR::get()->VRPreDraw();
      for (int eye = 0; eye < 2; ++eye) {
        // Switch to eye render target
        eyeRenderTexture[eye]->SetAndClearRenderSurface();
        // eyeRenderTexture[eye]->SetAndClearRenderSurface(eyeDepthBuffer[eye]);

        if (eye == 0 || eye == 1) {
          Matrix4f m = Matrix4f(EyeRenderPose[eye].Orientation);
          float roll, pitch, yaw;
          m.ToEulerAngles<Axis_Y, Axis_X, Axis_Z, Rotate_CCW, Handed_R>(
              &yaw, &pitch, &roll);
          auto& fov(hmdDesc.DefaultEyeFov[eye]);
          auto& pos(EyeRenderPose[eye].Position);
          ballistica::base::AppVR::get()->VRDrawEye(
              eye, yaw, pitch, roll, fov.LeftTan, fov.RightTan, fov.DownTan,
              fov.UpTan, pos.x, pos.y, pos.z, 0, 0);
        }
#if OLD_STUFF
        else {
          // Get view and projection matrices
          Matrix4f rollPitchYaw = Matrix4f::RotationY(Yaw);
          Matrix4f finalRollPitchYaw =
              rollPitchYaw * Matrix4f(EyeRenderPose[eye].Orientation);
          Vector3f finalUp = finalRollPitchYaw.Transform(Vector3f(0, 1, 0));
          Vector3f finalForward =
              finalRollPitchYaw.Transform(Vector3f(0, 0, -1));
          Vector3f shiftedEyePos =
              Pos2 + rollPitchYaw.Transform(EyeRenderPose[eye].Position);

          Matrix4f view = Matrix4f::LookAtRH(
              shiftedEyePos, shiftedEyePos + finalForward, finalUp);
          Matrix4f proj = ovrMatrix4f_Projection(
              hmdDesc.DefaultEyeFov[eye], 0.2f, 1000.0f, ovrProjection_None);

          // Render world
          roomScene->Render(view, proj);
        }
#endif  // OLD_STUFF

        Matrix4f proj = ovrMatrix4f_Projection(hmdDesc.DefaultEyeFov[eye], 0.2f,
                                               1000.0f, ovrProjection_None);
        posTimewarpProjectionDesc =
            ovrTimewarpProjectionDesc_FromProjection(proj, ovrProjection_None);

        // Avoids an error when calling SetAndClearRenderSurface during next
        // iteration. Without this, during the next while loop iteration
        // SetAndClearRenderSurface would bind a framebuffer with an invalid
        // COLOR_ATTACHMENT0 because the texture ID associated with
        // COLOR_ATTACHMENT0 had been unlocked by calling wglDXUnlockObjectsNV.
        eyeRenderTexture[eye]->UnsetRenderSurface();

        // Commit changes to the textures so they get picked up frame
        eyeRenderTexture[eye]->Commit();
      }
      ballistica::base::AppVR::get()->VRPostDraw();
    } else {
      // If we're not visible we still wanna let our app process events and
      // whatnot.
      OUR_GLOBALS_NAMESPACE::g_base->app->RunRenderUpkeepCycle();
    }

    // Do distortion rendering, Present and flush/sync

    ovrLayerEyeFovDepth ld;
    ld.Header.Type = ovrLayerType_EyeFovDepth;
    ld.Header.Flags =
        ovrLayerFlag_TextureOriginAtBottomLeft;  // Because OpenGL.
    ld.ProjectionDesc = posTimewarpProjectionDesc;
    ld.SensorSampleTime = sensorSampleTime;

    for (int eye = 0; eye < 2; ++eye) {
      ld.ColorTexture[eye] = eyeRenderTexture[eye]->ColorTextureChain;
      ld.DepthTexture[eye] = eyeRenderTexture[eye]->DepthTextureChain;
      ld.Viewport[eye] = Recti(eyeRenderTexture[eye]->GetSize());
      ld.Fov[eye] = hmdDesc.DefaultEyeFov[eye];
      ld.RenderPose[eye] = EyeRenderPose[eye];
    }

    ovrLayerHeader* layers = &ld.Header;
    ovrResult result =
        ovr_SubmitFrame(session, frameIndex, nullptr, &layers, 1);
    // exit the rendering loop if submit returns an error, will retry on
    // ovrError_DisplayLost
    if (!OVR_SUCCESS(result)) goto Done;

    isVisible = (result == ovrSuccess);

    if (session_status.ShouldQuit) {
      // Ok, we currently route quit commands to ballistica
      // which results in an exit(0) at some point; we probably
      // should try to tear down more gracefully.
      SDL_Event e;
      e.type = SDL_QUIT;
      SDL_PushEvent(&e);

      // exit(0);
    }
    if (session_status.ShouldRecenter) {
      ovr_RecenterTrackingOrigin(session);
    }

    // Blit mirror texture to back buffer
    glBindFramebuffer(GL_READ_FRAMEBUFFER, mirrorFBO);
    glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0);
    GLint w = windowSize.w;
    GLint h = windowSize.h;
    glBlitFramebuffer(0, h, w, 0, 0, 0, w, h, GL_COLOR_BUFFER_BIT, GL_NEAREST);
    glBindFramebuffer(GL_READ_FRAMEBUFFER, 0);

    SwapBuffers(Platform.hDC);

    frameIndex++;
  }

Done:
#if OLD_STUFF
  delete roomScene;
#endif  // OLD_STUFF

  if (mirrorFBO) glDeleteFramebuffers(1, &mirrorFBO);
  if (mirrorTexture) ovr_DestroyMirrorTexture(session, mirrorTexture);
  for (int eye = 0; eye < 2; ++eye) {
    delete eyeRenderTexture[eye];
    // delete eyeDepthBuffer[eye];
  }
  Platform.ReleaseDevice();
  ovr_Destroy(session);

  // Retry on ovrError_DisplayLost
  return retryCreate || OVR_SUCCESS(result) || (result == ovrError_DisplayLost);

  // need a test case before allowing retry...
  // return false;
}

//-------------------------------------------------------------------------------------
// int WINAPI WinMain(HINSTANCE hinst, HINSTANCE, LPSTR, int) {

int SDL_main(int argc, char** argv) {
  bool do2d = false;
  for (int i = 0; i < argc; i++) {
    if (!strcmp(argv[i], "-2d")) {
      do2d = true;
    }
  }

  // if they want 2d, hand off to our regular 2d sdl pathway..
  if (do2d) {
    // Fire up ballistica with a normal non-vr config.
    ballistica::MonolithicMain(ballistica::core::CoreConfig());
    assert(!OUR_GLOBALS_NAMESPACE::g_core->vr_mode);
  } else {
    // otherwise do VR goodness...

    // Initializes LibOVR, and the Rift
    ovrResult result = ovr_Initialize(nullptr);

    VALIDATE(OVR_SUCCESS(result), "Failed to initialize libOVR.");

    VALIDATE(Platform.InitWindow(GetModuleHandle(NULL), L"BallisticaKit"),
             "Failed to open window.");
    // VALIDATE(Platform.InitWindow(hinst, L"BallisticaKit VR"),
    // "Failed to open window.");

    Platform.Run(MainLoop);

    ovr_Shutdown();
  }
  return (0);
}

#endif  // BA_RIFT_BUILD
