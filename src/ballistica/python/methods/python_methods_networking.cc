// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/methods/python_methods_networking.h"

#include <set>
#include <string>
#include <vector>

#include "ballistica/app/app_globals.h"
#include "ballistica/game/connection/connection_to_host.h"
#include "ballistica/game/game.h"
#include "ballistica/math/vector3f.h"
#include "ballistica/networking/master_server_config.h"
#include "ballistica/networking/network_reader.h"
#include "ballistica/networking/networking.h"
#include "ballistica/networking/sockaddr.h"
#include "ballistica/networking/telnet_server.h"
#include "ballistica/platform/platform.h"
#include "ballistica/python/python.h"

namespace ballistica {

// Ignore signed bitwise stuff; python macros do it quite a bit.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"

auto PyGetPublicPartyEnabled(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("getpublicpartyenabled");
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist)))
    return nullptr;
  assert(g_python);
  if (g_game->public_party_enabled()) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

auto PySetPublicPartyEnabled(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("setpublicpartyenabled");
  int enable;
  static const char* kwlist[] = {"enabled", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p",
                                   const_cast<char**>(kwlist), &enable)) {
    return nullptr;
  }
  assert(g_python);
  g_game->SetPublicPartyEnabled(static_cast<bool>(enable));
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PySetPublicPartyName(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("setpublicpartyname");
  PyObject* name_obj;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &name_obj)) {
    return nullptr;
  }
  std::string name = Python::GetPyString(name_obj);
  assert(g_python);
  g_game->SetPublicPartyName(name);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PySetPublicPartyStatsURL(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("setpublicpartystatsurl");
  PyObject* url_obj;
  static const char* kwlist[] = {"url", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &url_obj)) {
    return nullptr;
  }
  // The call expects an empty string for the no-url option.
  std::string url = (url_obj == Py_None) ? "" : Python::GetPyString(url_obj);
  assert(g_python);
  g_game->SetPublicPartyStatsURL(url);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyGetPublicPartyMaxSize(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("getpublicpartymaxsize");
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  assert(g_python);
  return PyLong_FromLong(g_game->public_party_max_size());
  BA_PYTHON_CATCH;
}

auto PySetPublicPartyMaxSize(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("setpublicpartymaxsize");
  int max_size;
  static const char* kwlist[] = {"max_size", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "i",
                                   const_cast<char**>(kwlist), &max_size)) {
    return nullptr;
  }
  assert(g_python);
  g_game->SetPublicPartyMaxSize(max_size);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PySetAuthenticateClients(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("set_authenticate_clients");
  int enable;
  static const char* kwlist[] = {"enable", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p",
                                   const_cast<char**>(kwlist), &enable)) {
    return nullptr;
  }
  assert(g_game);
  g_game->set_require_client_authentication(static_cast<bool>(enable));
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PySetAdmins(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("set_admins");
  PyObject* admins_obj;
  static const char* kwlist[] = {"admins", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &admins_obj)) {
    return nullptr;
  }
  assert(g_game);

  auto admins = Python::GetPyStrings(admins_obj);
  std::set<std::string> adminset;
  for (auto&& admin : admins) {
    adminset.insert(admin);
  }
  g_game->set_admin_public_ids(adminset);

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PySetEnableDefaultKickVoting(PyObject* self, PyObject* args,
                                  PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("set_enable_default_kick_voting");
  int enable;
  static const char* kwlist[] = {"enable", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p",
                                   const_cast<char**>(kwlist), &enable)) {
    return nullptr;
  }
  assert(g_game);
  g_game->set_kick_voting_enabled(static_cast<bool>(enable));
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyConnectToParty(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("connect_to_party");
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
    ScreenMessage(g_game->GetResourceString("invalidAddressErrorText"),
                  {1, 0, 0});
    Py_RETURN_NONE;
  }
  g_game->PushHostConnectedUDPCall(s, static_cast<bool>(print_progress));
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyAcceptPartyInvitation(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("accept_party_invitation");
  const char* invite_id;
  static const char* kwlist[] = {"invite_id", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &invite_id)) {
    return nullptr;
  }
  g_platform->AndroidGPGSPartyInviteAccept(invite_id);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyGetGooglePlayPartyClientCount(PyObject* self, PyObject* args,
                                     PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_google_play_party_client_count");
  BA_PRECONDITION(InGameThread());
#if BA_GOOGLE_BUILD
  return PyLong_FromLong(g_game->GetGooglePlayClientCount());
#else
  return PyLong_FromLong(0);
#endif
  BA_PYTHON_CATCH;
}

