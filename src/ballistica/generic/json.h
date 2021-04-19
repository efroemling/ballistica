// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GENERIC_JSON_H_
#define BALLISTICA_GENERIC_JSON_H_

/*
  Copyright (c) 2009 Dave Gamble

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in
  all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
  THE SOFTWARE.
*/

#include "ballistica/ballistica.h"

namespace ballistica {

#pragma clang diagnostic push
#pragma ide diagnostic ignored "OCUnusedMacroInspection"

// #ifdef __cplusplus
// extern "C" {
// #endif

/* cJSON Types: */
#define cJSON_False 0u
#define cJSON_True 1u
#define cJSON_NULL 2u
#define cJSON_Number 3u
#define cJSON_String 4u
#define cJSON_Array 5u
#define cJSON_Object 6u

#define cJSON_IsReference 256u

/* The cJSON structure: */
typedef struct cJSON {
  struct cJSON *next,
      *prev; /* next/prev allow you to walk array/object chains. Alternatively,
                use GetArraySize/GetArrayItem/GetObjectItem */
  struct cJSON*
      child; /* An array or object item will have a child pointer pointing to a
                chain of the items in the array/object. */

  uint32_t type; /* The type of the item, as above. */

  char* valuestring;  /* The item's string, if type==cJSON_String */
  int valueint;       /* The item's number, if type==cJSON_Number */
  double valuedouble; /* The item's number, if type==cJSON_Number */

  char* string; /* The item's name string, if this item is the child of, or is
                   in the list of subitems of an object. */
} cJSON;

typedef struct cJSON_Hooks {
  void* (*malloc_fn)(size_t sz);
  void (*free_fn)(void* ptr);
} cJSON_Hooks;

/* Supply malloc, realloc and free functions to cJSON */
extern void cJSON_InitHooks(cJSON_Hooks* hooks);

/* Supply a block of JSON, and this returns a cJSON object you can interrogate.
 * Call cJSON_Delete when finished. */
extern auto cJSON_Parse(const char* value) -> cJSON*;
/* Render a cJSON entity to text for transfer/storage. Free the char* when
 * finished. */
extern auto cJSON_Print(cJSON* item) -> char*;
/* Render a cJSON entity to text for transfer/storage without any formatting.
 * Free the char* when finished. */
extern auto cJSON_PrintUnformatted(cJSON* item) -> char*;
/* Delete a cJSON entity and all subentities. */
extern void cJSON_Delete(cJSON* c);

/* Returns the number of items in an array (or object). */
extern auto cJSON_GetArraySize(cJSON* array) -> int;
/* Retrieve item number "item" from array "array". Returns NULL if unsuccessful.
 */
extern auto cJSON_GetArrayItem(cJSON* array, int item) -> cJSON*;
/* Get item "string" from object. Case insensitive. */
extern auto cJSON_GetObjectItem(cJSON* object, const char* string) -> cJSON*;

/* For analysing failed parses. This returns a pointer to the parse error.
 * You'll probably need to look a few chars back to make sense of it. Defined
 * when cJSON_Parse() returns 0. 0 when cJSON_Parse() succeeds. */
extern auto cJSON_GetErrorPtr() -> const char*;

/* These calls create a cJSON item of the appropriate type. */
extern auto cJSON_CreateNull() -> cJSON*;
extern auto cJSON_CreateTrue() -> cJSON*;
extern auto cJSON_CreateFalse() -> cJSON*;
extern auto cJSON_CreateBool(int b) -> cJSON*;
extern auto cJSON_CreateNumber(double num) -> cJSON*;
extern auto cJSON_CreateString(const char* string) -> cJSON*;
extern auto cJSON_CreateArray() -> cJSON*;
extern auto cJSON_CreateObject() -> cJSON*;

/* These utilities create an Array of count items. */
extern auto cJSON_CreateIntArray(const int* numbers, int count) -> cJSON*;
extern auto cJSON_CreateFloatArray(const float* numbers, int count) -> cJSON*;
extern auto cJSON_CreateDoubleArray(const double* numbers, int count) -> cJSON*;
extern auto cJSON_CreateStringArray(const char** strings, int count) -> cJSON*;

/* Append item to the specified array/object. */
extern void cJSON_AddItemToArray(cJSON* array, cJSON* item);
extern void cJSON_AddItemToObject(cJSON* object, const char* string,
                                  cJSON* item);
/* Append reference to item to the specified array/object. Use this when you
 * want to add an existing cJSON to a new cJSON, but don't want to corrupt your
 * existing cJSON. */
extern void cJSON_AddItemReferenceToArray(cJSON* array, cJSON* item);
extern void cJSON_AddItemReferenceToObject(cJSON* object, const char* string,
                                           cJSON* item);

/* Remove/Detach items from Arrays/Objects. */
extern auto cJSON_DetachItemFromArray(cJSON* array, int which) -> cJSON*;
extern void cJSON_DeleteItemFromArray(cJSON* array, int which);
extern auto cJSON_DetachItemFromObject(cJSON* object, const char* string)
    -> cJSON*;
extern void cJSON_DeleteItemFromObject(cJSON* object, const char* string);

/* Update array items. */
extern void cJSON_ReplaceItemInArray(cJSON* array, int which, cJSON* newitem);
extern void cJSON_ReplaceItemInObject(cJSON* object, const char* string,
                                      cJSON* newitem);

/* Duplicate a cJSON item */
extern auto cJSON_Duplicate(cJSON* item, int recurse) -> cJSON*;
/* Duplicate will create a new, identical cJSON item to the one you pass, in new
memory that will need to be released. With recurse!=0, it will duplicate any
children connected to the item. The item->next and ->prev pointers are always
zero on return from Duplicate. */

/* ParseWithOpts allows you to require (and check) that the JSON is null
 * terminated, and to retrieve the pointer to the final byte parsed. */
extern auto cJSON_ParseWithOpts(const char* value,
                                const char** return_parse_end,
                                int require_null_terminated) -> cJSON*;

extern void cJSON_Minify(char* json);

/* Macros for creating things quickly. */
#define cJSON_AddNullToObject(object, name) \
  cJSON_AddItemToObject(object, name, cJSON_CreateNull())
#define cJSON_AddTrueToObject(object, name) \
  cJSON_AddItemToObject(object, name, cJSON_CreateTrue())
#define cJSON_AddFalseToObject(object, name) \
  cJSON_AddItemToObject(object, name, cJSON_CreateFalse())
#define cJSON_AddBoolToObject(object, name, b) \
  cJSON_AddItemToObject(object, name, cJSON_CreateBool(b))
#define cJSON_AddNumberToObject(object, name, n) \
  cJSON_AddItemToObject(object, name, cJSON_CreateNumber(n))
#define cJSON_AddStringToObject(object, name, s) \
  cJSON_AddItemToObject(object, name, cJSON_CreateString(s))

/* When assigning an integer value, it needs to be propagated to valuedouble
 * too. */
#define cJSON_SetIntValue(object, val) \
  ((object) ? (object)->valueint = (object)->valuedouble = (val) : (val))

// ericf addition: c++ wrapper for this stuff.

// NOTE: once added to a dict/list/etc, the underlying cJSON's
// lifecycle is dependent on its parent, not this object.
// ..So be sure to keep the root JsonObject alive as long as child
// objects are being accessed.
class JsonObject {
 public:
  ~JsonObject() {
    if (obj_ && root_) {
      cJSON_Delete(obj_);
    }
  }
  auto root() const -> bool { return root_; }
  auto obj() const -> cJSON* { return obj_; }

