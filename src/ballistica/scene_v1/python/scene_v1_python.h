// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_PYTHON_SCENE_V1_PYTHON_H_
#define BALLISTICA_SCENE_V1_PYTHON_SCENE_V1_PYTHON_H_

#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/shared/foundation/input_types.h"
#include "ballistica/shared/python/python_object_set.h"

namespace ballistica::base {
class LangStr;
}

namespace ballistica::scene_v1 {

/// General Python support class for SceneV1.
class SceneV1Python {
 public:
  SceneV1Python();
  void Reset();

  /// Convert a Python value destined for a lang-str-flagged string
  /// slot (str | legacy Lstr | babase.LangStr; the D28 acceptance
  /// surface) into its tagged wire form, plus the parsed native value
  /// for the LangStr leg (null otherwise). ``host_session`` (nullable)
  /// supplies the package universe for indexed serialization; without
  /// it (or when indexing fails) LangStrs serialize with
  /// self-describing resource refs. Throws on unsupported types.
  static auto BuildLangStrWireValue(PyObject* obj, HostSession* host_session)
      -> std::pair<std::string, std::shared_ptr<const base::LangStr>>;

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

  void ReloadHooks();

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
  static auto HandleCapturedJoystickEventCall(const BAEvent& event,
                                              base::InputDevice* input_device)
      -> bool;
  static auto HandleCapturedKeyPressCall(const BAKeysym& keysym) -> bool;
  static auto HandleCapturedKeyReleaseCall(const BAKeysym& keysym) -> bool;
  auto HandleCapturedJoystickEvent(const BAEvent& event,
                                   base::InputDevice* input_device = nullptr)
      -> bool;
  auto HandleCapturedKeyPress(const BAKeysym& keysym) -> bool;
  auto HandleCapturedKeyRelease(const BAKeysym& keysym) -> bool;

  PythonObjectSet<ObjID> objs_;
  PythonRef joystick_capture_call_;
  PythonRef keyboard_capture_call_;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_PYTHON_SCENE_V1_PYTHON_H_
