// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/methods/python_methods_networking.h"

#include "ballistica/app/app.h"
#include "ballistica/logic/connection/connection_set.h"
#include "ballistica/logic/connection/connection_to_client.h"
#include "ballistica/logic/connection/connection_to_host.h"
#include "ballistica/logic/logic.h"
#include "ballistica/math/vector3f.h"
#include "ballistica/networking/network_reader.h"
#include "ballistica/networking/networking.h"
#include "ballistica/networking/sockaddr.h"
#include "ballistica/networking/telnet_server.h"
#include "ballistica/platform/platform.h"
#include "ballistica/python/python.h"
#include "ballistica/python/python_sys.h"

namespace ballistica {

// Ignore signed bitwise stuff; python macros do it quite a bit.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"

auto PyGetPublicPartyEnabled(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist)))
    return nullptr;
  assert(g_python);
  if (g_logic->public_party_enabled()) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

auto PySetPublicPartyEnabled(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  int enable;
  static const char* kwlist[] = {"enabled", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p",
                                   const_cast<char**>(kwlist), &enable)) {
    return nullptr;
  }
  assert(g_python);
  g_logic->SetPublicPartyEnabled(static_cast<bool>(enable));
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PySetPublicPartyName(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* name_obj;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &name_obj)) {
    return nullptr;
  }
  std::string name = Python::GetPyString(name_obj);
  assert(g_python);
  g_logic->SetPublicPartyName(name);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PySetPublicPartyStatsURL(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* url_obj;
  static const char* kwlist[] = {"url", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &url_obj)) {
    return nullptr;
  }
  // The call expects an empty string for the no-url option.
  std::string url = (url_obj == Py_None) ? "" : Python::GetPyString(url_obj);
  assert(g_python);
  g_logic->SetPublicPartyStatsURL(url);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyGetPublicPartyMaxSize(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  assert(g_python);
  return PyLong_FromLong(g_logic->public_party_max_size());
  BA_PYTHON_CATCH;
}

