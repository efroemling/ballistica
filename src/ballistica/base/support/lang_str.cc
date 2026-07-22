// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/support/lang_str.h"

#include <algorithm>
#include <charconv>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include "ballistica/base/assets/assets.h"
#include "ballistica/base/base.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/platform/platform.h"
#include "ballistica/shared/generic/json_facade.h"

namespace ballistica::base {

// Substitution keyword pattern: [a-z][a-z0-9_]* (mirrors the Python
// loctext _SUB_RE).
static auto IsSubKeyStart_(char c) -> bool { return c >= 'a' && c <= 'z'; }
static auto IsSubKeyChar_(char c) -> bool {
  return (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_';
}

// Append each {name} substitution token found in text to names (in
// order of appearance; duplicates kept). Non-token brace content is
// skipped, matching Substitute_'s scanning rules.
static void ScanSubTokens_(const std::string& text,
                           std::vector<std::string>* names) {
  size_t i = 0;
  while (i < text.size()) {
    if (text[i] == '{' && i + 1 < text.size() && IsSubKeyStart_(text[i + 1])) {
      size_t k = i + 2;
      while (k < text.size() && IsSubKeyChar_(text[k])) {
        ++k;
      }
      if (k < text.size() && text[k] == '}') {
        names->push_back(text.substr(i + 1, k - i - 1));
        i = k + 1;
        continue;
      }
    }
    ++i;
  }
}

static auto ParseSub_(const JsonRef& ref, int depth,
                      const std::vector<std::string>* packages,
                      std::string* error) -> std::optional<LangStr::Sub>;

static auto ParseNode_(const JsonRef& ref, int depth,
                       const std::vector<std::string>* packages,
                       std::string* error) -> std::shared_ptr<const LangStr> {
  if (depth > kLangStrMaxNestingDepth) {
    *error = "max nesting depth exceeded";
    return nullptr;
  }
  if (!ref.is_object()) {
    *error = "language-string node is not an object";
    return nullptr;
  }
  auto out = std::make_shared<LangStr>();

  // Type tag: 'r'/'v'/'i'; absent means the indexed (default) form.
  std::string tag{"i"};
  if (auto tagref = ref["t"]) {
    auto tagstr = tagref.as_string();
    if (!tagstr.has_value()) {
      *error = "non-string type tag";
      return nullptr;
    }
    tag = *tagstr;
  }

  auto parse_keyword_subs = [&](const JsonRef& subsref) -> bool {
    if (!subsref.is_object()) {
      *error = "substitutions are not an object";
      return false;
    }
    for (auto&& [key, val] : subsref.items()) {
      auto sub = ParseSub_(val, depth, packages, error);
      if (!sub.has_value()) {
        return false;
      }
      out->subs.push_back({std::string(key), std::move(*sub)});
    }
    return true;
  };

  if (tag == "r") {
    out->form = LangStr::Form::kResource;
    auto apverid = ref["a"].as_string();
    auto name = ref["n"].as_string();
    if (!apverid.has_value() || !name.has_value()) {
      *error = "resource form requires string 'a' and 'n'";
      return nullptr;
    }
    out->apverid = *apverid;
    out->name = *name;
    if (auto subsref = ref["s"]) {
      if (!parse_keyword_subs(subsref)) {
        return nullptr;
      }
    }
  } else if (tag == "v") {
    out->form = LangStr::Form::kValue;
    auto value = ref["v"].as_string();
    if (!value.has_value()) {
      *error = "value form requires string 'v'";
      return nullptr;
    }
    out->value = *value;
    if (auto subsref = ref["s"]) {
      if (!parse_keyword_subs(subsref)) {
        return nullptr;
      }
    }
    // A declared sub no {token} in the value consumes is always a bug
    // (typo'd key or a non-lowercase token, which reads as literal
    // text); fail here at parse rather than silently dropping it at
    // evaluate. Value forms are self-contained so this is fully
    // checkable at parse, unlike resource forms (locale-dependent
    // table text; covered by authoring-side checks + evaluate-time
    // missing-argument errors).
    if (!out->subs.empty()) {
      std::vector<std::string> tokens;
      ScanSubTokens_(out->value, &tokens);
      for (auto&& entry : out->subs) {
        if (std::find(tokens.begin(), tokens.end(), entry.key)
            == tokens.end()) {
          *error = "substitution '" + entry.key + "' matches no '{" + entry.key
                   + "}' token in value '" + out->value + "'";
          return nullptr;
        }
      }
    }
  } else if (tag == "i") {
    out->form = LangStr::Form::kResourceIndexed;
    auto pkg = ref["p"].as_int();
    auto index = ref["n"].as_int();
    if (!pkg.has_value() || !index.has_value()) {
      *error = "indexed form requires int 'p' and 'n'";
      return nullptr;
    }
    out->pkg = *pkg;
    out->index = *index;
    if (packages != nullptr) {
      // Bind against the payload's package-index manifest.
      if (*pkg < 0 || static_cast<size_t>(*pkg) >= packages->size()) {
        *error = "package index " + std::to_string(*pkg)
                 + " out of range for manifest of size "
                 + std::to_string(packages->size());
        return nullptr;
      }
      out->apverid = (*packages)[static_cast<size_t>(*pkg)];
    }
    if (auto subsref = ref["s"]) {
      if (!subsref.is_array()) {
        *error = "indexed substitutions are not an array";
        return nullptr;
      }
      for (auto&& val : subsref.elements()) {
        auto sub = ParseSub_(val, depth, packages, error);
        if (!sub.has_value()) {
          return nullptr;
        }
        out->subs.push_back({std::string(), std::move(*sub)});
      }
    }
  } else {
    *error = "unrecognized type tag '" + tag + "'";
    return nullptr;
  }
  return out;
}

static auto ParseSub_(const JsonRef& ref, int depth,
                      const std::vector<std::string>* packages,
                      std::string* error) -> std::optional<LangStr::Sub> {
  if (auto str = ref.as_string()) {
    return LangStr::Sub{std::string(*str)};
  }
  if (ref.is_number()) {
    auto intval = ref.as_int();
    if (!intval.has_value()) {
      *error = "non-integer numeric substitution";
      return {};
    }
    return LangStr::Sub{*intval};
  }
  if (ref.is_object()) {
    auto nested = ParseNode_(ref, depth + 1, packages, error);
    if (!nested) {
      return {};
    }
    return LangStr::Sub{std::move(nested)};
  }
  *error = "substitution is not a string, int, or language-string";
  return {};
}

auto LangStr::FromJson(std::string_view json,
                       const std::vector<std::string>* packages)
    -> std::expected<std::shared_ptr<const LangStr>, std::string> {
  auto doc = JsonDoc::Parse(json);
  if (!doc.has_value()) {
    return std::unexpected("json parse failed: " + doc.error().message);
  }
  std::string error;
  auto out = ParseNode_(doc->root(), 0, packages, &error);
  if (!out) {
    return std::unexpected(error);
  }
  return out;
}

// The substitution-argument names a table value consumes, in canonical
// (sorted) order: for plain text its {name} tokens; for a selector its
// pivot arg plus any tokens in its forms. Mirrors Python
// loctext.substitution_names + the PackageStructure sorted-params
// convention, fixing positional-substitution order for indexed values.
static auto SubstitutionNames_(const LangStrTableValue& value)
    -> std::vector<std::string> {
  std::vector<std::string> names;
  if (auto* text = std::get_if<std::string>(&value)) {
    ScanSubTokens_(*text, &names);
  } else {
    auto& sel = std::get<LangStrSelector>(value);
    names.push_back(sel.arg);
    for (auto&& [key, form] : sel.forms) {
      ScanSubTokens_(form, &names);
    }
  }
  std::sort(names.begin(), names.end());
  names.erase(std::unique(names.begin(), names.end()), names.end());
  return names;
}

// --- CLDR cardinal plural rules (integer-only) ------------------------------
//
// Direct port of the compact rule table in bacommon.loctext (see its
// module comment for scope/limits); keyed by *resolved* locale wire
// value. The Python side's producer tests cross-check these rules
// against ICU, so this port inherits that verification via the shared
// data model. Unknown locales fall back to the one-for-1 rule, matching
// Python.

static auto PluralCategory_(const std::string& locale, int64_t count)
    -> std::string {
  int64_t n = count < 0 ? -count : count;
  int64_t mod10 = n % 10;
  int64_t mod100 = n % 100;

  // other-only (no count distinction).
  if (locale == "chn_tr" || locale == "chn_sim" || locale == "jpn"
      || locale == "kor" || locale == "thai" || locale == "viet"
      || locale == "indnsn" || locale == "mlay") {
    return "other";
  }
  // 0,1 -> one.
  if (locale == "frnch" || locale == "prtg_brz" || locale == "pers"
      || locale == "hndi") {
    return (n == 0 || n == 1) ? "one" : "other";
  }
  // East-Slavic one/few/many.
  if (locale == "rusn" || locale == "ukrn" || locale == "blrs") {
    if (mod10 == 1 && mod100 != 11) {
      return "one";
    }
    if (mod10 >= 2 && mod10 <= 4 && !(mod100 >= 12 && mod100 <= 14)) {
      return "few";
    }
    return "many";
  }
  // Polish one/few/many.
  if (locale == "pol") {
    if (n == 1) {
      return "one";
    }
    if (mod10 >= 2 && mod10 <= 4 && !(mod100 >= 12 && mod100 <= 14)) {
      return "few";
    }
    return "many";
  }
  // West-Slavic one/few/other.
  if (locale == "czch" || locale == "slvk") {
    if (n == 1) {
      return "one";
    }
    if (n >= 2 && n <= 4) {
      return "few";
    }
    return "other";
  }
  // South-Slavic one/few/other.
  if (locale == "croat" || locale == "srbn") {
    if (mod10 == 1 && mod100 != 11) {
      return "one";
    }
    if (mod10 >= 2 && mod10 <= 4 && !(mod100 >= 12 && mod100 <= 14)) {
      return "few";
    }
    return "other";
  }
  // Romanian one/few/other.
  if (locale == "rom") {
    if (n == 1) {
      return "one";
    }
    if (n == 0 || (mod100 >= 1 && mod100 <= 19)) {
      return "few";
    }
    return "other";
  }
  // Arabic zero/one/two/few/many/other.
  if (locale == "arabc") {
    if (n == 0) {
      return "zero";
    }
    if (n == 1) {
      return "one";
    }
    if (n == 2) {
      return "two";
    }
    if (mod100 >= 3 && mod100 <= 10) {
      return "few";
    }
    if (mod100 >= 11 && mod100 <= 99) {
      return "many";
    }
    return "other";
  }
  // Filipino.
  if (locale == "filp") {
    return (mod10 == 4 || mod10 == 6 || mod10 == 9) ? "other" : "one";
  }
  // one/other (n == 1): the common Germanic/Romance rule and the
  // fallback for unknown locales.
  return n == 1 ? "one" : "other";
}

// Expand {name} placeholders in a template against evaluated args.
// Mirrors Python loctext._substitute: only tokens matching the keyword
// pattern are treated as substitutions (and are errors if missing from
// args); any other brace content passes through untouched. When
// ``pound`` is set, '#' occurrences are replaced with it first (on the
// template, so substituted values containing '#' stay untouched).
static auto Substitute_(
    const std::string& intext,
    const std::unordered_map<std::string, std::string>& args,
    const std::string* pound = nullptr)
    -> std::expected<std::string, std::string> {
  std::string text = intext;
  if (pound != nullptr) {
    size_t pos = 0;
    while ((pos = text.find('#', pos)) != std::string::npos) {
      text.replace(pos, 1, *pound);
      pos += pound->size();
    }
  }
  std::string out;
  out.reserve(text.size());
  size_t i = 0;
  while (i < text.size()) {
    char c = text[i];
    if (c != '{') {
      out.push_back(c);
      ++i;
      continue;
    }
    // Try to scan a {keyword} token.
    size_t j = i + 1;
    if (j < text.size() && IsSubKeyStart_(text[j])) {
      size_t k = j + 1;
      while (k < text.size() && IsSubKeyChar_(text[k])) {
        ++k;
      }
      if (k < text.size() && text[k] == '}') {
        std::string key = text.substr(j, k - j);
        auto entry = args.find(key);
        if (entry == args.end()) {
          return std::unexpected("Missing argument '" + key + "'.");
        }
        out += entry->second;
        i = k + 1;
        continue;
      }
    }
    // Not a token; pass the brace through literally.
    out.push_back(c);
    ++i;
  }
  return out;
}

// Pick a selector's form for the args and substitute its leaf text;
// mirrors Python loctext._eval_selector.
static auto EvalSelector_(
    const LangStrSelector& sel, const std::string& plural_locale,
    const std::unordered_map<std::string, std::string>& args)
    -> std::expected<std::string, std::string> {
  auto argval = args.find(sel.arg);
  if (argval == args.end()) {
    return std::unexpected("Missing argument '" + sel.arg + "'.");
  }
  auto find_form = [&sel](const std::string& key) -> const std::string* {
    for (auto&& [formkey, formval] : sel.forms) {
      if (formkey == key) {
        return &formval;
      }
    }
    return nullptr;
  };
  if (sel.is_plural) {
    // Our args are all strings by this point; the pivot must parse
    // fully as an integer (mirrors Python int(raw)).
    const std::string& raw = argval->second;
    int64_t count{};
    auto [ptr, ec] =
        std::from_chars(raw.data(), raw.data() + raw.size(), count);
    if (ec != std::errc() || ptr != raw.data() + raw.size()) {
      return std::unexpected("Plural argument '" + sel.arg
                             + "' must be an integer; got '" + raw + "'.");
    }
    // Exact '=N' matches win over the category rule.
    const std::string* form = find_form("=" + std::to_string(count));
    if (form == nullptr) {
      form = find_form(PluralCategory_(plural_locale, count));
    }
    if (form == nullptr) {
      form = find_form("other");
    }
    if (form == nullptr) {
      return std::unexpected("Plural for '" + sel.arg
                             + "' has no matching form and no 'other'.");
    }
    std::string pound = std::to_string(count);
    return Substitute_(*form, args, &pound);
  }
  // Select: key by the argument's string value.
  const std::string* form = find_form(argval->second);
  if (form == nullptr) {
    form = find_form("other");
  }
  if (form == nullptr) {
    return std::unexpected("Select for '" + sel.arg + "' has no matching key '"
                           + argval->second + "' and no 'other'.");
  }
  return Substitute_(*form, args);
}

static auto EvalNode_(const LangStr& ls, int depth)
    -> std::expected<std::string, std::string> {
  if (depth > kLangStrMaxNestingDepth) {
    return std::unexpected("max nesting depth exceeded");
  }
  if (ls.form == LangStr::Form::kResourceIndexed && ls.apverid.empty()) {
    // Unbound indexed values are unresolvable by design: their package
    // ints only mean something against a payload's package-index
    // manifest (supplied to FromJson at parse).
    return std::unexpected(
        "indexed form requires a package-index binding to evaluate");
  }

  // Evaluate substitutions first (shared by all forms). Keyword subs
  // land in ``args``; the indexed form's positional subs (empty keys)
  // land in ``posargs`` in order.
  std::unordered_map<std::string, std::string> args;
  std::vector<std::string> posargs;
  for (auto&& entry : ls.subs) {
    std::string evaluated;
    if (auto* strval = std::get_if<std::string>(&entry.value)) {
      evaluated = *strval;
    } else if (auto* intval = std::get_if<int64_t>(&entry.value)) {
      evaluated = std::to_string(*intval);
    } else {
      auto& nested = std::get<std::shared_ptr<const LangStr>>(entry.value);
      auto sub = EvalNode_(*nested, depth + 1);
      if (!sub.has_value()) {
        return sub;
      }
      evaluated = std::move(*sub);
    }
    if (entry.key.empty()) {
      posargs.push_back(std::move(evaluated));
    } else {
      args[entry.key] = std::move(evaluated);
    }
  }

  if (ls.form == LangStr::Form::kValue) {
    return Substitute_(ls.value, args);
  }

  // Resource / bound-indexed: resolve against the current native
  // language tables.
  auto tables = g_base && g_base->assets
                    ? g_base->assets->LangStrTablesSnapshot()
                    : nullptr;
  if (!tables) {
    return std::unexpected("no language tables loaded");
  }
  auto pkg = tables->packages.find(ls.apverid);
  if (pkg == tables->packages.end()) {
    return std::unexpected("no values for package '" + ls.apverid + "'");
  }
  const LangStrTableValue* tableval{};
  if (ls.form == LangStr::Form::kResource) {
    auto val = pkg->second.values.find(ls.name);
    if (val == pkg->second.values.end()) {
      return std::unexpected("no value for '" + ls.name + "' in " + ls.apverid);
    }
    tableval = &val->second.value;
  } else {
    // Bound indexed: the integer index resolves via canonical
    // sorted-name order, and its positional subs map onto the value's
    // canonical (sorted) substitution names.
    auto& names = pkg->second.sorted_names;
    if (ls.index < 0 || static_cast<size_t>(ls.index) >= names.size()) {
      return std::unexpected("unknown string index " + std::to_string(ls.index)
                             + " in " + ls.apverid);
    }
    const std::string& name = names[static_cast<size_t>(ls.index)];
    tableval = &pkg->second.values.at(name).value;
    auto params = SubstitutionNames_(*tableval);
    if (params.size() != posargs.size()) {
      return std::unexpected("arity mismatch for '" + name
                             + "': " + std::to_string(posargs.size())
                             + " != " + std::to_string(params.size()));
    }
    for (size_t i = 0; i < params.size(); ++i) {
      args[params[i]] = std::move(posargs[i]);
    }
  }
  if (auto* text = std::get_if<std::string>(&*tableval)) {
    return Substitute_(*text, args);
  }
  return EvalSelector_(std::get<LangStrSelector>(*tableval),
                       tables->plural_locale, args);
}

auto LangStr::Evaluate() const -> std::string {
  auto result = EvalNode_(*this, 0);
  if (!result.has_value()) {
    g_core->logging->Log(LogName::kBa, LogLevel::kWarning,
                         "langstr evaluate: " + result.error());
    return "LANGSTR_ERROR:" + result.error();
  }

  // Apply line-wrapping (decision D-t): a usage-site override on this
  // value wins; otherwise the *top-level* string's definition-time
  // hint from the tables applies (nested substitution fragments never
  // wrap themselves - the composed result is what has presentation).
  std::optional<LangStrWrap> wrapval = wrap;
  if (!wrapval.has_value()
      && (form == Form::kResource
          || (form == Form::kResourceIndexed && !apverid.empty()))) {
    if (auto tables = g_base && g_base->assets
                          ? g_base->assets->LangStrTablesSnapshot()
                          : nullptr) {
      if (auto pkg = tables->packages.find(apverid);
          pkg != tables->packages.end()) {
        const LangStrTableEntry* entry{};
        if (form == Form::kResource) {
          if (auto val = pkg->second.values.find(name);
              val != pkg->second.values.end()) {
            entry = &val->second;
          }
        } else if (index >= 0
                   && static_cast<size_t>(index)
                          < pkg->second.sorted_names.size()) {
          entry = &pkg->second.values.at(
              pkg->second.sorted_names[static_cast<size_t>(index)]);
        }
        if (entry != nullptr) {
          wrapval = entry->wrap;
        }
      }
    }
  }
  if (wrapval.has_value()) {
    return g_core->platform->SplitTextIntoLines(*result, wrapval->min_lines,
                                                wrapval->max_lines,
                                                wrapval->max_chars_per_line);
  }
  return *result;
}

static void FillObj_(JsonObjBuilder obj, const LangStr& ls) {
  auto fill_sub_obj = [](JsonObjBuilder subs, const LangStr::SubEntry& entry) {
    if (auto* strval = std::get_if<std::string>(&entry.value)) {
      subs.Add(entry.key, *strval);
    } else if (auto* intval = std::get_if<int64_t>(&entry.value)) {
      subs.Add(entry.key, *intval);
    } else {
      FillObj_(subs.AddObject(entry.key),
               *std::get<std::shared_ptr<const LangStr>>(entry.value));
    }
  };
  switch (ls.form) {
    case LangStr::Form::kResource: {
      obj.Add("t", "r");
      obj.Add("a", ls.apverid);
      obj.Add("n", ls.name);
      if (!ls.subs.empty()) {
        auto subs = obj.AddObject("s");
        for (auto&& entry : ls.subs) {
          fill_sub_obj(subs, entry);
        }
      }
      break;
    }
    case LangStr::Form::kValue: {
      obj.Add("t", "v");
      obj.Add("v", ls.value);
      if (!ls.subs.empty()) {
        auto subs = obj.AddObject("s");
        for (auto&& entry : ls.subs) {
          fill_sub_obj(subs, entry);
        }
      }
      break;
    }
    case LangStr::Form::kResourceIndexed: {
      // The indexed form is the multitype default; no type tag.
      obj.Add("p", ls.pkg);
      obj.Add("n", ls.index);
      if (!ls.subs.empty()) {
        auto subs = obj.AddArray("s");
        for (auto&& entry : ls.subs) {
          if (auto* strval = std::get_if<std::string>(&entry.value)) {
            subs.Add(*strval);
          } else if (auto* intval = std::get_if<int64_t>(&entry.value)) {
            subs.Add(*intval);
          } else {
            FillObj_(subs.AddObject(),
                     *std::get<std::shared_ptr<const LangStr>>(entry.value));
          }
        }
      }
      break;
    }
  }
}

auto LangStr::ToJson() const -> std::string {
  JsonBuilder builder;
  FillObj_(builder.root_object(), *this);
  return builder.Write();
}

// Fill a wire object with the resource-form projection of a node:
// bound indexed nodes convert (via tables) to resource nodes with
// keyword subs; resource/value nodes emit as-is with converted subs.
static auto FillResourceObj_(JsonObjBuilder obj, const LangStr& ls,
                             const LangStrTables* tables, int depth,
                             std::string* error) -> bool {
  if (depth > kLangStrMaxNestingDepth) {
    *error = "max nesting depth exceeded";
    return false;
  }
  auto fill_keyword_sub = [&](JsonObjBuilder subs, const std::string& key,
                              const LangStr::Sub& sub) -> bool {
    if (auto* strval = std::get_if<std::string>(&sub)) {
      subs.Add(key, *strval);
      return true;
    }
    if (auto* intval = std::get_if<int64_t>(&sub)) {
      subs.Add(key, *intval);
      return true;
    }
    return FillResourceObj_(subs.AddObject(key),
                            *std::get<std::shared_ptr<const LangStr>>(sub),
                            tables, depth + 1, error);
  };
  switch (ls.form) {
    case LangStr::Form::kValue: {
      obj.Add("t", "v");
      obj.Add("v", ls.value);
      if (!ls.subs.empty()) {
        auto subs = obj.AddObject("s");
        for (auto&& entry : ls.subs) {
          if (!fill_keyword_sub(subs, entry.key, entry.value)) {
            return false;
          }
        }
      }
      return true;
    }
    case LangStr::Form::kResource: {
      obj.Add("t", "r");
      obj.Add("a", ls.apverid);
      obj.Add("n", ls.name);
      if (!ls.subs.empty()) {
        auto subs = obj.AddObject("s");
        for (auto&& entry : ls.subs) {
          if (!fill_keyword_sub(subs, entry.key, entry.value)) {
            return false;
          }
        }
      }
      return true;
    }
    case LangStr::Form::kResourceIndexed: {
      if (ls.apverid.empty()) {
        *error = "cannot convert an unbound indexed value";
        return false;
      }
      if (tables == nullptr) {
        *error = "no language tables loaded";
        return false;
      }
      auto pkg = tables->packages.find(ls.apverid);
      if (pkg == tables->packages.end()) {
        *error = "no values for package '" + ls.apverid + "'";
        return false;
      }
      auto& names = pkg->second.sorted_names;
      if (ls.index < 0 || static_cast<size_t>(ls.index) >= names.size()) {
        *error = "unknown string index " + std::to_string(ls.index) + " in "
                 + ls.apverid;
        return false;
      }
      const std::string& name = names[static_cast<size_t>(ls.index)];
      auto params = SubstitutionNames_(pkg->second.values.at(name).value);
      if (params.size() != ls.subs.size()) {
        *error = "arity mismatch for '" + name + "'";
        return false;
      }
      obj.Add("t", "r");
      obj.Add("a", ls.apverid);
      obj.Add("n", name);
      if (!ls.subs.empty()) {
        auto subs = obj.AddObject("s");
        for (size_t i = 0; i < ls.subs.size(); ++i) {
          if (!fill_keyword_sub(subs, params[i], ls.subs[i].value)) {
            return false;
          }
        }
      }
      return true;
    }
  }
  return false;
}

auto LangStr::ToResourceJson() const
    -> std::expected<std::string, std::string> {
  auto tables = g_base && g_base->assets
                    ? g_base->assets->LangStrTablesSnapshot()
                    : nullptr;
  JsonBuilder builder;
  std::string error;
  if (!FillResourceObj_(builder.root_object(), *this, tables.get(), 0,
                        &error)) {
    return std::unexpected(error);
  }
  return builder.Write();
}

// Fill a wire object with the indexed-form projection of a node (the
// inverse of FillResourceObj_): resource nodes convert (via the package
// manifest + tables) to indexed nodes with positional subs; bound
// indexed nodes re-derive their package index; value nodes emit as-is
// with converted subs.
static auto FillIndexedObj_(JsonObjBuilder obj, const LangStr& ls,
                            const std::vector<std::string>& packages,
                            const LangStrTables* tables, int depth,
                            std::string* error) -> bool {
  if (depth > kLangStrMaxNestingDepth) {
    *error = "max nesting depth exceeded";
    return false;
  }
  auto pkg_index_for = [&](const std::string& apverid,
                           int64_t* out_index) -> bool {
    auto it = std::find(packages.begin(), packages.end(), apverid);
    if (it == packages.end()) {
      *error = "package '" + apverid + "' is not in the package manifest";
      return false;
    }
    *out_index = static_cast<int64_t>(it - packages.begin());
    return true;
  };
  auto fill_keyword_sub = [&](JsonObjBuilder subs, const std::string& key,
                              const LangStr::Sub& sub) -> bool {
    if (auto* strval = std::get_if<std::string>(&sub)) {
      subs.Add(key, *strval);
      return true;
    }
    if (auto* intval = std::get_if<int64_t>(&sub)) {
      subs.Add(key, *intval);
      return true;
    }
    return FillIndexedObj_(subs.AddObject(key),
                           *std::get<std::shared_ptr<const LangStr>>(sub),
                           packages, tables, depth + 1, error);
  };
  auto fill_positional_sub = [&](JsonArrBuilder subs,
                                 const LangStr::Sub& sub) -> bool {
    if (auto* strval = std::get_if<std::string>(&sub)) {
      subs.Add(*strval);
      return true;
    }
    if (auto* intval = std::get_if<int64_t>(&sub)) {
      subs.Add(*intval);
      return true;
    }
    return FillIndexedObj_(subs.AddObject(),
                           *std::get<std::shared_ptr<const LangStr>>(sub),
                           packages, tables, depth + 1, error);
  };
  switch (ls.form) {
    case LangStr::Form::kValue: {
      obj.Add("t", "v");
      obj.Add("v", ls.value);
      if (!ls.subs.empty()) {
        auto subs = obj.AddObject("s");
        for (auto&& entry : ls.subs) {
          if (!fill_keyword_sub(subs, entry.key, entry.value)) {
            return false;
          }
        }
      }
      return true;
    }
    case LangStr::Form::kResource: {
      if (tables == nullptr) {
        *error = "no language tables loaded";
        return false;
      }
      auto pkg = tables->packages.find(ls.apverid);
      if (pkg == tables->packages.end()) {
        *error = "no values for package '" + ls.apverid + "'";
        return false;
      }
      auto& names = pkg->second.sorted_names;
      auto name_it = std::lower_bound(names.begin(), names.end(), ls.name);
      if (name_it == names.end() || *name_it != ls.name) {
        *error = "no value for '" + ls.name + "' in " + ls.apverid;
        return false;
      }
      int64_t pkg_index;
      if (!pkg_index_for(ls.apverid, &pkg_index)) {
        return false;
      }
      // Keyword subs re-order onto the value's canonical (sorted)
      // substitution names; require an exact match.
      auto params = SubstitutionNames_(pkg->second.values.at(ls.name).value);
      if (params.size() != ls.subs.size()) {
        *error = "arity mismatch for '" + ls.name + "'";
        return false;
      }
      obj.Add("p", pkg_index);
      obj.Add("n", static_cast<int64_t>(name_it - names.begin()));
      if (!ls.subs.empty()) {
        auto subs = obj.AddArray("s");
        for (auto&& param : params) {
          const LangStr::Sub* sub{};
          for (auto&& entry : ls.subs) {
            if (entry.key == param) {
              sub = &entry.value;
              break;
            }
          }
          if (sub == nullptr) {
            *error =
                "missing substitution '" + param + "' for '" + ls.name + "'";
            return false;
          }
          if (!fill_positional_sub(subs, *sub)) {
            return false;
          }
        }
      }
      return true;
    }
    case LangStr::Form::kResourceIndexed: {
      if (ls.apverid.empty()) {
        *error = "cannot convert an unbound indexed value";
        return false;
      }
      int64_t pkg_index;
      if (!pkg_index_for(ls.apverid, &pkg_index)) {
        return false;
      }
      obj.Add("p", pkg_index);
      obj.Add("n", ls.index);
      if (!ls.subs.empty()) {
        auto subs = obj.AddArray("s");
        for (auto&& entry : ls.subs) {
          if (!fill_positional_sub(subs, entry.value)) {
            return false;
          }
        }
      }
      return true;
    }
  }
  return false;
}

auto LangStr::ToIndexedJson(const std::vector<std::string>& packages) const
    -> std::expected<std::string, std::string> {
  auto tables = g_base && g_base->assets
                    ? g_base->assets->LangStrTablesSnapshot()
                    : nullptr;
  JsonBuilder builder;
  std::string error;
  if (!FillIndexedObj_(builder.root_object(), *this, packages, tables.get(), 0,
                       &error)) {
    return std::unexpected(error);
  }
  return builder.Write();
}

static auto SubEquals_(const LangStr::Sub& a, const LangStr::Sub& b) -> bool {
  if (a.index() != b.index()) {
    return false;
  }
  if (auto* stra = std::get_if<std::string>(&a)) {
    return *stra == std::get<std::string>(b);
  }
  if (auto* inta = std::get_if<int64_t>(&a)) {
    return *inta == std::get<int64_t>(b);
  }
  return std::get<std::shared_ptr<const LangStr>>(a)->Equals(
      *std::get<std::shared_ptr<const LangStr>>(b));
}

auto LangStr::Equals(const LangStr& other) const -> bool {
  if (form != other.form || subs.size() != other.subs.size()
      || wrap.has_value() != other.wrap.has_value()) {
    return false;
  }
  if (wrap.has_value()
      && (wrap->min_lines != other.wrap->min_lines
          || wrap->max_lines != other.wrap->max_lines
          || wrap->max_chars_per_line != other.wrap->max_chars_per_line)) {
    return false;
  }
  switch (form) {
    case Form::kResource:
      if (apverid != other.apverid || name != other.name) {
        return false;
      }
      break;
    case Form::kValue:
      if (value != other.value) {
        return false;
      }
      break;
    case Form::kResourceIndexed:
      if (pkg != other.pkg || index != other.index) {
        return false;
      }
      break;
  }
  for (size_t i = 0; i < subs.size(); ++i) {
    if (subs[i].key != other.subs[i].key
        || !SubEquals_(subs[i].value, other.subs[i].value)) {
      return false;
    }
  }
  return true;
}

static void HashCombine_(size_t* seed, size_t val) {
  *seed ^= val + 0x9e3779b97f4a7c15u + (*seed << 6u) + (*seed >> 2u);
}

auto LangStr::Hash() const -> size_t {
  size_t seed = static_cast<size_t>(form);
  if (wrap.has_value()) {
    HashCombine_(&seed, static_cast<size_t>(wrap->min_lines));
    HashCombine_(&seed, static_cast<size_t>(wrap->max_lines + 1));
    HashCombine_(&seed, static_cast<size_t>(wrap->max_chars_per_line + 2));
  }
  std::hash<std::string> strhash;
  std::hash<int64_t> inthash;
  switch (form) {
    case Form::kResource:
      HashCombine_(&seed, strhash(apverid));
      HashCombine_(&seed, strhash(name));
      break;
    case Form::kValue:
      HashCombine_(&seed, strhash(value));
      break;
    case Form::kResourceIndexed:
      HashCombine_(&seed, inthash(pkg));
      HashCombine_(&seed, inthash(index));
      break;
  }
  for (auto&& entry : subs) {
    HashCombine_(&seed, strhash(entry.key));
    if (auto* strval = std::get_if<std::string>(&entry.value)) {
      HashCombine_(&seed, strhash(*strval));
    } else if (auto* intval = std::get_if<int64_t>(&entry.value)) {
      HashCombine_(&seed, inthash(*intval));
    } else {
      HashCombine_(
          &seed, std::get<std::shared_ptr<const LangStr>>(entry.value)->Hash());
    }
  }
  return seed;
}

}  // namespace ballistica::base
