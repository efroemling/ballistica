# Released under the MIT License. See LICENSE for details.
#
"""Codegen for the typed Android JNI message bus.

Reads a spec module (babasemeta.android_messages) describing typed
messages between Java and C++, and emits:

* ``BallisticaJniBridge.java`` — JNI sender natives, outbound handler
  interface, and outbound JNI entry points.
* ``android_messages_decl.inc`` — C++ inbound handler abstract base,
  outbound sender class, install/setter declarations.
* ``android_messages_impl.inc`` — C++ inbound trampolines, JNI native
  method table, outbound sender bodies, install/setter definitions.

The two ``.inc`` files are ``#include``d from a hand-written ``.h``
and ``.cc`` pair under ``src/ballistica/base/platform/android/``.
Adding a new message regenerates these and forces every implementer
of ``AndroidInboundHandler`` (C++) / ``BallisticaJniBridge.OutboundHandler``
(Java) to provide the new method — missing implementations are compile
errors.
"""

from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass, field
from enum import Enum

# Type definitions used by both this codegen module and the per-
# project spec under `src/meta/<featureset>meta/android_messages.py`.
# These live HERE (in tools/, always present) rather than in the
# featureset spec module so that spinoff projects which omit the
# owning featureset still type-check this file cleanly. The spec
# imports these names from this module.


class Dir(Enum):
    """Message direction."""

    JAVA_TO_NATIVE = 'j2n'
    NATIVE_TO_JAVA = 'n2j'


# Field type tokens. Strings (not Python types) so we can extend
# later (e.g. bytes-with-length-hint) without breaking the spec.
INT = 'int'
FLOAT = 'float'
BOOL = 'bool'
STR = 'str'
BYTES = 'bytes'
STR_LIST = 'list[str]'

ALL_TYPES = {INT, FLOAT, BOOL, STR, BYTES, STR_LIST}


@dataclass
class Field:
    """A single typed payload field on a Message."""

    name: str
    type: str


@dataclass
class Message:
    """A single typed message between Java and C++."""

    name: str
    direction: Dir
    fields: list[Field] = field(default_factory=list)
    doc: str = ''


# ---------------------------------------------------------------- types

# Spec type token -> Java method param type.
_JAVA_TYPE: dict[str, str] = {
    'int': 'int',
    'float': 'float',
    'bool': 'boolean',
    'str': 'String',
    'bytes': 'byte[]',
    'list[str]': 'String[]',
}

# Spec type token -> JNI signature char (or compound).
_JNI_SIG: dict[str, str] = {
    'int': 'I',
    'float': 'F',
    'bool': 'Z',
    'str': 'Ljava/lang/String;',
    'bytes': '[B',
    'list[str]': '[Ljava/lang/String;',
}

# Spec type token -> C++ param type for handler/sender method.
_CPP_PARAM: dict[str, str] = {
    'int': 'int',
    'float': 'float',
    'bool': 'bool',
    'str': 'const std::string&',
    'bytes': 'const std::vector<uint8_t>&',
    'list[str]': 'const std::vector<std::string>&',
}

# Spec type token -> JNI C type for trampoline / Call*Method args.
_JNI_CTYPE: dict[str, str] = {
    'int': 'jint',
    'float': 'jfloat',
    'bool': 'jboolean',
    'str': 'jstring',
    'bytes': 'jbyteArray',
    'list[str]': 'jobjectArray',
}


# ---------------------------------------------------------------- helpers


def _snake_to_lower_camel(snake: str) -> str:
    parts = snake.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])


def _upper_camel_to_snake(name: str) -> str:
    """`MusicPlay` -> `music_play`. Doesn't handle acronyms cleverly."""
    out: list[str] = []
    for i, ch in enumerate(name):
        if i > 0 and ch.isupper():
            out.append('_')
        out.append(ch.lower())
    return ''.join(out)


def _method_id_member(msg_name: str) -> str:
    """Field name for the cached jmethodID of an outbound message."""
    return f'{_upper_camel_to_snake(msg_name)}_method_id_'


def _jni_signature(fields: list[Field], return_sig: str = 'V') -> str:
    return '(' + ''.join(_JNI_SIG[f.type] for f in fields) + ')' + return_sig


def _load_spec(projroot: str) -> list[Message]:
    """Import the spec module and return its MESSAGES list."""

    sys.path.insert(0, os.path.abspath(os.path.join(projroot, 'src/meta')))
    try:
        # Avoid cached import in tests.
        if 'babasemeta.android_messages' in sys.modules:
            importlib.reload(sys.modules['babasemeta.android_messages'])
        mod = importlib.import_module('babasemeta.android_messages')
    finally:
        sys.path.pop(0)
    return list(mod.MESSAGES)


