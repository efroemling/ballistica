// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/python/class/python_class_lang_str.h"

#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/base/python/base_python.h"

namespace ballistica::base {

void PythonClassLangStr::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  cls->tp_name = "babase.LangStr";
  cls->tp_basicsize = sizeof(PythonClassLangStr);
  cls->tp_doc =
      "LangStr(json: str, packages: Sequence[str] | None = None,\n"
      "        wrap: tuple[int, int | None, int | None] | None = None)\n"
      "\n"
      "A deferred, language-agnostic complex string (native).\n"
      "\n"
      "The verified-local counterpart of\n"
      ":class:`bacommon.langstr.LangStrSpec` (see the D28 semantic\n"
      "split -- holding one of these implies displayability here):\n"
      "holds tokens, not text, and evaluates to a flat string in the\n"
      "client's locale at display time. Construct from the canonical\n"
      "wire JSON of any language-string form; pass the payload's\n"
      "``packages`` manifest to bind integer-indexed values at parse,\n"
      "and optionally a ``wrap`` triple (min-lines, max-lines,\n"
      "max-chars-per-line; None = unlimited) as a usage-site override\n"
      "of the string's definition-time line-wrapping. Immutable, with\n"
      "content equality and hashing. Accepted anywhere\n"
      "``str | babase.Lstr`` is accepted for display.";
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
  cls->tp_richcompare = (richcmpfunc)tp_richcompare;
  cls->tp_hash = (hashfunc)tp_hash;
  cls->tp_methods = tp_methods;
  cls->tp_getset = tp_getsets;
}

auto PythonClassLangStr::Create(std::shared_ptr<const LangStr> value)
    -> PyObject* {
  assert(value != nullptr);
  assert(TypeIsSetUp(&type_obj));
  assert(Python::HaveGIL());
  // Hand the value to tp_new via the pending slot (GIL-serialized).
  auto pending =
      std::make_unique<std::shared_ptr<const LangStr>>(std::move(value));
  s_pending_value_ = pending.get();
  auto* obj = reinterpret_cast<PythonClassLangStr*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  s_pending_value_ = nullptr;
  if (!obj) {
    throw Exception("babase.LangStr creation failed.");
  }
  return reinterpret_cast<PyObject*>(obj);
}

auto PythonClassLangStr::tp_new(PyTypeObject* type, PyObject* args,
                                PyObject* keywds) -> PyObject* {
  auto* self = reinterpret_cast<PythonClassLangStr*>(type->tp_alloc(type, 0));
  if (!self) {
    return nullptr;
  }
  BA_PYTHON_TRY;
  // Native-side Create() path: adopt the pending value.
  if (s_pending_value_ != nullptr) {
    self->value_ =
        new std::shared_ptr<const LangStr>(std::move(*s_pending_value_));
    return reinterpret_cast<PyObject*>(self);
  }
  // Python-side construction from canonical wire JSON, optionally
  // binding indexed nodes against a payload's package manifest and/or
  // attaching a usage-site wrap override.
  const char* json;
  PyObject* packages_obj{Py_None};
  PyObject* wrap_obj{Py_None};
  static const char* kwlist[] = {"json", "packages", "wrap", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s|OO",
                                   const_cast<char**>(kwlist), &json,
                                   &packages_obj, &wrap_obj)) {
    return nullptr;
  }
  std::vector<std::string> packages;
  bool have_packages{packages_obj != Py_None};
  if (have_packages) {
    packages = Python::GetStrings(packages_obj);
  }
  auto parsed = LangStr::FromJson(json, have_packages ? &packages : nullptr);
  if (!parsed.has_value()) {
    throw Exception("Invalid language-string json: " + parsed.error(),
                    PyExcType::kValue);
  }
  if (wrap_obj != Py_None) {
    // A (min_lines, max_lines | None, max_chars_per_line | None)
    // triple; None maps to the engine's 0-means-unlimited sentinel.
    auto seq = PythonRef::Stolen(
        PySequence_Fast(wrap_obj, "wrap must be a 3-item sequence"));
    if (!seq.exists() || PySequence_Fast_GET_SIZE(seq.get()) != 3) {
      PyErr_Clear();
      throw Exception("wrap must be a 3-item sequence.", PyExcType::kValue);
    }
    auto getint = [&seq](int i, int none_val) {
      PyObject* item = PySequence_Fast_GET_ITEM(seq.get(), i);
      return item == Py_None ? none_val
                             : static_cast<int>(Python::GetInt(item));
    };
    LangStrWrap wrapval;
    wrapval.min_lines = getint(0, 1);
    wrapval.max_lines = getint(1, 0);
    wrapval.max_chars_per_line = getint(2, 0);
    // Values are immutable-by-convention; this pre-publish tweak of
    // our freshly-parsed private copy is the sanctioned exception.
    const_cast<LangStr*>(parsed->get())->wrap = wrapval;
  }
  self->value_ = new std::shared_ptr<const LangStr>(std::move(*parsed));
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

