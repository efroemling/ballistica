// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_GENERIC_JSON_H_
#define BALLISTICA_SHARED_GENERIC_JSON_H_

/*
  Copyright (c) 2009-2017 Dave Gamble and cJSON contributors

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

#include "ballistica/shared/ballistica.h"

// ericf note: Changes here from vanilla cJSON:
// - Placed under ballistica namespace.
// - Removed extern "C" braces.
// - Removed CJSON_CDECL, CJSON_PUBLIC, and other visibility controls.
// - In general, just treating this like our other internal C++ source.
// - Also added a few simple C++ wrappers (see bottom of this file)
// - Edited cJSON_GetNumberValue() to not return NAN (see notes in func).

namespace ballistica {

/* project version */
#define CJSON_VERSION_MAJOR 1
#define CJSON_VERSION_MINOR 7
#define CJSON_VERSION_PATCH 16

/* cJSON Types: */
#define cJSON_Invalid (0)
#define cJSON_False (1 << 0)
#define cJSON_True (1 << 1)
#define cJSON_NULL (1 << 2)
#define cJSON_Number (1 << 3)
#define cJSON_String (1 << 4)
#define cJSON_Array (1 << 5)
#define cJSON_Object (1 << 6)
#define cJSON_Raw (1 << 7) /* raw json */

#define cJSON_IsReference 256
#define cJSON_StringIsConst 512

/* The cJSON structure: */
typedef struct cJSON {
  /* next/prev allow you to walk array/object chains. Alternatively, use
   * GetArraySize/GetArrayItem/GetObjectItem */
  struct cJSON* next;
  struct cJSON* prev;
  /* An array or object item will have a child pointer pointing to a chain of
   * the items in the array/object. */
  struct cJSON* child;

  /* The type of the item, as above. */
  int type;

  /* The item's string, if type==cJSON_String  and type == cJSON_Raw */
  char* valuestring;
  /* writing to valueint is DEPRECATED, use cJSON_SetNumberValue instead */
  int valueint;
  /* The item's number, if type==cJSON_Number */
  double valuedouble;

  /* The item's name string, if this item is the child of, or is in the list of
   * subitems of an object. */
  char* string;
} cJSON;

typedef struct cJSON_Hooks {
  /* malloc/free are CDECL on Windows regardless of the default calling
   * convention of the compiler, so ensure the hooks allow passing those
   * functions directly. */
  void* (*malloc_fn)(size_t sz);
  void (*free_fn)(void* ptr);
} cJSON_Hooks;

typedef int cJSON_bool;

/* Limits how deeply nested arrays/objects can be before cJSON rejects to parse
 * them. This is to prevent stack overflows. */
#ifndef CJSON_NESTING_LIMIT
#define CJSON_NESTING_LIMIT 1000
#endif

/* returns the version of cJSON as a string */
const char* cJSON_Version(void);

/* Supply malloc, realloc and free functions to cJSON */
void cJSON_InitHooks(cJSON_Hooks* hooks);

/* Memory Management: the caller is always responsible to free the results from
 * all variants of cJSON_Parse (with cJSON_Delete) and cJSON_Print (with stdlib
 * free, cJSON_Hooks.free_fn, or cJSON_free as appropriate). The exception is
 * cJSON_PrintPreallocated, where the caller has full responsibility of the
 * buffer. */
/* Supply a block of JSON, and this returns a cJSON object you can interrogate.
 */
cJSON* cJSON_Parse(const char* value);
cJSON* cJSON_ParseWithLength(const char* value, size_t buffer_length);
/* ParseWithOpts allows you to require (and check) that the JSON is null
 * terminated, and to retrieve the pointer to the final byte parsed. */
/* If you supply a ptr in return_parse_end and parsing fails, then
 * return_parse_end will contain a pointer to the error so will match
 * cJSON_GetErrorPtr(). */
cJSON* cJSON_ParseWithOpts(const char* value, const char** return_parse_end,
                           cJSON_bool require_null_terminated);
cJSON* cJSON_ParseWithLengthOpts(const char* value, size_t buffer_length,
                                 const char** return_parse_end,
                                 cJSON_bool require_null_terminated);

/* Render a cJSON entity to text for transfer/storage. */
char* cJSON_Print(const cJSON* item);
/* Render a cJSON entity to text for transfer/storage without any formatting. */
char* cJSON_PrintUnformatted(const cJSON* item);
/* Render a cJSON entity to text using a buffered strategy. prebuffer is a guess
 * at the final size. guessing well reduces reallocation. fmt=0 gives
 * unformatted, =1 gives formatted */
char* cJSON_PrintBuffered(const cJSON* item, int prebuffer, cJSON_bool fmt);
/* Render a cJSON entity to text using a buffer already allocated in memory with
 * given length. Returns 1 on success and 0 on failure. */
