#ifndef Py_EMSCRIPTEN_TRAMPOLINE_H
#define Py_EMSCRIPTEN_TRAMPOLINE_H

#include "pycore_runtime.h"  // _PyRuntimeState

/**
 * C function call trampolines to mitigate bad function pointer casts.
 *
 * Section 6.3.2.3, paragraph 8 reads:
 *
 *      A pointer to a function of one type may be converted to a pointer to a
 *      function of another type and back again; the result shall compare equal to
 *      the original pointer. If a converted pointer is used to call a function
 *      whose type is not compatible with the pointed-to type, the behavior is
 *      undefined.
 *
 * Typical native ABIs ignore additional arguments or fill in missing values
 * with 0/NULL in function pointer cast. Compilers do not show warnings when a
 * function pointer is explicitly casted to an incompatible type.
 *
 * Bad fpcasts are an issue in WebAssembly. WASM's indirect_call has strict
 * function signature checks. Argument count, types, and return type must match.
 *
 * Third party code unintentionally rely on problematic fpcasts. The call
 * trampoline mitigates common occurrences of bad fpcasts on Emscripten.
 */

#if defined(__EMSCRIPTEN__) && defined(PY_CALL_TRAMPOLINE)

void _Py_EmscriptenTrampoline_Init(_PyRuntimeState *runtime);

PyObject*
_PyEM_TrampolineCall_JavaScript(PyCFunctionWithKeywords func,
                                PyObject* self,
                                PyObject* args,
                                PyObject* kw);

PyObject*
_PyEM_TrampolineCall_Reflection(PyCFunctionWithKeywords func,
                                PyObject* self,
                                PyObject* args,
                                PyObject* kw);

#define _PyEM_TrampolineCall(meth, self, args, kw) \
    ((_PyRuntime.wasm_type_reflection_available) ? \
        (_PyEM_TrampolineCall_Reflection((PyCFunctionWithKeywords)(meth), (self), (args), (kw))) : \
        (_PyEM_TrampolineCall_JavaScript((PyCFunctionWithKeywords)(meth), (self), (args), (kw))))

#define _PyCFunction_TrampolineCall(meth, self, args) \
    _PyEM_TrampolineCall( \
        (*(PyCFunctionWithKeywords)(void(*)(void))(meth)), (self), (args), NULL)

#define _PyCFunctionWithKeywords_TrampolineCall(meth, self, args, kw) \
    _PyEM_TrampolineCall((meth), (self), (args), (kw))

#define descr_set_trampoline_call(set, obj, value, closure) \
    ((int)_PyEM_TrampolineCall((PyCFunctionWithKeywords)(set), (obj), (value), (PyObject*)(closure)))

#define descr_get_trampoline_call(get, obj, closure) \
    _PyEM_TrampolineCall((PyCFunctionWithKeywords)(get), (obj), (PyObject*)(closure), NULL)


#else // defined(__EMSCRIPTEN__) && defined(PY_CALL_TRAMPOLINE)

#define _Py_EmscriptenTrampoline_Init(runtime)

#define _PyCFunction_TrampolineCall(meth, self, args) \
    (meth)((self), (args))

#define _PyCFunctionWithKeywords_TrampolineCall(meth, self, args, kw) \
    (meth)((self), (args), (kw))

#define descr_set_trampoline_call(set, obj, value, closure) \
    (set)((obj), (value), (closure))

#define descr_get_trampoline_call(get, obj, closure) \
    (get)((obj), (closure))

#endif // defined(__EMSCRIPTEN__) && defined(PY_CALL_TRAMPOLINE)

#endif // ndef Py_EMSCRIPTEN_SIGNAL_H