void PythonClassLangStr::tp_dealloc(PythonClassLangStr* self) {
  // Atomic refcount; any thread may release.
  delete self->value_;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

auto PythonClassLangStr::tp_repr(PythonClassLangStr* self) -> PyObject* {
  BA_PYTHON_TRY;
  auto* val = self->value_ ? self->value_->get() : nullptr;
  return Py_BuildValue("s",
                       (std::string("<babase.LangStr ")
                        + (val ? val->ToJson() : std::string("(empty)")) + ">")
                           .c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassLangStr::tp_richcompare(PythonClassLangStr* self,
                                        PyObject* other, int op) -> PyObject* {
  if (op != Py_EQ && op != Py_NE) {
    Py_RETURN_NOTIMPLEMENTED;
  }
  if (!Check(other)) {
    Py_RETURN_NOTIMPLEMENTED;
  }
  auto& otherval = *reinterpret_cast<PythonClassLangStr*>(other);
  bool eq = self->value()->Equals(*otherval.value());
  if (op == Py_NE) {
    eq = !eq;
  }
  if (eq) {
    Py_RETURN_TRUE;
  }
  Py_RETURN_FALSE;
}

auto PythonClassLangStr::tp_hash(PythonClassLangStr* self) -> Py_hash_t {
  auto hashval = static_cast<Py_hash_t>(self->value()->Hash());
  // CPython reserves -1 for errors.
  return hashval == -1 ? -2 : hashval;
}

auto PythonClassLangStr::Evaluate(PythonClassLangStr* self) -> PyObject* {
  BA_PYTHON_TRY;
  return PyUnicode_FromString(self->value()->Evaluate().c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassLangStr::ToJson(PythonClassLangStr* self) -> PyObject* {
  BA_PYTHON_TRY;
  return PyUnicode_FromString(self->value()->ToJson().c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassLangStr::ToResourceJson(PythonClassLangStr* self) -> PyObject* {
  BA_PYTHON_TRY;
  auto result = self->value()->ToResourceJson();
  if (!result.has_value()) {
    throw Exception("Cannot convert to resource form: " + result.error(),
                    PyExcType::kValue);
  }
  return PyUnicode_FromString(result->c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassLangStr::FromText(PyObject* cls, PyObject* arg) -> PyObject* {
  BA_PYTHON_TRY;
  if (!PyUnicode_Check(arg)) {
    throw Exception("Expected a str.", PyExcType::kType);
  }
  Py_ssize_t size;
  const char* utf8 = PyUnicode_AsUTF8AndSize(arg, &size);
  if (utf8 == nullptr) {
    throw Exception("Unable to decode str.", PyExcType::kValue);
  }
  // Double every brace so any {token}-shaped run in the caller's text
  // survives evaluation untouched ({{ -> { and }} -> } at eval time).
  // The result is a pure literal value form: no subs, no package.
  std::string doubled;
  doubled.reserve(static_cast<size_t>(size));
  for (Py_ssize_t i = 0; i < size; ++i) {
    char c = utf8[i];
    if (c == '{') {
      doubled += "{{";
    } else if (c == '}') {
      doubled += "}}";
    } else {
      doubled += c;
    }
  }
  auto ls = std::make_shared<LangStr>();
  ls->form = LangStr::Form::kValue;
  ls->value = std::move(doubled);
  return Create(std::move(ls));
  BA_PYTHON_CATCH;
}

auto PythonClassLangStr::GetSpec(PythonClassLangStr* self, void* closure)
    -> PyObject* {
  BA_PYTHON_TRY;
  auto json = self->value()->ToResourceJson();
  if (!json.has_value()) {
    throw Exception("Cannot project to spec form: " + json.error(),
                    PyExcType::kValue);
  }
  auto spec = g_base->python->MakeLangStrSpecFromJson(*json);
  if (!spec.exists()) {
    throw Exception("LangStrSpec construction failed.", PyExcType::kRuntime);
  }
  return spec.NewRef();
  BA_PYTHON_CATCH;
}

std::shared_ptr<const LangStr>* PythonClassLangStr::s_pending_value_ = nullptr;
PyTypeObject PythonClassLangStr::type_obj;
PyMethodDef PythonClassLangStr::tp_methods[] = {
    {"from_text", (PyCFunction)FromText, METH_O | METH_CLASS,
     "from_text(text: str) -> babase.LangStr\n"
     "\n"
     "Wrap a plain string as a literal language-string.\n"
     "\n"
     "The text is shown exactly as given in every locale -- any\n"
     "``{`` or ``}`` displays literally, with no substitution. Use\n"
     "this to pass a piece of already-final text (a name a mod\n"
     "supplied, a value with no translation entry) through an API\n"
     "that wants a :class:`~babase.LangStr`. Anything that needs\n"
     "substitutions or translation should be an authored\n"
     "asset-package entry instead, so its arguments are type-checked.\n"},
    {"evaluate", (PyCFunction)Evaluate, METH_NOARGS,
     "evaluate() -> str\n"
     "\n"
     "Evaluate to flat display text in the client's locale.\n"
     "\n"
     "Fail-visible: structural problems yield a ``LANGSTR_ERROR:...``\n"
     "sentinel string (with a logged warning) rather than raising.\n"},
    {"to_json", (PyCFunction)ToJson, METH_NOARGS,
     "to_json() -> str\n"
     "\n"
     "Return the canonical wire JSON for this language-string.\n"},
    {"to_resource_json", (PyCFunction)ToResourceJson, METH_NOARGS,
     "to_resource_json() -> str\n"
     "\n"
     "Return wire JSON for the self-describing resource-form\n"
     "projection of this language-string (bound indexed nodes convert\n"
     "via the native language tables). For persisting values beyond\n"
     "their payload's package-index context. Raises ValueError for\n"
     "unbound/unknown indexed nodes.\n"},
    {nullptr}};
PyGetSetDef PythonClassLangStr::tp_getsets[] = {
    {const_cast<char*>("spec"), (getter)GetSpec, nullptr,
     const_cast<char*>(
         "spec: bacommon.langstr.LangStrSpec\n"
         "\n"
         "The authoring-spec projection of this verified-local string.\n"
         "\n"
         "Projecting verified -> spec is always valid (the reverse is\n"
         "deliberately not offered; see the D28 semantic split). Use this\n"
         "when feeding a wrapper string into spec-typed surfaces such as\n"
         "doc-ui models or client-effects. Content-only: any usage-site\n"
         "line-wrap override does not carry into the spec.\n"),
     nullptr},
    {nullptr}};

}  // namespace ballistica::base