auto PySetPublicPartyMaxSize(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  int max_size;
  static const char* kwlist[] = {"max_size", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "i",
                                   const_cast<char**>(kwlist), &max_size)) {
    return nullptr;
  }
  assert(g_python);
  g_logic->SetPublicPartyMaxSize(max_size);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PySetPublicPartyQueueEnabled(PyObject* self, PyObject* args,
                                  PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  int enabled;
  static const char* kwlist[] = {"enabled", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p",
                                   const_cast<char**>(kwlist), &enabled)) {
    return nullptr;
  }
  assert(g_python);
  g_logic->SetPublicPartyQueueEnabled(enabled);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PySetAuthenticateClients(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  int enable;
  static const char* kwlist[] = {"enable", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p",
                                   const_cast<char**>(kwlist), &enable)) {
    return nullptr;
  }
  assert(g_logic);
  g_logic->set_require_client_authentication(static_cast<bool>(enable));
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PySetAdmins(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* admins_obj;
  static const char* kwlist[] = {"admins", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &admins_obj)) {
    return nullptr;
  }
  assert(g_logic);

  auto admins = Python::GetPyStrings(admins_obj);
  std::set<std::string> adminset;
  for (auto&& admin : admins) {
    adminset.insert(admin);
  }
  g_logic->set_admin_public_ids(adminset);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PySetEnableDefaultKickVoting(PyObject* self, PyObject* args,
                                  PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  int enable;
  static const char* kwlist[] = {"enable", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p",
                                   const_cast<char**>(kwlist), &enable)) {
    return nullptr;
  }
  assert(g_logic);
  g_logic->set_kick_voting_enabled(static_cast<bool>(enable));
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyConnectToParty(PyObject* self, PyObject* args, PyObject* keywds)
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
  address = Python::GetPyString(address_obj);

  // Disallow in headless build (people were using this for spam-bots).

  if (HeadlessMode()) {
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
    ScreenMessage(g_logic->GetResourceString("invalidAddressErrorText"),
                  {1, 0, 0});
    Py_RETURN_NONE;
  }
  g_logic->connections()->PushHostConnectedUDPCall(
      s, static_cast<bool>(print_progress));
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyClientInfoQueryResponse(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* token;
  PyObject* response_obj;
  static const char* kwlist[] = {"token", "response", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "sO",
                                   const_cast<char**>(kwlist), &token,
                                   &response_obj)) {
    return nullptr;
  }
  g_logic->connections()->SetClientInfoFromMasterServer(token, response_obj);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyGetConnectionToHostInfo(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  ConnectionToHost* hc = g_logic->connections()->connection_to_host();
  if (hc) {
    return Py_BuildValue("{sssi}", "name", hc->party_name().c_str(),
                         "build_number", hc->build_number());
  } else {
    return Py_BuildValue("{}");
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyDisconnectFromHost(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  g_logic->connections()->PushDisconnectFromHostCall();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyDisconnectClient(PyObject* self, PyObject* args, PyObject* keywds)
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
  bool kickable = g_logic->connections()->DisconnectClient(client_id, ban_time);
  if (kickable) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

auto PyGetClientPublicDeviceUUID(PyObject* self, PyObject* args,
                                 PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  int client_id;
  static const char* kwlist[] = {"client_id", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "i",
                                   const_cast<char**>(kwlist), &client_id)) {
    return nullptr;
  }
  auto&& connection{
      g_logic->connections()->connections_to_clients().find(client_id)};

  // Does this connection exist?
  if (connection == g_logic->connections()->connections_to_clients().end()) {
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

auto PyGetGamePort(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  int port = 0;
  if (g_network_reader != nullptr) {
    // Hmmm; we're just fetching the ipv4 port here; 6 could be different.
    port = g_network_reader->port4();
  }
  return Py_BuildValue("i", port);
  BA_PYTHON_CATCH;
}

auto PySetMasterServerSource(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  int source;
  if (!PyArg_ParseTuple(args, "i", &source)) return nullptr;
  if (source != 0 && source != 1) {
    BA_LOG_ONCE(LogLevel::kError,
                "Invalid server source: " + std::to_string(source) + ".");
    source = 1;
  }
  g_app->master_server_source = source;
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PySetTelnetAccessEnabled(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(InLogicThread());
  int enable;
  static const char* kwlist[] = {"enable", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p",
                                   const_cast<char**>(kwlist), &enable)) {
    return nullptr;
  }
  if (g_app->telnet_server) {
    g_app->telnet_server->SetAccessEnabled(static_cast<bool>(enable));
  } else {
    throw Exception("Telnet server not enabled.");
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyHostScanCycle(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  g_networking->HostScanCycle();
  std::vector<Networking::ScanResultsEntry> results =
      g_networking->GetScanResults();
  PyObject* py_list = PyList_New(0);
  for (auto&& i : results) {
    PyList_Append(py_list, Py_BuildValue("{ssss}", "display_string",
                                         i.display_string.c_str(), "address",
                                         i.address.c_str()));
  }
  return py_list;
  BA_PYTHON_CATCH;
}

auto PyEndHostScanning(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  g_networking->EndHostScanning();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyHaveConnectedClients(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  if (g_logic->connections()->GetConnectedClientCount() > 0) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

auto PythonMethodsNetworking::GetMethods() -> std::vector<PyMethodDef> {
  return {
      {"have_connected_clients", (PyCFunction)PyHaveConnectedClients,
       METH_VARARGS | METH_KEYWORDS,
       "have_connected_clients() -> bool\n"
       "\n"
       "(internal)\n"
       "\n"
       "Category: General Utility Functions"},

      {"end_host_scanning", (PyCFunction)PyEndHostScanning,
       METH_VARARGS | METH_KEYWORDS,
       "end_host_scanning() -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Category: General Utility Functions"},

      {"host_scan_cycle", (PyCFunction)PyHostScanCycle,
       METH_VARARGS | METH_KEYWORDS,
       "host_scan_cycle() -> list\n"
       "\n"
       "(internal)"},

      {"set_telnet_access_enabled", (PyCFunction)PySetTelnetAccessEnabled,
       METH_VARARGS | METH_KEYWORDS,
       "set_telnet_access_enabled(enable: bool)\n"
       " -> None\n"
       "\n"
       "(internal)"},

      {"set_master_server_source", PySetMasterServerSource, METH_VARARGS,
       "set_master_server_source(source: int) -> None\n"
       "\n"
       "(internal)"},

      {"get_game_port", PyGetGamePort, METH_VARARGS,
       "get_game_port() -> int\n"
       "\n"
       "(internal)\n"
       "\n"
       "Return the port ballistica is hosting on."},

      {"disconnect_from_host", (PyCFunction)PyDisconnectFromHost,
       METH_VARARGS | METH_KEYWORDS,
       "disconnect_from_host() -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Category: General Utility Functions"},

      {"disconnect_client", (PyCFunction)PyDisconnectClient,
       METH_VARARGS | METH_KEYWORDS,
       "disconnect_client(client_id: int, ban_time: int = 300) -> bool\n"
       "\n"
       "(internal)"},

      {"get_client_public_device_uuid",
       (PyCFunction)PyGetClientPublicDeviceUUID, METH_VARARGS | METH_KEYWORDS,
       "get_client_public_device_uuid(client_id: int) -> str | None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Category: General Utility Functions\n"
       "\n"
       "Return a public device UUID for a client. If the client does not\n"
       "exist or is running a version older than 1.6.10, returns None.\n"
       "Public device UUID uniquely identifies the device the client is\n"
       "using in a semi-permanent way. The UUID value will change\n"
       "periodically with updates to the game or operating system."},

      {"get_connection_to_host_info", (PyCFunction)PyGetConnectionToHostInfo,
       METH_VARARGS | METH_KEYWORDS,
       "get_connection_to_host_info() -> dict\n"
       "\n"
       "(internal)"},

      {"client_info_query_response", (PyCFunction)PyClientInfoQueryResponse,
       METH_VARARGS | METH_KEYWORDS,
       "client_info_query_response(token: str, response: Any) -> None\n"
       "\n"
       "(internal)"},

      {"connect_to_party", (PyCFunction)PyConnectToParty,
       METH_VARARGS | METH_KEYWORDS,
       "connect_to_party(address: str, port: int | None = None,\n"
       "  print_progress: bool = True) -> None\n"
       "\n"
       "(internal)"},

      {"set_authenticate_clients", (PyCFunction)PySetAuthenticateClients,
       METH_VARARGS | METH_KEYWORDS,
       "set_authenticate_clients(enable: bool) -> None\n"
       "\n"
       "(internal)"},

      {"set_admins", (PyCFunction)PySetAdmins, METH_VARARGS | METH_KEYWORDS,
       "set_admins(admins: list[str]) -> None\n"
       "\n"
       "(internal)"},

      {"set_enable_default_kick_voting",
       (PyCFunction)PySetEnableDefaultKickVoting, METH_VARARGS | METH_KEYWORDS,
       "set_enable_default_kick_voting(enable: bool) -> None\n"
       "\n"
       "(internal)"},

      {"set_public_party_max_size", (PyCFunction)PySetPublicPartyMaxSize,
       METH_VARARGS | METH_KEYWORDS,
       "set_public_party_max_size(max_size: int) -> None\n"
       "\n"

       "(internal)"},

      {"set_public_party_queue_enabled",
       (PyCFunction)PySetPublicPartyQueueEnabled, METH_VARARGS | METH_KEYWORDS,
       "set_public_party_queue_enabled(max_size: bool) -> None\n"
       "\n"
       "(internal)"},

      {"get_public_party_max_size", (PyCFunction)PyGetPublicPartyMaxSize,
       METH_VARARGS | METH_KEYWORDS,
       "get_public_party_max_size() -> int\n"
       "\n"
       "(internal)"},

      {"set_public_party_stats_url", (PyCFunction)PySetPublicPartyStatsURL,
       METH_VARARGS | METH_KEYWORDS,
       "set_public_party_stats_url(url: str | None) -> None\n"
       "\n"
       "(internal)"},

      {"set_public_party_name", (PyCFunction)PySetPublicPartyName,
       METH_VARARGS | METH_KEYWORDS,
       "set_public_party_name(name: str) -> None\n"
       "\n"
       "(internal)"},

      {"set_public_party_enabled", (PyCFunction)PySetPublicPartyEnabled,
       METH_VARARGS | METH_KEYWORDS,
       "set_public_party_enabled(enabled: bool) -> None\n"
       "\n"
       "(internal)"},

      {"get_public_party_enabled", (PyCFunction)PyGetPublicPartyEnabled,
       METH_VARARGS | METH_KEYWORDS,
       "get_public_party_enabled() -> bool\n"
       "\n"
       "(internal)"},
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica
