// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_PYTHON_PYTHON_SYS_H_
#define BALLISTICA_SHARED_PYTHON_PYTHON_SYS_H_

// Any code that actually runs any Python logic should include this.
// This header pulls in the actual Python includes and also defines some handy
// macros and functions for working with Python objects.

// UPDATE (September 2024): We now include Python.h directly in some places;
// this causes less friction with include-what-you-use checks.
#include <Python.h>
#include <frameobject.h>
#include <weakrefobject.h>

#include <string>  // IWYU pragma: keep. (macros below use this)

// Saving/restoring Python error state; useful when function PyObject_Str()
// or other functionality is needed during error reporting; by default it
// craps out when an error is set.
#define BA_PYTHON_ERROR_SAVE          \
  PyObject* pes_perr = nullptr;       \
  PyObject* pes_pvalue = nullptr;     \
  PyObject* pes_ptraceback = nullptr; \
  PyErr_Fetch(&pes_perr, &pes_pvalue, &pes_ptraceback)

#define BA_PYTHON_ERROR_RESTORE \
  PyErr_Restore(pes_perr, pes_pvalue, pes_ptraceback)

// Some macros to handle/propagate C++ exceptions within Python calls.
#define BA_PYTHON_TRY \
  try {               \
  ((void)0)

// Set Python error state based on the caught C++ exception and returns null.
#define BA_PYTHON_CATCH                                                   \
  }                                                                       \
  catch (const Exception& e) {                                            \
    Python::SetPythonException(e);                                        \
    return nullptr;                                                       \
  }                                                                       \
  catch (const std::exception& e) {                                       \
    PyErr_SetString(PyExc_RuntimeError, GetShortExceptionDescription(e)); \
    return nullptr;                                                       \
  }                                                                       \
  ((void)0)

// For use in tp_new; sets Python err, frees aborted self, returns null.
#define BA_PYTHON_NEW_CATCH                                               \
  }                                                                       \
  catch (const Exception& e) {                                            \
    Python::SetPythonException(e);                                        \
    if (self) {                                                           \
      Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));          \
    }                                                                     \
    return nullptr;                                                       \
  }                                                                       \
  catch (const std::exception& e) {                                       \
    PyErr_SetString(PyExc_RuntimeError, GetShortExceptionDescription(e)); \
    if (self) {                                                           \
      Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));          \
    }                                                                     \
    return nullptr;                                                       \
  }                                                                       \
  ((void)0)

// For use in tp_dealloc; simply prints the error.
#define BA_PYTHON_DEALLOC_CATCH                                   \
  }                                                               \
  catch (const std::exception& e) {                               \
    Log(LogLevel::kError, std::string("tp_dealloc exception: ")   \
                              + GetShortExceptionDescription(e)); \
  }                                                               \
  ((void)0)

// Sets Python error and returns -1.
#define BA_PYTHON_INT_CATCH                                               \
  }                                                                       \
  catch (const Exception& e) {                                            \
    Python::SetPythonException(e);                                        \
    return -1;                                                            \
  }                                                                       \
  catch (const std::exception& e) {                                       \
    PyErr_SetString(PyExc_RuntimeError, GetShortExceptionDescription(e)); \
    return -1;                                                            \
  }                                                                       \
  ((void)0)

#endif  // BALLISTICA_SHARED_PYTHON_PYTHON_SYS_H_
