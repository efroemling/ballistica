// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/methods/python_methods_networking.h"

#include <set>
#include <string>
#include <vector>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/networking/network_reader.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/core/python/core_python.h"
#include "ballistica/scene_v1/connection/connection_set.h"
#include "ballistica/scene_v1/connection/connection_to_client.h"
#include "ballistica/scene_v1/connection/connection_to_host_udp.h"
#include "ballistica/scene_v1/python/scene_v1_python.h"
#include "ballistica/shared/math/vector3f.h"
#include "ballistica/shared/networking/sockaddr.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_macros.h"

namespace ballistica::scene_v1 {

// Ignore signed bitwise stuff; python macros do it quite a bit.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"

// ----------------------- get_public_party_enabled  ---------------------------

static auto PyGetPublicPartyEnabled(PyObject* self, PyObject* args,
                                    PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();
  if (appmode->public_party_enabled()) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetPublicPartyEnabledDef = {
    "get_public_party_enabled",            // name
    (PyCFunction)PyGetPublicPartyEnabled,  // method
    METH_VARARGS | METH_KEYWORDS,          // flags

    "get_public_party_enabled() -> bool\n"
    "\n"
    "(internal)",
};

// ----------------------- set_public_party_enabled ----------------------------

static auto PySetPublicPartyEnabled(PyObject* self, PyObject* args,
                                    PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  int enable;
  static const char* kwlist[] = {"enabled", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p",
                                   const_cast<char**>(kwlist), &enable)) {
    return nullptr;
  }
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();
  appmode->SetPublicPartyEnabled(static_cast<bool>(enable));
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetPublicPartyEnabledDef = {
    "set_public_party_enabled",            // name
    (PyCFunction)PySetPublicPartyEnabled,  // method
    METH_VARARGS | METH_KEYWORDS,          // flags

    "set_public_party_enabled(enabled: bool) -> None\n"
    "\n"
    "(internal)",
};

// ------------------------- set_public_party_name -----------------------------

static auto PySetPublicPartyName(PyObject* self, PyObject* args,
                                 PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* name_obj;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &name_obj)) {
    return nullptr;
  }
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();
  std::string name = g_base->python->GetPyLString(name_obj);
  appmode->SetPublicPartyName(name);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetPublicPartyNameDef = {
    "set_public_party_name",            // name
    (PyCFunction)PySetPublicPartyName,  // method
    METH_VARARGS | METH_KEYWORDS,       // flags

    "set_public_party_name(name: str) -> None\n"
    "\n"
    "(internal)",
};

// ----------------------- set_public_party_stats_url --------------------------

static auto PySetPublicPartyStatsURL(PyObject* self, PyObject* args,
                                     PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* url_obj;
  static const char* kwlist[] = {"url", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &url_obj)) {
    return nullptr;
  }
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();

  // The call expects an empty string for the no-url option.
  std::string url = (url_obj == Py_None) ? "" : Python::GetString(url_obj);
  appmode->SetPublicPartyStatsURL(url);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetPublicPartyStatsURLDef = {
    "set_public_party_stats_url",           // name
    (PyCFunction)PySetPublicPartyStatsURL,  // method
    METH_VARARGS | METH_KEYWORDS,           // flags

    "set_public_party_stats_url(url: str | None) -> None\n"
    "\n"
    "(internal)",
};

// ----------------------- get_public_party_max_size ---------------------------

static auto PyGetPublicPartyMaxSize(PyObject* self, PyObject* args,
                                    PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();
  return PyLong_FromLong(appmode->public_party_max_size());
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetPublicPartyMaxSizeDef = {
    "get_public_party_max_size",           // name
    (PyCFunction)PyGetPublicPartyMaxSize,  // method
    METH_VARARGS | METH_KEYWORDS,          // flags

    "get_public_party_max_size() -> int\n"
    "\n"
    "(internal)",
};

// ----------------------- set_public_party_max_size ---------------------------

static auto PySetPublicPartyMaxSize(PyObject* self, PyObject* args,
                                    PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  int max_size;
  static const char* kwlist[] = {"max_size", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "i",
                                   const_cast<char**>(kwlist), &max_size)) {
    return nullptr;
  }
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();
  appmode->SetPublicPartyMaxSize(max_size);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetPublicPartyMaxSizeDef = {
    "set_public_party_max_size",           // name
    (PyCFunction)PySetPublicPartyMaxSize,  // method
    METH_VARARGS | METH_KEYWORDS,          // flags

    "set_public_party_max_size(max_size: int) -> None\n"
    "\n"

    "(internal)",
};

// --------------------- set_public_party_queue_enabled ------------------------

static auto PySetPublicPartyQueueEnabled(PyObject* self, PyObject* args,
                                         PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  int enabled;
  static const char* kwlist[] = {"enabled", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p",
                                   const_cast<char**>(kwlist), &enabled)) {
    return nullptr;
  }
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();
  appmode->SetPublicPartyQueueEnabled(enabled);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetPublicPartyQueueEnabledDef = {
    "set_public_party_queue_enabled",           // name
    (PyCFunction)PySetPublicPartyQueueEnabled,  // method
    METH_VARARGS | METH_KEYWORDS,               // flags

    "set_public_party_queue_enabled(max_size: bool) -> None\n"
    "\n"
    "(internal)",
};

// ----------------- set_public_party_public_address_ipv4 ----------------------

static auto PySetPublicPartyPublicAddressIPV4(PyObject* self, PyObject* args,
                                              PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* address_obj;
  static const char* kwlist[] = {"address", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &address_obj)) {
    return nullptr;
  }
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();

  // The call expects an empty string for the no-url option.

  std::optional<std::string> address{};
  if (address_obj != Py_None) {
    address = Python::GetString(address_obj);
  }
  appmode->set_public_party_public_address_ipv4(address);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetPublicPartyPublicAddressIPV4Def = {
    "set_public_party_public_address_ipv4",          // name
    (PyCFunction)PySetPublicPartyPublicAddressIPV4,  // method
    METH_VARARGS | METH_KEYWORDS,                    // flags

    "set_public_party_public_address_ipv4(address: str | None) -> None\n"
    "\n"
    "(internal)",
};

// ----------------- set_public_party_public_address_ipv6 ----------------------

static auto PySetPublicPartyPublicAddressIPV6(PyObject* self, PyObject* args,
                                              PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* address_obj;
  static const char* kwlist[] = {"address", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &address_obj)) {
    return nullptr;
  }
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();

  // The call expects an empty string for the no-url option.

  std::optional<std::string> address{};
  if (address_obj != Py_None) {
    address = Python::GetString(address_obj);
  }
  appmode->set_public_party_public_address_ipv6(address);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetPublicPartyPublicAddressIPV6Def = {
    "set_public_party_public_address_ipv6",          // name
    (PyCFunction)PySetPublicPartyPublicAddressIPV6,  // method
    METH_VARARGS | METH_KEYWORDS,                    // flags

    "set_public_party_public_address_ipv6(address: str | None) -> None\n"
    "\n"
    "(internal)",
};

// ------------------------ set_authenticate_clients ---------------------------

static auto PySetAuthenticateClients(PyObject* self, PyObject* args,
                                     PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  int enable;
  static const char* kwlist[] = {"enable", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p",
                                   const_cast<char**>(kwlist), &enable)) {
    return nullptr;
  }
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();
  appmode->set_require_client_authentication(static_cast<bool>(enable));
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetAuthenticateClientsDef = {
    "set_authenticate_clients",             // name
    (PyCFunction)PySetAuthenticateClients,  // method
    METH_VARARGS | METH_KEYWORDS,           // flags

    "set_authenticate_clients(enable: bool) -> None\n"
    "\n"
    "(internal)",
};

// ------------------------------- set_admins ----------------------------------

static auto PySetAdmins(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* admins_obj;
  static const char* kwlist[] = {"admins", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &admins_obj)) {
    return nullptr;
  }
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();

  auto admins = Python::GetStrings(admins_obj);
  std::set<std::string> adminset;
  for (auto&& admin : admins) {
    adminset.insert(admin);
  }
  appmode->set_admin_public_ids(adminset);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetAdminsDef = {
    "set_admins",                  // name
    (PyCFunction)PySetAdmins,      // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "set_admins(admins: list[str]) -> None\n"
    "\n"
    "(internal)",
};

// --------------------- set_enable_default_kick_voting ------------------------

static auto PySetEnableDefaultKickVoting(PyObject* self, PyObject* args,
                                         PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  int enable;
  static const char* kwlist[] = {"enable", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p",
                                   const_cast<char**>(kwlist), &enable)) {
    return nullptr;
  }
  assert(g_base->logic);

  if (auto* appmode{classic::ClassicAppMode::GetActiveOrWarn()}) {
    appmode->set_kick_voting_enabled(static_cast<bool>(enable));
  }

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetEnableDefaultKickVotingDef = {
    "set_enable_default_kick_voting",           // name
    (PyCFunction)PySetEnableDefaultKickVoting,  // method
    METH_VARARGS | METH_KEYWORDS,               // flags

    "set_enable_default_kick_voting(enable: bool) -> None\n"
    "\n"
    "(internal)",
};

// --------------------------- connect_to_party --------------------------------

static auto PyConnectToParty(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  std::string address;
  PyObject* address_obj;
  int port = kDefaultPort;

  // Whether we should print standard 'connecting...' and 'party full..'
  // messages when false, only odd errors such as version incompatibility will
  // be printed and most connection attempts will be silent todo: could
  // generalize this to pass all results to a callback instead
  int print_progress = 1;
  static const char* kwlist[] = {"address", "port", "print_progress", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O|ip",
                                   const_cast<char**>(kwlist), &address_obj,
                                   &port, &print_progress)) {
    return nullptr;
  }

  // Error if we're not in our app-mode.
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();

  address = Python::GetString(address_obj);

  // Disallow in headless build (people were using this for spam-bots).

  if (g_core->HeadlessMode()) {
    throw Exception("Not available in headless mode.");
  }

  SockAddr s;
  try {
    s = SockAddr(address, port);

    // HACK: CLion currently flags our catch clause as unreachable even
    // though SockAddr constructor can throw exceptions. Work around that here.
    if (explicit_bool(false)) {
      throw Exception();
    }
  } catch (const std::exception&) {
    g_base->ScreenMessage(
        g_base->assets->GetResourceString("invalidAddressErrorText"),
        {1, 0, 0});
    Py_RETURN_NONE;
  }
  appmode->connections()->PushHostConnectedUDPCall(
      s, static_cast<bool>(print_progress));
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyConnectToPartyDef = {
    "connect_to_party",             // name
    (PyCFunction)PyConnectToParty,  // method
    METH_VARARGS | METH_KEYWORDS,   // flags

    "connect_to_party(address: str, port: int | None = None,\n"
    "  print_progress: bool = True) -> None\n"
    "\n"
    "(internal)",
};

// ---------------------- client_info_query_response ---------------------------

static auto PyClientInfoQueryResponse(PyObject* self, PyObject* args,
                                      PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  const char* token;
  PyObject* response_obj;
  static const char* kwlist[] = {"token", "response", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "sO",
                                   const_cast<char**>(kwlist), &token,
                                   &response_obj)) {
    return nullptr;
  }
  // Error if we're not in our app-mode.
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();

  appmode->connections()->SetClientInfoFromMasterServer(token, response_obj);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyClientInfoQueryResponseDef = {
    "client_info_query_response",            // name
    (PyCFunction)PyClientInfoQueryResponse,  // method
    METH_VARARGS | METH_KEYWORDS,            // flags

    "client_info_query_response(token: str, response: Any) -> None\n"
    "\n"
    "(internal)",
};

// ---------------------- get_connection_to_host_info --------------------------

static auto PyGetConnectionToHostInfo(PyObject* self, PyObject* args,
                                      PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kWarning,
              "bascenev1.get_connection_to_host_info() is deprecated; use "
              "bascenev1.get_connection_to_host_info_2().");
  BA_PRECONDITION(g_base->InLogicThread());
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();

  ConnectionToHost* hc = appmode->connections()->connection_to_host();
  if (hc) {
    return Py_BuildValue("{sssi}", "name", hc->party_name().c_str(),
                         "build_number", hc->build_number());
  } else {
    return Py_BuildValue("{}");
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetConnectionToHostInfoDef = {
    "get_connection_to_host_info",           // name
    (PyCFunction)PyGetConnectionToHostInfo,  // method
    METH_VARARGS | METH_KEYWORDS,            // flags

    "get_connection_to_host_info() -> dict\n"
    "\n"
    "(internal)",
};

// --------------------- get_connection_to_host_info_2 -------------------------

static auto PyGetConnectionToHostInfo2(PyObject* self, PyObject* args,
                                       PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  BA_PRECONDITION(g_base->InLogicThread());
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();

  ConnectionToHost* hc = appmode->connections()->connection_to_host();
  if (hc) {
    PythonRef addr_obj;
    PythonRef port_obj;
    if (ConnectionToHostUDP* hcu = dynamic_cast<ConnectionToHostUDP*>(hc)) {
      addr_obj.Steal(PyUnicode_FromString(hcu->addr().AddressString().c_str()));
      port_obj.Steal(PyLong_FromLong(hcu->addr().Port()));
    } else {
      addr_obj.Acquire(Py_None);
      port_obj.Acquire(Py_None);
    }
    auto args =
        g_core->python->objs().Get(core::CorePython::ObjID::kEmptyTuple);
    auto keywds = PythonRef::Stolen(Py_BuildValue(
        "{sssisOsO}", "name", hc->party_name().c_str(), "build_number",
        hc->build_number(), "address", addr_obj.get(), "port", port_obj.get()));
    auto result = g_scene_v1->python->objs()
                      .Get(SceneV1Python::ObjID::kHostInfoClass)
                      .Call(args, keywds);
    if (!result.exists()) {
      throw Exception("Failed to instantiate HostInfo.", PyExcType::kRuntime);
    }
    return result.HandOver();
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetConnectionToHostInfo2Def = {
    "get_connection_to_host_info_2",          // name
    (PyCFunction)PyGetConnectionToHostInfo2,  // method
    METH_VARARGS | METH_KEYWORDS,             // flags

    "get_connection_to_host_info_2() -> bascenev1.HostInfo | None\n"
    "\n"
    "Return info about the host we are currently connected to.",
};

// --------------------------- disconnect_from_host ----------------------------

static auto PyDisconnectFromHost(PyObject* self, PyObject* args,
                                 PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  // Error if we're not in our app-mode.
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();

  appmode->connections()->PushDisconnectFromHostCall();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyDisconnectFromHostDef = {
    "disconnect_from_host",             // name
    (PyCFunction)PyDisconnectFromHost,  // method
    METH_VARARGS | METH_KEYWORDS,       // flags

    "disconnect_from_host() -> None\n"
    "\n"
    "(internal)",
};

// --------------------------- disconnect_client -------------------------------

static auto PyDisconnectClient(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  int client_id;
  int ban_time = 300;  // Old default before we exposed this.
  static const char* kwlist[] = {"client_id", "ban_time", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "i|i",
                                   const_cast<char**>(kwlist), &client_id,
                                   &ban_time)) {
    return nullptr;
  }
  // Error if we're not in our app-mode.
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();

  bool kickable = appmode->connections()->DisconnectClient(client_id, ban_time);
  if (kickable) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

static PyMethodDef PyDisconnectClientDef = {
    "disconnect_client",              // name
    (PyCFunction)PyDisconnectClient,  // method
    METH_VARARGS | METH_KEYWORDS,     // flags

    "disconnect_client(client_id: int, ban_time: int = 300) -> bool\n"
    "\n"
    "(internal)",
};

// --------------------- get_client_public_device_uuid -------------------------

static auto PyGetClientPublicDeviceUUID(PyObject* self, PyObject* args,
                                        PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  int client_id;
  static const char* kwlist[] = {"client_id", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "i",
                                   const_cast<char**>(kwlist), &client_id)) {
    return nullptr;
  }
  // Error if we're not in our app-mode.
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();

  auto&& connection{
      appmode->connections()->connections_to_clients().find(client_id)};

  // Does this connection exist?
  if (connection == appmode->connections()->connections_to_clients().end()) {
    Py_RETURN_NONE;
  }

  // Connections should always be valid refs.
  assert(connection->second.exists());

  // Old clients don't assign this; it will be empty.
  if (connection->second->public_device_id().empty()) {
    Py_RETURN_NONE;
  }
  return PyUnicode_FromString(connection->second->public_device_id().c_str());
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetClientPublicDeviceUUIDDef = {
    "get_client_public_device_uuid",           // name
    (PyCFunction)PyGetClientPublicDeviceUUID,  // method
    METH_VARARGS | METH_KEYWORDS,              // flags

    "get_client_public_device_uuid(client_id: int) -> str | None\n"
    "\n"
    "(internal)\n"
    "\n"
    "Return a public device UUID for a client. If the client does not\n"
    "exist or is running a version older than 1.6.10, returns None.\n"
    "Public device UUID uniquely identifies the device the client is\n"
    "using in a semi-permanent way. The UUID value will change\n"
    "periodically with updates to the game or operating system.",
};

// ----------------------------- get_game_port ---------------------------------

static auto PyGetGamePort(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  int port = 0;
  if (g_base && g_base->network_reader != nullptr) {
    // Hmmm; we're just fetching the ipv4 port here; 6 could be different.
    port = g_base->network_reader->port4();
  }
  return Py_BuildValue("i", port);
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetGamePortDef = {
    "get_game_port",  // name
    PyGetGamePort,    // method
    METH_VARARGS,     // flags

    "get_game_port() -> int\n"
    "\n"
    "(internal)\n"
    "\n"
    "Return the port ballistica is hosting on.",
};

// ------------------------ set_master_server_source ---------------------------

static auto PySetMasterServerSource(PyObject* self, PyObject* args)
    -> PyObject* {
  BA_PYTHON_TRY;
  int source;
  if (!PyArg_ParseTuple(args, "i", &source)) return nullptr;
  if (source != 0 && source != 1) {
    BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kError,
                "Invalid server source: " + std::to_string(source) + ".");
    source = 1;
  }
  g_core->master_server_source = source;
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PySetMasterServerSourceDef = {
    "set_master_server_source",  // name
    PySetMasterServerSource,     // method
    METH_VARARGS,                // flags

    "set_master_server_source(source: int) -> None\n"
    "\n"
    "(internal)",
};

// ----------------------------- host_scan_cycle -------------------------------

static auto PyHostScanCycle(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();
  appmode->HostScanCycle();
  std::vector<classic::ClassicAppMode::ScanResultsEntry> results =
      appmode->GetScanResults();
  PyObject* py_list = PyList_New(0);
  for (auto&& i : results) {
    PyList_Append(py_list, Py_BuildValue("{ssss}", "display_string",
                                         i.display_string.c_str(), "address",
                                         i.address.c_str()));
  }
  return py_list;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyHostScanCycleDef = {
    "host_scan_cycle",             // name
    (PyCFunction)PyHostScanCycle,  // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "host_scan_cycle() -> list\n"
    "\n"
    "(internal)\n"
    "\n"
    ":meta private:",
};

// ---------------------------- end_host_scanning ------------------------------

static auto PyEndHostScanning(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();
  appmode->EndHostScanning();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyEndHostScanningDef = {
    "end_host_scanning",             // name
    (PyCFunction)PyEndHostScanning,  // method
    METH_VARARGS | METH_KEYWORDS,    // flags

    "end_host_scanning() -> None\n"
    "\n"
    "(internal)",
};

// ------------------------- have_connected_clients ----------------------------

static auto PyHaveConnectedClients(PyObject* self, PyObject* args,
                                   PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  if (g_base->app_mode()->HasConnectionToClients()) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

static PyMethodDef PyHaveConnectedClientsDef = {
    "have_connected_clients",             // name
    (PyCFunction)PyHaveConnectedClients,  // method
    METH_VARARGS | METH_KEYWORDS,         // flags

    "have_connected_clients() -> bool\n"
    "\n"
    "(internal)\n"
    "\n"
    ":meta private:",
};

// ------------------------------ chatmessage ----------------------------------

static auto PyChatMessage(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  std::string message;
  PyObject* message_obj;
  PyObject* clients_obj = Py_None;
  PyObject* sender_override_obj = Py_None;
  std::string sender_override;
  const std::string* sender_override_p{};
  std::vector<int> clients;
  std::vector<int>* clients_p{};

  static const char* kwlist[] = {"message", "clients", "sender_override",
                                 nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O|OO",
                                   const_cast<char**>(kwlist), &message_obj,
                                   &clients_obj, &sender_override_obj)) {
    return nullptr;
  }
  BA_PRECONDITION(g_base->InLogicThread());
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();

  message = g_base->python->GetPyLString(message_obj);
  if (sender_override_obj != Py_None) {
    sender_override = g_base->python->GetPyLString(sender_override_obj);
    sender_override_p = &sender_override;
  }

  if (clients_obj != Py_None) {
    clients = Python::GetInts(clients_obj);
    clients_p = &clients;
  }
  appmode->connections()->SendChatMessage(message, clients_p,
                                          sender_override_p);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyChatMessageDef = {
    "chatmessage",                 // name
    (PyCFunction)PyChatMessage,    // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "chatmessage(message: str | babase.Lstr,\n"
    "  clients: Sequence[int] | None = None,\n"
    "  sender_override: str | None = None) -> None\n"
    "\n"
    "(internal)",
};

// --------------------------- get_chat_messages -------------------------------

static auto PyGetChatMessages(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  BA_PRECONDITION(g_base->InLogicThread());
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  auto* appmode = classic::ClassicAppMode::GetActiveOrThrow();
  PyObject* py_list = PyList_New(0);
  for (auto&& i : appmode->chat_messages()) {
    PyList_Append(py_list, PyUnicode_FromString(i.c_str()));
  }
  return py_list;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetChatMessagesDef = {
    "get_chat_messages",             // name
    (PyCFunction)PyGetChatMessages,  // method
    METH_VARARGS | METH_KEYWORDS,    // flags

    "get_chat_messages() -> list[str]\n"
    "\n"
    "(internal)",
};

// -----------------------------------------------------------------------------

auto PythonMethodsNetworking::GetMethods() -> std::vector<PyMethodDef> {
  return {
      PyHaveConnectedClientsDef,
      PyEndHostScanningDef,
      PyHostScanCycleDef,
      PySetMasterServerSourceDef,
      PyGetGamePortDef,
      PyDisconnectFromHostDef,
      PyDisconnectClientDef,
      PyGetClientPublicDeviceUUIDDef,
      PyGetConnectionToHostInfoDef,
      PyGetConnectionToHostInfo2Def,
      PyClientInfoQueryResponseDef,
      PyConnectToPartyDef,
      PySetPublicPartyPublicAddressIPV4Def,
      PySetPublicPartyPublicAddressIPV6Def,
      PySetAuthenticateClientsDef,
      PySetAdminsDef,
      PySetEnableDefaultKickVotingDef,
      PySetPublicPartyMaxSizeDef,
      PySetPublicPartyQueueEnabledDef,
      PyGetPublicPartyMaxSizeDef,
      PySetPublicPartyStatsURLDef,
      PySetPublicPartyNameDef,
      PySetPublicPartyEnabledDef,
      PyGetPublicPartyEnabledDef,
      PyChatMessageDef,
      PyGetChatMessagesDef,
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica::scene_v1