def _validate(messages: list[Message]) -> None:
    """Sanity-check the spec; raise on problems."""

    seen: set[str] = set()
    for msg in messages:
        if not msg.name or not msg.name[0].isupper():
            raise ValueError(f'Message name {msg.name!r} must be UpperCamel.')
        if msg.name in seen:
            raise ValueError(f'Duplicate message name: {msg.name}.')
        seen.add(msg.name)
        field_names: set[str] = set()
        for fld in msg.fields:
            if fld.type not in ALL_TYPES:
                raise ValueError(
                    f'Unknown field type {fld.type!r} on '
                    f'{msg.name}.{fld.name}.'
                )
            if fld.name in field_names:
                raise ValueError(
                    f'Duplicate field name {fld.name} on {msg.name}.'
                )
            field_names.add(fld.name)


# ---------------------------------------------------------------- Java


_JAVA_HEADER = '''\
// Released under the MIT License. See LICENSE for details.
//
// AUTO-GENERATED by `tools/pcommand gen_android_message_java`.
// Do not edit by hand; see src/meta/babasemeta/android_messages.py.

package com.ericfroemling.ballistica.mgen;

import androidx.annotation.Keep;

import com.ericfroemling.ballistica.BallisticaContext;

/** Typed Java<->C++ message bus for Android. */
public final class BallisticaJniBridge {
  private BallisticaJniBridge() {}

  // J->N send-deferral: messages sent before C++ is ready get
  // queued and replayed once markReady() fires. Matches the
  // legacy nativeCommand* wrappers' "if (_nativeInited) ... else
  // _deferredNativeCommands.add(...)" pattern, but centralized in
  // the bus instead of repeated at every call site.
  private static volatile boolean sReady = false;
  private static final java.util.List<Runnable> sDeferred =
      new java.util.LinkedList<>();

  /** Called once from BallisticaContext.onNativeInitComplete(). */
  public static synchronized void markReady() {
    sReady = true;
    for (Runnable r : sDeferred) {
      r.run();
    }
    sDeferred.clear();
  }

  private static synchronized void deferOrCall(Runnable r) {
    if (sReady) {
      r.run();
    } else {
      sDeferred.add(r);
    }
  }

'''

_JAVA_FOOTER = '''\
}
'''


def _emit_java(messages: list[Message]) -> str:

    out: list[str] = [_JAVA_HEADER]

    # Section 1: J->N sender natives.
    j2n = [m for m in messages if m.direction is Dir.JAVA_TO_NATIVE]
    n2j = [m for m in messages if m.direction is Dir.NATIVE_TO_JAVA]

    out.append(
        '  // J->N typed senders. Each public method either calls\n'
        '  // its JNI impl directly (when sReady) or queues a\n'
        '  // Runnable that does so on markReady(). The Impl is\n'
        '  // the actual native binding registered via JNI_OnLoad.\n\n'
    )
    for msg in j2n:
        params = ', '.join(
            f'{_JAVA_TYPE[f.type]} {_snake_to_lower_camel(f.name)}'
            for f in msg.fields
        )
        arg_names = [_snake_to_lower_camel(f.name) for f in msg.fields]
        call_args = ', '.join(arg_names)
        impl_name = f'nativeSend{msg.name}Impl'
        if msg.fields:
            # Lambda captures the (effectively final) args.
            defer_body = f'() -> {impl_name}({call_args})'
        else:
            defer_body = f'BallisticaJniBridge::{impl_name}'
        if msg.doc:
            out.append(f'  /** {msg.doc} */\n')
        out.append(
            f'  public static void nativeSend{msg.name}({params}) {{\n'
            f'    if (sReady) {{\n'
            f'      {impl_name}({call_args});\n'
            f'    }} else {{\n'
            f'      deferOrCall({defer_body});\n'
            f'    }}\n'
            f'  }}\n'
            f'  private static native void {impl_name}({params});\n\n'
        )

    # Section 2: N->J handler interface.
    out.append(
        '  // N->J handler interface. Implemented by\n'
        '  // BallisticaContext (or whoever else needs to\n'
        '  // receive native->Java messages). Adding a new\n'
        '  // N->J message forces every implementer to add the\n'
        '  // matching onXxx method or fail to compile.\n'
        '  public interface OutboundHandler {\n'
    )
    for msg in n2j:
        params = ', '.join(
            f'{_JAVA_TYPE[f.type]} {_snake_to_lower_camel(f.name)}'
            for f in msg.fields
        )
        method = f'on{msg.name}'
        if msg.doc:
            out.append(f'    /** {msg.doc} */\n')
        out.append(f'    void {method}({params});\n')
    if not n2j:
        out.append('    // (no N->J messages yet)\n')
    out.append('  }\n\n')

    out.append(
        '  private static volatile OutboundHandler sOutboundHandler;\n'
        '  public static void setOutboundHandler(OutboundHandler h) {\n'
        '    sOutboundHandler = h;\n'
        '  }\n\n'
    )

    # Section 3: N->J JNI entry points (called by C++).
    out.append(
        '  // N->J JNI entry points. C++ calls these via\n'
        '  // GetStaticMethodID + CallStaticVoidMethod. Each\n'
        '  // dispatches to the active handler on the UI thread\n'
        '  // (matches legacy miscAndroidCommand* behavior).\n\n'
    )
    for msg in n2j:
        camel_params = [
            (_JAVA_TYPE[f.type], _snake_to_lower_camel(f.name))
            for f in msg.fields
        ]
        sig_params = ', '.join(f'final {t} {n}' for t, n in camel_params)
        call_params = ', '.join(n for _, n in camel_params)
        method = f'fromNative{msg.name}'
        on_method = f'on{msg.name}'
        out.append(
            f'  @Keep\n'
            f'  public static void {method}({sig_params}) {{\n'
            f'    final OutboundHandler h = sOutboundHandler;\n'
            f'    if (h == null) {{\n'
            f'      android.util.Log.e("BA",\n'
            f'          "{method}: no OutboundHandler installed");\n'
            f'      return;\n'
            f'    }}\n'
            f'    final BallisticaContext ctx_ =\n'
            f'        BallisticaContext.getActive();\n'
            f'    if (ctx_ == null) {{\n'
            f'      android.util.Log.e("BA",\n'
            f'          "{method}: no active BallisticaContext");\n'
            f'      return;\n'
            f'    }}\n'
            f'    ctx_.getActivity().runOnUiThread(\n'
            f'        () -> h.{on_method}({call_params}));\n'
            f'  }}\n\n'
        )

    out.append(_JAVA_FOOTER)
    return ''.join(out)


# ---------------------------------------------------------------- C++


_CPP_DECL_HEADER = '''\
// Released under the MIT License. See LICENSE for details.
//
// AUTO-GENERATED by `tools/pcommand gen_android_message_cpp`.
// Do not edit by hand; see src/meta/babasemeta/android_messages.py.
//
// Included inside `namespace ballistica::base` (inside
// `#if BA_PLATFORM_ANDROID`) by android_message_bus.h.

'''

_CPP_IMPL_HEADER = '''\
// Released under the MIT License. See LICENSE for details.
//
// AUTO-GENERATED by `tools/pcommand gen_android_message_cpp`.
// Do not edit by hand; see src/meta/babasemeta/android_messages.py.
//
// Included once inside `namespace ballistica::base` (inside
// `#if BA_PLATFORM_ANDROID`) by android_message_bus.cc.

'''


def _emit_cpp_decl(messages: list[Message]) -> str:

    j2n = [m for m in messages if m.direction is Dir.JAVA_TO_NATIVE]
    n2j = [m for m in messages if m.direction is Dir.NATIVE_TO_JAVA]

    out: list[str] = [_CPP_DECL_HEADER]

    # Inbound abstract handler.
    out.append(
        '// Inbound (J->N) handler. PlatformAndroid (or a\n'
        '// delegate it owns) subclasses this. Missing override\n'
        '// on a new message = compile error.\n'
        'class AndroidInboundHandler {\n'
        ' public:\n'
        '  virtual ~AndroidInboundHandler() = default;\n'
    )
    for msg in j2n:
        params = ', '.join(f'{_CPP_PARAM[f.type]} {f.name}' for f in msg.fields)
        if msg.doc:
            out.append(f'  /// {msg.doc}\n')
        out.append(f'  virtual void On{msg.name}({params}) = 0;\n')
    if not j2n:
        out.append('  // (no J->N messages yet)\n')
    out.append('};\n\n')

    # Outbound sender.
    out.append(
        '// Outbound (N->J) sender. Owned by PlatformAndroid;\n'
        '// populated at JNI_OnLoad with the bridge jclass and\n'
        '// per-method jmethodID values.\n'
        'class AndroidMessageSender {\n'
        ' public:\n'
    )
    for msg in n2j:
        params = ', '.join(f'{_CPP_PARAM[f.type]} {f.name}' for f in msg.fields)
        if msg.doc:
            out.append(f'  /// {msg.doc}\n')
        out.append(f'  void Send{msg.name}({params});\n')
    if not n2j:
        out.append('  // (no N->J messages yet)\n')
    out.append(' private:\n  jclass jbridge_class_{};\n')
    for msg in n2j:
        out.append(f'  jmethodID {_method_id_member(msg.name)}{{}};\n')
    out.append(
        '  friend auto InstallAndroidMessageBus(JNIEnv* env) -> jint;\n'
        '};\n\n'
    )

    out.append(
        '// Bind both directions during JNI_OnLoad. Returns\n'
        '// JNI_OK on success, JNI_ERR if the bridge class or\n'
        '// any method cannot be resolved.\n'
        'auto InstallAndroidMessageBus(JNIEnv* env) -> jint;\n\n'
        '// Process-singleton sender. Valid after\n'
        '// InstallAndroidMessageBus succeeds.\n'
        'auto GetAndroidMessageSender() -> AndroidMessageSender*;\n\n'
        '// Install the active inbound handler. Call once after\n'
        '// PlatformAndroid is constructed.\n'
        'void SetAndroidInboundHandler(AndroidInboundHandler* h);\n'
    )

    return ''.join(out)


def _emit_sender_marshal(
    fields: list[Field],
) -> tuple[list[str], list[str], list[str]]:
    """Emit C++ marshalling for one outbound message's fields.

    Returns (marshal_lines, cleanup_lines, call_args). The marshal
    block runs before CallStaticVoidMethod; cleanup runs after; the
    call args are what gets passed to CallStaticVoidMethod.
    """
    marshal_lines: list[str] = []
    cleanup_lines: list[str] = []
    call_args: list[str] = []
    for f in fields:
        if f.type in ('int', 'float', 'bool'):
            cast = {'int': 'jint', 'float': 'jfloat', 'bool': 'jboolean'}[
                f.type
            ]
            call_args.append(f'static_cast<{cast}>({f.name})')
        elif f.type == 'str':
            marshal_lines.append(f'  jstring j_{f.name} =')
            marshal_lines.append(f'      env->NewStringUTF({f.name}.c_str());')
            cleanup_lines.append(f'  env->DeleteLocalRef(j_{f.name});')
            call_args.append(f'j_{f.name}')
        elif f.type == 'bytes':
            marshal_lines.append(
                f'  jbyteArray j_{f.name} = env->NewByteArray('
            )
            marshal_lines.append(f'      static_cast<jsize>({f.name}.size()));')
            marshal_lines.append(f'  if ({f.name}.size() > 0) {{')
            marshal_lines.append('    env->SetByteArrayRegion(')
            marshal_lines.append(f'        j_{f.name}, 0,')
            marshal_lines.append(
                f'        static_cast<jsize>({f.name}.size()),'
            )
            marshal_lines.append(
                f'        reinterpret_cast<const jbyte*>(' f'{f.name}.data()));'
            )
            marshal_lines.append('  }')
            cleanup_lines.append(f'  env->DeleteLocalRef(j_{f.name});')
            call_args.append(f'j_{f.name}')
        elif f.type == 'list[str]':
            marshal_lines.append(f'  jclass j_string_cls_{f.name} =')
            marshal_lines.append('      env->FindClass("java/lang/String");')
            marshal_lines.append(
                f'  jobjectArray j_{f.name} = env->NewObjectArray('
            )
            marshal_lines.append(f'      static_cast<jsize>({f.name}.size()),')
            marshal_lines.append(f'      j_string_cls_{f.name}, nullptr);')
            marshal_lines.append(
                f'  for (size_t i = 0; i < {f.name}.size(); ++i) {{'
            )
            marshal_lines.append(
                f'    jstring s = env->NewStringUTF(' f'{f.name}[i].c_str());'
            )
            marshal_lines.append(f'    env->SetObjectArrayElement(j_{f.name},')
            marshal_lines.append('        static_cast<jsize>(i), s);')
            marshal_lines.append('    env->DeleteLocalRef(s);')
            marshal_lines.append('  }')
            cleanup_lines.append(f'  env->DeleteLocalRef(j_{f.name});')
            cleanup_lines.append(
                f'  env->DeleteLocalRef(j_string_cls_{f.name});'
            )
            call_args.append(f'j_{f.name}')
        else:
            raise ValueError(f'Unhandled field type: {f.type}')
    return marshal_lines, cleanup_lines, call_args


def _emit_trampoline_arg_marshal(
    fields: list[Field],
) -> tuple[list[str], list[str]]:
    """Pre-call lines + call-arg names for the inbound trampoline body.

    For str / list[str] / bytes fields, generate the conversion from
    JNI types to the handler's std:: types; for primitives, just pass
    them through unchanged.
    """
    pre_lines: list[str] = []
    call_args: list[str] = []
    for f in fields:
        if f.type == 'str':
            pre_lines.append(f'    const std::string {f.name}_str =')
            pre_lines.append(
                f'        core::PlatformAndroid::GetJString(' f'env, {f.name});'
            )
            call_args.append(f'{f.name}_str')
        elif f.type == 'list[str]':
            pre_lines.append(f'    std::vector<std::string> {f.name}_vec;')
            pre_lines.append('    {')
            pre_lines.append(
                f'      const jsize {f.name}_len ='
                f' env->GetArrayLength({f.name});'
            )
            pre_lines.append(
                f'      {f.name}_vec.reserve('
                f'static_cast<size_t>({f.name}_len));'
            )
            pre_lines.append(
                f'      for (jsize {f.name}_i = 0;'
                f' {f.name}_i < {f.name}_len; ++{f.name}_i) {{'
            )
            pre_lines.append(
                f'        auto* {f.name}_js = static_cast<jstring>('
            )
            pre_lines.append(
                f'            env->GetObjectArrayElement('
                f'{f.name}, {f.name}_i));'
            )
            pre_lines.append(
                f'        {f.name}_vec.push_back('
                f'core::PlatformAndroid::GetJString('
                f'env, {f.name}_js));'
            )
            pre_lines.append(f'        env->DeleteLocalRef({f.name}_js);')
            pre_lines.append('      }')
            pre_lines.append('    }')
            call_args.append(f'{f.name}_vec')
        elif f.type == 'bytes':
            pre_lines.append(f'    std::vector<uint8_t> {f.name}_vec;')
            pre_lines.append('    {')
            pre_lines.append(
                f'      const jsize {f.name}_len ='
                f' env->GetArrayLength({f.name});'
            )
            pre_lines.append(
                f'      {f.name}_vec.resize('
                f'static_cast<size_t>({f.name}_len));'
            )
            pre_lines.append(f'      if ({f.name}_len > 0) {{')
            pre_lines.append(
                f'        env->GetByteArrayRegion({f.name}, 0,'
                f' {f.name}_len,'
            )
            pre_lines.append(
                f'            reinterpret_cast<jbyte*>('
                f'{f.name}_vec.data()));'
            )
            pre_lines.append('      }')
            pre_lines.append('    }')
            call_args.append(f'{f.name}_vec')
        else:
            # Primitive — pass through.
            call_args.append(f.name)
    return pre_lines, call_args


