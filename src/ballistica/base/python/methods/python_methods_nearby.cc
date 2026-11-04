// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/python/methods/python_methods_nearby.h"

#include <string>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/base/networking/nearby_services.h"
#include "ballistica/core/core.h"
#include "ballistica/core/platform/platform.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_macros.h"
#include "ballistica/shared/python/python_ref.h"

namespace ballistica::base {

// Ignore signed bitwise warnings; python macros do it quite a bit.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"

// Everything here is for babase/_nearbyimpl.py, which calls it from its
// own network thread; none of it touches logic-thread state.

// ------------------------ nearby_broadcast_addrs -----------------------------

static auto PyNearbyBroadcastAddrs(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  std::vector<uint32_t> addrs = g_core->platform->GetBroadcastAddrs();
  PythonRef list{PyList_New(0), PythonRef::kSteal};
  for (uint32_t addr : addrs) {
    std::string str = std::to_string((addr >> 24) & 0xFF) + "."
                      + std::to_string((addr >> 16) & 0xFF) + "."
                      + std::to_string((addr >> 8) & 0xFF) + "."
                      + std::to_string(addr & 0xFF);
    PythonRef item{PyUnicode_FromString(str.c_str()), PythonRef::kSteal};
    PyList_Append(list.get(), item.get());
  }
  return list.NewRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyNearbyBroadcastAddrsDef = {
    "nearby_broadcast_addrs",             // name
    (PyCFunction)PyNearbyBroadcastAddrs,  // method
    METH_NOARGS,                          // flags

    "nearby_broadcast_addrs() -> list[str]\n"
    "\n"
    "Return the subnet broadcast address of each local IPv4 interface.\n"
    "Safe to call from any thread.\n"
    "\n"
    ":meta private:",
};

// ------------------------ nearby_service_types -------------------------------

static auto PyNearbyServiceTypes(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  return Py_BuildValue("(ss)", kNearbyGameServiceType,
                       kNearbyRemoteServiceType);
  BA_PYTHON_CATCH;
}

static PyMethodDef PyNearbyServiceTypesDef = {
    "nearby_service_types",             // name
    (PyCFunction)PyNearbyServiceTypes,  // method
    METH_NOARGS,                        // flags

    "nearby_service_types() -> tuple[str, str]\n"
    "\n"
    "Return the DNS-SD service types we advertise (game, remote).\n"
    "\n"
    ":meta private:",
};

// ----------------------- nearby_browse_supported -----------------------------

static auto PyNearbyBrowseSupported(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  if (NearbyServices::Get().BrowseSupported()) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyNearbyBrowseSupportedDef = {
    "nearby_browse_supported",             // name
    (PyCFunction)PyNearbyBrowseSupported,  // method
    METH_NOARGS,                           // flags

    "nearby_browse_supported() -> bool\n"
    "\n"
    "Whether DNS-SD service browsing works on this platform.\n"
    "\n"
    ":meta private:",
};

// ------------------------- nearby_browse_start -------------------------------

static auto PyNearbyBrowseStart(PyObject* self, PyObject* args,
                                PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* types_obj{};
  static const char* kwlist[] = {"service_types", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &types_obj)) {
    return nullptr;
  }
  std::vector<std::string> types = Python::GetStrings(types_obj);
  int fd = NearbyServices::Get().StartBrowse(types);
  return PyLong_FromLong(fd);
  BA_PYTHON_CATCH;
}

static PyMethodDef PyNearbyBrowseStartDef = {
    "nearby_browse_start",             // name
    (PyCFunction)PyNearbyBrowseStart,  // method
    METH_VARARGS | METH_KEYWORDS,      // flags

    "nearby_browse_start(service_types: list[str]) -> int\n"
    "\n"
    "Start browsing; returns a file descriptor that becomes readable\n"
    "when nearby_browse_process() has something, -2 where there's no\n"
    "descriptor (call nearby_browse_process() periodically instead), or\n"
    "-1 on failure.\n"
    "\n"
    ":meta private:",
};

// ------------------------ nearby_browse_process ------------------------------

static auto PyNearbyBrowseProcess(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  auto events = NearbyServices::Get().ProcessBrowse();
  PythonRef list{PyList_New(0), PythonRef::kSteal};
  for (auto&& event : events) {
    PythonRef txt{PyDict_New(), PythonRef::kSteal};
    for (auto&& [key, value] : event.txt) {
      PythonRef pyval{
          PyUnicode_DecodeUTF8(
              value.data(), static_cast<Py_ssize_t>(value.size()), "replace"),
          PythonRef::kSteal};
      PyDict_SetItemString(txt.get(), key.c_str(), pyval.get());
    }
    PythonRef item{Py_BuildValue("(OssssiO)", event.added ? Py_True : Py_False,
                                 event.service_type.c_str(),
                                 event.instance.c_str(), event.name.c_str(),
                                 event.address.c_str(), event.port, txt.get()),
                   PythonRef::kSteal};
    PyList_Append(list.get(), item.get());
  }
  return list.NewRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyNearbyBrowseProcessDef = {
    "nearby_browse_process",             // name
    (PyCFunction)PyNearbyBrowseProcess,  // method
    METH_NOARGS,                         // flags

    "nearby_browse_process()"
    " -> list[tuple[bool, str, str, str, str, int, dict[str, str]]]\n"
    "\n"
    "Handle pending browse results, returning events as (added,\n"
    "service-type, instance, name, address, port, txt).\n"
    "Raises if the browse has failed for good.\n"
    "\n"
    ":meta private:",
};

// -------------------------- nearby_browse_stop -------------------------------

static auto PyNearbyBrowseStop(PyObject* self) -> PyObject* {
  BA_PYTHON_TRY;
  NearbyServices::Get().StopBrowse();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

static PyMethodDef PyNearbyBrowseStopDef = {
    "nearby_browse_stop",             // name
    (PyCFunction)PyNearbyBrowseStop,  // method
    METH_NOARGS,                      // flags

    "nearby_browse_stop() -> None\n"
    "\n"
    ":meta private:",
};

// -----------------------------------------------------------------------------

auto PythonMethodsNearby::GetMethods() -> std::vector<PyMethodDef> {
  return {
      PyNearbyBroadcastAddrsDef,  PyNearbyServiceTypesDef,
      PyNearbyBrowseSupportedDef, PyNearbyBrowseStartDef,
      PyNearbyBrowseProcessDef,   PyNearbyBrowseStopDef,
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica::base
