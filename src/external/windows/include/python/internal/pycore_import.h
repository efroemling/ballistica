#ifndef Py_LIMITED_API
#ifndef Py_INTERNAL_IMPORT_H
#define Py_INTERNAL_IMPORT_H
#ifdef __cplusplus
extern "C" {
#endif

#ifndef Py_BUILD_CORE
#  error "this header requires Py_BUILD_CORE define"
#endif

#include "pycore_lock.h"          // PyMutex
#include "pycore_hashtable.h"     // _Py_hashtable_t

extern int _PyImport_IsInitialized(PyInterpreterState *);

// Export for 'pyexpat' shared extension
PyAPI_FUNC(int) _PyImport_SetModule(PyObject *name, PyObject *module);

extern int _PyImport_SetModuleString(const char *name, PyObject* module);

extern void _PyImport_AcquireLock(PyInterpreterState *interp);
extern void _PyImport_ReleaseLock(PyInterpreterState *interp);
extern void _PyImport_ReInitLock(PyInterpreterState *interp);

// This is used exclusively for the sys and builtins modules:
extern int _PyImport_FixupBuiltin(
    PyThreadState *tstate,
    PyObject *mod,
    const char *name,            /* UTF-8 encoded string */
    PyObject *modules
    );

// Export for many shared extensions, like '_json'
PyAPI_FUNC(PyObject*) _PyImport_GetModuleAttr(PyObject *, PyObject *);

// Export for many shared extensions, like '_datetime'
PyAPI_FUNC(PyObject*) _PyImport_GetModuleAttrString(const char *, const char *);


struct _import_runtime_state {
    /* The builtin modules (defined in config.c). */
    struct _inittab *inittab;
    /* The most recent value assigned to a PyModuleDef.m_base.m_index.
       This is incremented each time PyModuleDef_Init() is called,
       which is just about every time an extension module is imported.
       See PyInterpreterState.modules_by_index for more info. */
    Py_ssize_t last_module_index;
    struct {
        /* A lock to guard the cache. */
        PyMutex mutex;
        /* The actual cache of (filename, name, PyModuleDef) for modules.
           Only legacy (single-phase init) extension modules are added
           and only if they support multiple initialization (m_size >- 0)
           or are imported in the main interpreter.
           This is initialized lazily in fix_up_extension() in import.c.
           Modules are added there and looked up in _imp.find_extension(). */
        _Py_hashtable_t *hashtable;
    } extensions;
    /* Package context -- the full module name for package imports */
    const char * pkgcontext;
};

struct _import_state {
    /* cached sys.modules dictionary */
    PyObject *modules;
    /* This is the list of module objects for all legacy (single-phase init)
       extension modules ever loaded in this process (i.e. imported
       in this interpreter or in any other).  Py_None stands in for
       modules that haven't actually been imported in this interpreter.

       A module's index (PyModuleDef.m_base.m_index) is used to look up
       the corresponding module object for this interpreter, if any.
       (See PyState_FindModule().)  When any extension module
       is initialized during import, its moduledef gets initialized by
       PyModuleDef_Init(), and the first time that happens for each
       PyModuleDef, its index gets set to the current value of
       a global counter (see _PyRuntimeState.imports.last_module_index).
       The entry for that index in this interpreter remains unset until
       the module is actually imported here.  (Py_None is used as
       a placeholder.)  Note that multi-phase init modules always get
       an index for which there will never be a module set.

       This is initialized lazily in PyState_AddModule(), which is also
       where modules get added. */
    PyObject *modules_by_index;
    /* importlib module._bootstrap */
    PyObject *importlib;
    /* override for config->use_frozen_modules (for tests)
       (-1: "off", 1: "on", 0: no override) */
    int override_frozen_modules;
    int override_multi_interp_extensions_check;
#ifdef HAVE_DLOPEN
    int dlopenflags;
#endif
    PyObject *import_func;
    /* The global import lock. */
    _PyRecursiveMutex lock;
    /* diagnostic info in PyImport_ImportModuleLevelObject() */
    struct {
        int import_level;
        PyTime_t accumulated;
        int header;
    } find_and_load;
};

#ifdef HAVE_DLOPEN
#  include <dlfcn.h>              // RTLD_NOW, RTLD_LAZY
#  if HAVE_DECL_RTLD_NOW
#    define _Py_DLOPEN_FLAGS RTLD_NOW
#  else
#    define _Py_DLOPEN_FLAGS RTLD_LAZY
#  endif
#  define DLOPENFLAGS_INIT .dlopenflags = _Py_DLOPEN_FLAGS,
#else
#  define _Py_DLOPEN_FLAGS 0
#  define DLOPENFLAGS_INIT
#endif

#define IMPORTS_INIT \
    { \
        DLOPENFLAGS_INIT \
        .find_and_load = { \
            .header = 1, \
        }, \
    }

extern void _PyImport_ClearCore(PyInterpreterState *interp);

extern Py_ssize_t _PyImport_GetNextModuleIndex(void);
extern const char * _PyImport_ResolveNameWithPackageContext(const char *name);
extern const char * _PyImport_SwapPackageContext(const char *newcontext);

extern int _PyImport_GetDLOpenFlags(PyInterpreterState *interp);
extern void _PyImport_SetDLOpenFlags(PyInterpreterState *interp, int new_val);

extern PyObject * _PyImport_InitModules(PyInterpreterState *interp);
extern PyObject * _PyImport_GetModules(PyInterpreterState *interp);
extern void _PyImport_ClearModules(PyInterpreterState *interp);

extern void _PyImport_ClearModulesByIndex(PyInterpreterState *interp);

extern int _PyImport_InitDefaultImportFunc(PyInterpreterState *interp);
extern int _PyImport_IsDefaultImportFunc(
        PyInterpreterState *interp,
        PyObject *func);

extern PyObject * _PyImport_GetImportlibLoader(
        PyInterpreterState *interp,
        const char *loader_name);
extern PyObject * _PyImport_GetImportlibExternalLoader(
        PyInterpreterState *interp,
        const char *loader_name);
extern PyObject * _PyImport_BlessMyLoader(
        PyInterpreterState *interp,
        PyObject *module_globals);
extern PyObject * _PyImport_ImportlibModuleRepr(
        PyInterpreterState *interp,
        PyObject *module);


extern PyStatus _PyImport_Init(void);
extern void _PyImport_Fini(void);
extern void _PyImport_Fini2(void);

extern PyStatus _PyImport_InitCore(
        PyThreadState *tstate,
        PyObject *sysmod,
        int importlib);
extern PyStatus _PyImport_InitExternal(PyThreadState *tstate);
extern void _PyImport_FiniCore(PyInterpreterState *interp);
extern void _PyImport_FiniExternal(PyInterpreterState *interp);


extern PyObject* _PyImport_GetBuiltinModuleNames(void);

struct _module_alias {
    const char *name;                 /* ASCII encoded string */
    const char *orig;                 /* ASCII encoded string */
};

// Export these 3 symbols for test_ctypes
PyAPI_DATA(const struct _frozen*) _PyImport_FrozenBootstrap;
PyAPI_DATA(const struct _frozen*) _PyImport_FrozenStdlib;
PyAPI_DATA(const struct _frozen*) _PyImport_FrozenTest;

extern const struct _module_alias * _PyImport_FrozenAliases;

extern int _PyImport_CheckSubinterpIncompatibleExtensionAllowed(
    const char *name);


// Export for '_testinternalcapi' shared extension
PyAPI_FUNC(int) _PyImport_ClearExtension(PyObject *name, PyObject *filename);

#ifdef Py_GIL_DISABLED
// Assuming that the GIL is enabled from a call to
// _PyEval_EnableGILTransient(), resolve the transient request depending on the
// state of the module argument:
// - If module is NULL or a PyModuleObject with md_gil == Py_MOD_GIL_NOT_USED,
//   call _PyEval_DisableGIL().
// - Otherwise, call _PyEval_EnableGILPermanent(). If the GIL was not already
//   enabled permanently, issue a warning referencing the module's name.
//
// This function may raise an exception.
extern int _PyImport_CheckGILForModule(PyObject *module, PyObject *module_name);
#endif

#ifdef __cplusplus
}
#endif
#endif /* !Py_INTERNAL_IMPORT_H */
#endif /* !Py_LIMITED_API */