def _emit_cpp_impl(messages: list[Message]) -> str:

    j2n = [m for m in messages if m.direction is Dir.JAVA_TO_NATIVE]
    n2j = [m for m in messages if m.direction is Dir.NATIVE_TO_JAVA]

    out: list[str] = [_CPP_IMPL_HEADER]

    # Anonymous-namespace state + trampolines + native-method table.
    out.append(
        'namespace {\n\n'
        'AndroidInboundHandler* g_inbound_handler{};\n'
        'AndroidMessageSender g_sender;\n\n'
    )

    # J->N trampolines.
    for msg in j2n:
        c_params = [(_JNI_CTYPE[f.type], f.name) for f in msg.fields]
        c_param_list = ', '.join(f'{t} {n}' for t, n in c_params)
        pre_lines, call_args = _emit_trampoline_arg_marshal(msg.fields)
        call_args_str = ', '.join(call_args)
        signature = 'JNIEnv* env, jclass'
        if c_param_list:
            signature += f', {c_param_list}'

        body = (
            f'void JniBridge_{msg.name}({signature}) {{\n'
            f'  try {{\n'
            f'    if (g_inbound_handler != nullptr) {{\n'
        )
        if pre_lines:
            body += '\n'.join(pre_lines) + '\n'
        body += (
            f'      g_inbound_handler->On{msg.name}({call_args_str});\n'
            f'    }}\n'
            f'  }} catch (const std::exception& exc) {{\n'
            f'    if (core::g_core != nullptr) {{\n'
            f'      core::g_core->logging->Log(\n'
            f'          LogName::kBa, LogLevel::kError,\n'
            f'          std::string("AndroidMessageBus {msg.name}: ")\n'
            f'              + exc.what());\n'
            f'    }}\n'
            f'  }}\n'
            f'}}\n\n'
        )
        out.append(body)

    # Native method table.  Java side splits each typed sender into
    # a public wrapper + a private Impl native; the Impl is what we
    # bind here. The wrapper handles pre-init queueing.
    out.append('const JNINativeMethod kJniBridgeMethods[] = {\n')
    for msg in j2n:
        sig = _jni_signature(msg.fields)
        out.append(
            f'    {{"nativeSend{msg.name}Impl", "{sig}",\n'
            f'     reinterpret_cast<void*>(&JniBridge_{msg.name})}},\n'
        )
    out.append('};\n\n}  // namespace\n\n')

    # Outbound sender method bodies.
    for msg in n2j:
        params = ', '.join(f'{_CPP_PARAM[f.type]} {f.name}' for f in msg.fields)
        marshal_lines, cleanup_lines, call_args = _emit_sender_marshal(
            msg.fields
        )
        call_arg_str = ''.join(', ' + a for a in call_args)
        body = (
            f'void AndroidMessageSender::Send{msg.name}({params}) {{\n'
            f'  JNIEnv* env = core::PlatformAndroid::GetEnv();\n'
        )
        if marshal_lines:
            body += '\n'.join(marshal_lines) + '\n'
        body += (
            f'  env->CallStaticVoidMethod(jbridge_class_,\n'
            f'      {_method_id_member(msg.name)}{call_arg_str});\n'
        )
        if cleanup_lines:
            body += '\n'.join(cleanup_lines) + '\n'
        body += '}\n\n'
        out.append(body)

    # Handler-installer + sender-accessor functions.
    out.append(
        'auto GetAndroidMessageSender() -> AndroidMessageSender* {\n'
        '  return &g_sender;\n'
        '}\n\n'
        'void SetAndroidInboundHandler(AndroidInboundHandler* h) {\n'
        '  g_inbound_handler = h;\n'
        '}\n\n'
    )

    out.append(
        'auto InstallAndroidMessageBus(JNIEnv* env) -> jint {\n'
        '  jclass cls = env->FindClass(\n'
        '      "com/ericfroemling/ballistica/mgen/BallisticaJniBridge");\n'
        '  if (cls == nullptr) {\n'
        '    return JNI_ERR;\n'
        '  }\n'
        '  if (env->RegisterNatives(\n'
        '          cls, kJniBridgeMethods,\n'
        '          sizeof(kJniBridgeMethods) / sizeof(JNINativeMethod))\n'
        '      != JNI_OK) {\n'
        '    env->DeleteLocalRef(cls);\n'
        '    return JNI_ERR;\n'
        '  }\n'
        '  g_sender.jbridge_class_ = static_cast<jclass>(\n'
        '      env->NewGlobalRef(cls));\n'
    )
    for msg in n2j:
        sig = _jni_signature(msg.fields)
        member = _method_id_member(msg.name)
        out.append(
            f'  g_sender.{member} = env->GetStaticMethodID(\n'
            f'      cls, "fromNative{msg.name}", "{sig}");\n'
        )
    out.append('  env->DeleteLocalRef(cls);\n')
    # Verify every cached mid is non-null.
    for msg in n2j:
        member = _method_id_member(msg.name)
        out.append(f'  if (g_sender.{member} == nullptr) return JNI_ERR;\n')
    out.append('  return JNI_OK;\n}\n')

    return ''.join(out)


# --------------------------------------------------------- pcommand entries


def generate_java(projroot: str, out_path: str) -> None:
    """Emit BallisticaJniBridge.java to `out_path`."""

    messages = _load_spec(projroot)
    _validate(messages)
    text = _emit_java(messages)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(text)


def generate_cpp(projroot: str, out_path: str) -> None:
    """Emit android_messages_{decl,impl}.inc based on out_path basename."""

    messages = _load_spec(projroot)
    _validate(messages)
    base = os.path.basename(out_path)
    if base == 'android_messages_decl.inc':
        text = _emit_cpp_decl(messages)
    elif base == 'android_messages_impl.inc':
        text = _emit_cpp_impl(messages)
    else:
        raise ValueError(
            f'gen_android_message_cpp got unexpected output name: {base!r}.'
        )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(text)