auto PyClientInfoQueryResponse(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("client_info_query_response");
  const char* token;
  PyObject* response_obj;
  static const char* kwlist[] = {"token", "response", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "sO",
                                   const_cast<char**>(kwlist), &token,
                                   &response_obj)) {
    return nullptr;
  }
  g_game->SetClientInfoFromMasterServer(token, response_obj);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyGetConnectionToHostInfo(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_connection_to_host_info");
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  ConnectionToHost* hc = g_game->connection_to_host();
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
  Platform::SetLastPyCall("disconnect_from_host");
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  g_game->PushDisconnectFromHostCall();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyDisconnectClient(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("disconnect_client");
  int client_id;
  int ban_time = 300;  // Old default before we exposed this.
  static const char* kwlist[] = {"client_id", "ban_time", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "i|i",
                                   const_cast<char**>(kwlist), &client_id,
                                   &ban_time)) {
    return nullptr;
  }
  bool kickable = g_game->DisconnectClient(client_id, ban_time);
  if (kickable) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

auto PyGetGamePort(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_game_port");
  int port = 0;
  if (g_network_reader != nullptr) {
    // hmmm; we're just fetching the ipv4 port here;
    // 6 could be different....
    port = g_network_reader->port4();
  }
  return Py_BuildValue("i", port);
  BA_PYTHON_CATCH;
}

auto PyGetMasterServerAddress(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("get_master_server_address");
  int source = -1;  // use default..
  if (!PyArg_ParseTuple(args, "|i", &source)) {
    return nullptr;
  }
  // source -1 implies to use current one
  if (source == -1) {
    source = g_app_globals->master_server_source;
  }
  const char* addr;
  if (source == 0) {
    addr = BA_MASTER_SERVER_DEFAULT_ADDR;
  } else if (source == 1) {
    addr = BA_MASTER_SERVER_FALLBACK_ADDR;
  } else {
    BA_LOG_ONCE("Error: Got unexpected source: " + std::to_string(source)
                + ".");
    addr = BA_MASTER_SERVER_FALLBACK_ADDR;
  }
  return PyUnicode_FromString(addr);
  BA_PYTHON_CATCH;
}

auto PySetMasterServerSource(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("set_master_server_source");
  int source;
  if (!PyArg_ParseTuple(args, "i", &source)) return nullptr;
  if (source != 0 && source != 1) {
    BA_LOG_ONCE("Error: Invalid server source: " + std::to_string(source)
                + ".");
    source = 1;
  }
  g_app_globals->master_server_source = source;
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PySetTelnetAccessEnabled(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("set_telnet_access_enabled");
  assert(InGameThread());
  int enable;
  static const char* kwlist[] = {"enable", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "p",
                                   const_cast<char**>(kwlist), &enable)) {
    return nullptr;
  }
  if (g_app_globals->telnet_server) {
    g_app_globals->telnet_server->SetAccessEnabled(static_cast<bool>(enable));
  } else {
    throw Exception("Telnet server not enabled.");
  }
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyHostScanCycle(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("host_scan_cycle");
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
  Platform::SetLastPyCall("end_host_scanning");
  g_networking->EndHostScanning();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyHaveConnectedClients(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("have_connected_clients");
  if (g_game->GetConnectedClientCount() > 0) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

auto PyInvitePlayers(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  Platform::SetLastPyCall("invite_players");
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  g_platform->AndroidGPGSPartyInvitePlayers();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

PyMethodDef PythonMethodsNetworking::methods_def[] = {
    {"invite_players", (PyCFunction)PyInvitePlayers,
     METH_VARARGS | METH_KEYWORDS,
     "invite_players() -> None\n"
     "\n"
     "(internal)"
     "\n"
     "Category: General Utility Functions"},

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

    {"get_master_server_address", PyGetMasterServerAddress, METH_VARARGS,
     "get_master_server_address(source: int = -1) -> str\n"
     "\n"
     "(internal)\n"
     "\n"
     "Return the address of the master server."},

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

    {"get_google_play_party_client_count",
     (PyCFunction)PyGetGooglePlayPartyClientCount, METH_VARARGS | METH_KEYWORDS,
     "get_google_play_party_client_count() -> int\n"
     "\n"
     "(internal)"},

    {"accept_party_invitation", (PyCFunction)PyAcceptPartyInvitation,
     METH_VARARGS | METH_KEYWORDS,
     "accept_party_invitation(invite_id: str) -> None\n"
     "\n"
     "(internal)"},

    {"connect_to_party", (PyCFunction)PyConnectToParty,
     METH_VARARGS | METH_KEYWORDS,
     "connect_to_party(address: str, port: int = None,\n"
     "  print_progress: bool = True) -> None\n"
     "\n"
     "(internal)"},

    {"set_authenticate_clients", (PyCFunction)PySetAuthenticateClients,
     METH_VARARGS | METH_KEYWORDS,
     "set_authenticate_clients(enable: bool) -> None\n"
     "\n"
     "(internal)"},

    {"set_admins", (PyCFunction)PySetAdmins, METH_VARARGS | METH_KEYWORDS,
     "set_admins(admins: List[str]) -> None\n"
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

    {"get_public_party_max_size", (PyCFunction)PyGetPublicPartyMaxSize,
     METH_VARARGS | METH_KEYWORDS,
     "get_public_party_max_size() -> int\n"
     "\n"
     "(internal)"},

    {"set_public_party_stats_url", (PyCFunction)PySetPublicPartyStatsURL,
     METH_VARARGS | METH_KEYWORDS,
     "set_public_party_stats_url(url: Optional[str]) -> None\n"
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

    {nullptr, nullptr, 0, nullptr}};

#pragma clang diagnostic pop

}  // namespace ballistica
