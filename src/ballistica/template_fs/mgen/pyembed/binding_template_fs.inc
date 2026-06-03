{
// Python code from batemplatefsmeta/pyembed/binding_template_fs.py:
const char* bindcode =
  "# Released under the MIT License. See LICENSE for details.\n"
  "\n"
  "# Where most of our python-c++ binding happens.\n"
  "# Python objects should be added here along with their associated c++ enum.\n"
  "# pylint: disable=useless-suppression, missing-module-docstring, line-too-long\n"
  "from __future__ import annotations\n"
  "\n"
  "from batemplatefs import _hooks\n"
  "\n"
  "# The C++ layer looks for this variable:\n"
  "values = [\n"
  "    _hooks.hello_world,  # kHelloWorldCall\n"
  "]\n";

// Exec the Python code in an empty context.
auto ctx = PythonRef::Stolen(PyDict_New());
bool success = PythonCommand(bindcode, "binding_template_fs.py").Exec(true, *ctx, *ctx);
if (!success) {
  FatalError("Error fetching required Python objects.");
}

// Grab the 'values' list that the binding code created.
auto bindvals = ctx.DictGetItem("values");
if (!bindvals.exists() || !PyList_Check(*bindvals)) {
  FatalError("Error binding required Python objects.");
}

// Pull our various obj_ values from the values list.
objs_.StoreCallable(ObjID::kHelloWorldCall, PyList_GET_ITEM(bindvals.get(), 0));
}