/* NOTE: cJSON is not always 100% accurate in estimating how much memory it will
 * use, so to be safe allocate 5 bytes more than you actually need */
cJSON_bool cJSON_PrintPreallocated(cJSON* item, char* buffer, const int length,
                                   const cJSON_bool format);
/* Delete a cJSON entity and all subentities. */
void cJSON_Delete(cJSON* item);

/* Returns the number of items in an array (or object). */
int cJSON_GetArraySize(const cJSON* array);
/* Retrieve item number "index" from array "array". Returns NULL if
 * unsuccessful. */
cJSON* cJSON_GetArrayItem(const cJSON* array, int index);
/* Get item "string" from object. Case insensitive. */
cJSON* cJSON_GetObjectItem(const cJSON* const object, const char* const string);
cJSON* cJSON_GetObjectItemCaseSensitive(const cJSON* const object,
                                        const char* const string);
cJSON_bool cJSON_HasObjectItem(const cJSON* object, const char* string);
/* For analysing failed parses. This returns a pointer to the parse error.
 * You'll probably need to look a few chars back to make sense of it. Defined
 * when cJSON_Parse() returns 0. 0 when cJSON_Parse() succeeds. */
const char* cJSON_GetErrorPtr(void);

/* Check item type and return its value */
char* cJSON_GetStringValue(const cJSON* const item);
double cJSON_GetNumberValue(const cJSON* const item);

/* These functions check the type of an item */
cJSON_bool cJSON_IsInvalid(const cJSON* const item);
cJSON_bool cJSON_IsFalse(const cJSON* const item);
cJSON_bool cJSON_IsTrue(const cJSON* const item);
cJSON_bool cJSON_IsBool(const cJSON* const item);
cJSON_bool cJSON_IsNull(const cJSON* const item);
cJSON_bool cJSON_IsNumber(const cJSON* const item);
cJSON_bool cJSON_IsString(const cJSON* const item);
cJSON_bool cJSON_IsArray(const cJSON* const item);
cJSON_bool cJSON_IsObject(const cJSON* const item);
cJSON_bool cJSON_IsRaw(const cJSON* const item);

/* These calls create a cJSON item of the appropriate type. */
cJSON* cJSON_CreateNull(void);
cJSON* cJSON_CreateTrue(void);
cJSON* cJSON_CreateFalse(void);
cJSON* cJSON_CreateBool(cJSON_bool boolean);
cJSON* cJSON_CreateNumber(double num);
cJSON* cJSON_CreateString(const char* string);
/* raw json */
cJSON* cJSON_CreateRaw(const char* raw);
cJSON* cJSON_CreateArray(void);
cJSON* cJSON_CreateObject(void);

/* Create a string where valuestring references a string so
 * it will not be freed by cJSON_Delete */
cJSON* cJSON_CreateStringReference(const char* string);
/* Create an object/array that only references it's elements so
 * they will not be freed by cJSON_Delete */
cJSON* cJSON_CreateObjectReference(const cJSON* child);
cJSON* cJSON_CreateArrayReference(const cJSON* child);

/* These utilities create an Array of count items.
 * The parameter count cannot be greater than the number of elements in the
 * number array, otherwise array access will be out of bounds.*/
cJSON* cJSON_CreateIntArray(const int* numbers, int count);
cJSON* cJSON_CreateFloatArray(const float* numbers, int count);
cJSON* cJSON_CreateDoubleArray(const double* numbers, int count);
cJSON* cJSON_CreateStringArray(const char* const* strings, int count);

/* Append item to the specified array/object. */
cJSON_bool cJSON_AddItemToArray(cJSON* array, cJSON* item);
cJSON_bool cJSON_AddItemToObject(cJSON* object, const char* string,
                                 cJSON* item);
/* Use this when string is definitely const (i.e. a literal, or as good as), and
 * will definitely survive the cJSON object. WARNING: When this function was
 * used, make sure to always check that (item->type & cJSON_StringIsConst) is
 * zero before writing to `item->string` */
cJSON_bool cJSON_AddItemToObjectCS(cJSON* object, const char* string,
                                   cJSON* item);
/* Append reference to item to the specified array/object. Use this when you
 * want to add an existing cJSON to a new cJSON, but don't want to corrupt your
 * existing cJSON. */
cJSON_bool cJSON_AddItemReferenceToArray(cJSON* array, cJSON* item);
cJSON_bool cJSON_AddItemReferenceToObject(cJSON* object, const char* string,
                                          cJSON* item);