  // Root objects will clean themselves up.
  // turn this off when adding to a dict/list/etc.
  // that will take responsibility for that instead.
  void set_root(bool val) { root_ = val; }

 protected:
  JsonObject() = default;

  // Used by subclasses to fill value.
  void set_obj(cJSON* val) {
    assert(obj_ == nullptr);
    obj_ = val;
  }

 private:
  cJSON* obj_ = nullptr;
  bool root_ = true;
};

class JsonDict : public JsonObject {
 public:
  JsonDict() { set_obj(cJSON_CreateObject()); }
  void AddNumber(const std::string& name, double val) {
    cJSON_AddItemToObject(obj(), name.c_str(), cJSON_CreateNumber(val));
  }
  void AddString(const std::string& name, const std::string& val) {
    cJSON_AddItemToObject(obj(), name.c_str(), cJSON_CreateString(val.c_str()));
  }
  auto PrintUnformatted() -> std::string {
    return cJSON_PrintUnformatted(obj());
  }
};

// class JsonNumber : public JsonObject {
//  public:
//   JsonNumber(double val) { set_obj(cJSON_CreateNumber(val)); }
// };

// class JsonString : public JsonObject {
//  public:
//   JsonString(const std::string& s) { set_obj(cJSON_CreateString(s.c_str()));
//   } JsonString(const char* s) { set_obj(cJSON_CreateString(s)); }
// };

#pragma clang diagnostic pop

}  // namespace ballistica

#endif  // BALLISTICA_GENERIC_JSON_H_
