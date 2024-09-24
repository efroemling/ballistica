// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_SCENE_V1_PYTHON_H_
#define BALLISTICA_SCENE_V1_PYTHON_SCENE_V1_PYTHON_H_

#include "ballistica/base/base.h"
#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/python/python_object_set.h"

namespace ballistica::scene_v1 {

/// General Python support class for SceneV1.
class SceneV1Python {
 public:
  SceneV1Python();
  void Reset();

  static void SetNodeAttr(Node* node, const char* attr_name,
                          PyObject* value_obj);
  static auto DoNewNode(PyObject* args, PyObject* keywds) -> Node*;
  static auto GetNodeAttr(Node* node, const char* attr_name) -> PyObject*;
  static auto GetPyHostActivity(PyObject* o) -> HostActivity*;
  static auto IsPyHostActivity(PyObject* o) -> bool;
  static auto GetPyNode(PyObject* o, bool allow_empty_ref = false,
                        bool allow_none = false) -> Node*;
  static auto GetPyNodes(PyObject* o) -> std::vector<Node*>;
  static auto GetPyMaterial(PyObject* o, bool allow_empty_ref = false,
                            bool allow_none = false) -> Material*;
  static auto GetPyMaterials(PyObject* o) -> std::vector<Material*>;
  static auto GetPySceneTexture(PyObject* o, bool allow_empty_ref = false,
                                bool allow_none = false) -> SceneTexture*;
  static auto GetPySceneTextures(PyObject* o) -> std::vector<SceneTexture*>;
  static auto GetPySceneMesh(PyObject* o, bool allow_empty_ref = false,
                             bool allow_none = false) -> SceneMesh*;
  static auto GetPySceneMeshes(PyObject* o) -> std::vector<SceneMesh*>;
  static auto IsPyPlayer(PyObject* o) -> bool;
  static auto GetPyPlayer(PyObject* o, bool allow_empty_ref = false,
                          bool allow_none = false) -> Player*;
  static auto GetPySceneSound(PyObject* o, bool allow_empty_ref = false,
                              bool allow_none = false) -> SceneSound*;
  static auto GetPySceneSounds(PyObject* o) -> std::vector<SceneSound*>;
  static auto GetPySceneCollisionMesh(PyObject* o, bool allow_empty_ref = false,
                                      bool allow_none = false)
      -> SceneCollisionMesh*;
  static auto GetPySceneCollisionMeshes(PyObject* o)
      -> std::vector<SceneCollisionMesh*>;
  static auto IsPySession(PyObject* o) -> bool;
  static auto GetPySession(PyObject* o) -> Session*;
  static auto GetPySessionPlayer(PyObject* o, bool allow_empty_ref = false,
                                 bool allow_none = false) -> Player*;
  static auto GetPySceneDataAsset(PyObject* o, bool allow_empty_ref = false,
                                  bool allow_none = false) -> SceneDataAsset*;
  static void DoBuildNodeMessage(PyObject* args, int arg_offset,
                                 std::vector<char>* b,
                                 PyObject** user_message_obj);
  static auto GetPyInputDevice(PyObject* o) -> SceneV1InputDeviceDelegate*;

  void CaptureJoystickInput(PyObject* obj);
  void ReleaseJoystickInputCapture();
  void CaptureKeyboardInput(PyObject* obj);
  void ReleaseKeyboardInputCapture();

  /// Filter incoming chat message from client.
  /// If returns false, message should be ignored.
  auto FilterChatMessage(std::string* message, int client_id) -> bool;

  /// Pass a chat message along to the python UI layer for handling..
  void HandleLocalChatMessage(const std::string& message);

  /// Given an asset-package python object and a media name, verify
  /// that the asset-package is valid in the current context_ref and return
  /// its fully qualified name if so.  Throw an Exception if not.
  auto ValidatedPackageAssetName(PyObject* package, const char* name)
      -> std::string;

  /// Specific Python objects we hold in objs_.
  enum class ObjID {
    kClientInfoQueryResponseCall,
    kShouldShatterMessageClass,
    kImpactDamageMessageClass,
    kPickedUpMessageClass,
    kDroppedMessageClass,
    kOutOfBoundsMessageClass,
    kPickUpMessageClass,
    kDropMessageClass,
    kPlayerClass,
    kAssetPackageClass,
    kActivityClass,
    kSceneV1SessionClass,
    kLaunchMainMenuSessionCall,
    kGetPlayerIconCall,
    kFilterChatMessageCall,
    kHandleLocalChatMessageCall,
    kHostInfoClass,
    kLast  // Sentinel; must be at end.
  };

  void AddPythonClasses(PyObject* module);
  void ImportPythonObjs();

  const auto& objs() { return objs_; }

 private:
  static auto HandleCapturedJoystickEventCall(const SDL_Event& event,
                                              base::InputDevice* input_device)
      -> bool;
  static auto HandleCapturedKeyPressCall(const SDL_Keysym& keysym) -> bool;
  static auto HandleCapturedKeyReleaseCall(const SDL_Keysym& keysym) -> bool;
  auto HandleCapturedJoystickEvent(const SDL_Event& event,
                                   base::InputDevice* input_device = nullptr)
      -> bool;
  auto HandleCapturedKeyPress(const SDL_Keysym& keysym) -> bool;
  auto HandleCapturedKeyRelease(const SDL_Keysym& keysym) -> bool;

  PythonObjectSet<ObjID> objs_;
  PythonRef joystick_capture_call_;
  PythonRef keyboard_capture_call_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_SCENE_V1_PYTHON_H_