/* Remove/Detach items from Arrays/Objects. */
cJSON* cJSON_DetachItemViaPointer(cJSON* parent, cJSON* const item);
cJSON* cJSON_DetachItemFromArray(cJSON* array, int which);
void cJSON_DeleteItemFromArray(cJSON* array, int which);
cJSON* cJSON_DetachItemFromObject(cJSON* object, const char* string);
cJSON* cJSON_DetachItemFromObjectCaseSensitive(cJSON* object,
                                               const char* string);
void cJSON_DeleteItemFromObject(cJSON* object, const char* string);
void cJSON_DeleteItemFromObjectCaseSensitive(cJSON* object, const char* string);

/* Update array items. */
cJSON_bool cJSON_InsertItemInArray(
    cJSON* array, int which,
    cJSON* newitem); /* Shifts pre-existing items to the right. */
cJSON_bool cJSON_ReplaceItemViaPointer(cJSON* const parent, cJSON* const item,
                                       cJSON* replacement);
cJSON_bool cJSON_ReplaceItemInArray(cJSON* array, int which, cJSON* newitem);
cJSON_bool cJSON_ReplaceItemInObject(cJSON* object, const char* string,
                                     cJSON* newitem);
cJSON_bool cJSON_ReplaceItemInObjectCaseSensitive(cJSON* object,
                                                  const char* string,
                                                  cJSON* newitem);

/* Duplicate a cJSON item */
cJSON* cJSON_Duplicate(const cJSON* item, cJSON_bool recurse);
/* Duplicate will create a new, identical cJSON item to the one you pass, in new
 * memory that will need to be released. With recurse!=0, it will duplicate any
 * children connected to the item. The item->next and ->prev pointers are always
 * zero on return from Duplicate. */
/* Recursively compare two cJSON items for equality. If either a or b is NULL or
 * invalid, they will be considered unequal. case_sensitive determines if object
 * keys are treated case sensitive (1) or case insensitive (0) */
cJSON_bool cJSON_Compare(const cJSON* const a, const cJSON* const b,
                         const cJSON_bool case_sensitive);

/* Minify a strings, remove blank characters(such as ' ', '\t', '\r', '\n') from
 * strings. The input pointer json cannot point to a read-only address area,
 * such as a string constant, but should point to a readable and writable
 * address area. */
void cJSON_Minify(char* json);

/* Helper functions for creating and adding items to an object at the same time.
 * They return the added item or NULL on failure. */
cJSON* cJSON_AddNullToObject(cJSON* const object, const char* const name);
cJSON* cJSON_AddTrueToObject(cJSON* const object, const char* const name);
cJSON* cJSON_AddFalseToObject(cJSON* const object, const char* const name);
cJSON* cJSON_AddBoolToObject(cJSON* const object, const char* const name,
                             const cJSON_bool boolean);
cJSON* cJSON_AddNumberToObject(cJSON* const object, const char* const name,
                               const double number);
cJSON* cJSON_AddStringToObject(cJSON* const object, const char* const name,
                               const char* const string);
cJSON* cJSON_AddRawToObject(cJSON* const object, const char* const name,
                            const char* const raw);
cJSON* cJSON_AddObjectToObject(cJSON* const object, const char* const name);
cJSON* cJSON_AddArrayToObject(cJSON* const object, const char* const name);

/* When assigning an integer value, it needs to be propagated to valuedouble
 * too. */
#define cJSON_SetIntValue(object, number) \
  ((object) ? (object)->valueint = (object)->valuedouble = (number) : (number))
/* helper for the cJSON_SetNumberValue macro */
double cJSON_SetNumberHelper(cJSON* object, double number);
#define cJSON_SetNumberValue(object, number) \
  ((object != NULL) ? cJSON_SetNumberHelper(object, (double)number) : (number))
/* Change the valuestring of a cJSON_String object, only takes effect when type
 * of object is cJSON_String */
char* cJSON_SetValuestring(cJSON* object, const char* valuestring);

/* If the object is not a boolean type this does nothing and returns
 * cJSON_Invalid else it returns the new type*/
#define cJSON_SetBoolValue(object, boolValue)                              \
  ((object != NULL && ((object)->type & (cJSON_False | cJSON_True)))       \
       ? (object)->type = ((object)->type & (~(cJSON_False | cJSON_True))) \
                          | ((boolValue) ? cJSON_True : cJSON_False)       \
       : cJSON_Invalid)

/* Macro for iterating over an array or object */
#define cJSON_ArrayForEach(element, array)                                 \
  for (element = (array != NULL) ? (array)->child : NULL; element != NULL; \
       element = element->next)

/* malloc/free objects using the malloc/free functions that have been set with
 * cJSON_InitHooks */
void* cJSON_malloc(size_t size);
void cJSON_free(void* object);

// ericf addition: simple c++ wrappers for a few things here.

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

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_GENERIC_JSON_H_
