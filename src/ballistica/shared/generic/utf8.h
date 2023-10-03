// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SHARED_GENERIC_UTF8_H_
#define BALLISTICA_SHARED_GENERIC_UTF8_H_

#include <cstdarg>

#include "ballistica/shared/ballistica.h"

// ericf note: i think this is cutef8?...
namespace ballistica {

/* is c the start of a utf8 sequence? */
#define isutf(c) (((c) & 0xC0) != 0x80)

/* convert UTF-8 data to wide character */
auto u8_toucs(uint32_t* dest, int sz, const char* src, int srcsz) -> int;

/* the opposite conversion */
auto u8_toutf8(char* dest, int sz, const uint32_t* src, int srcsz) -> int;

/* single character to UTF-8 */
auto u8_wc_toutf8(char* dest, uint32_t ch) -> int;

/* character number to byte offset */
auto u8_offset(const char* str, int charnum) -> int;

/* byte offset to character number */
auto u8_charnum(const char* s, int offset) -> int;

/* return next character, updating an index variable */
auto u8_nextchar(const char* s, int* i) -> uint32_t;

/* move to next character */
void u8_inc(const char* s, int* i);

/* move to previous character */
void u8_dec(const char* s, int* i);

/* returns length of next utf-8 sequence */
auto u8_seqlen(const char* s) -> int;

/* assuming src points to the character after a backslash, read an
   escape sequence, storing the result in dest and returning the number of
   input characters processed */
auto u8_read_escape_sequence(char* src, uint32_t* dest) -> int;

/* given a wide character, convert it to an ASCII escape sequence stored in
   buf, where buf is "sz" bytes. returns the number of characters output. */
auto u8_escape_wchar(char* buf, int sz, uint32_t ch) -> int;

/* convert a string "src" containing escape sequences to UTF-8 */
auto u8_unescape(char* buf, int sz, char* src) -> int;

/* convert UTF-8 "src" to ASCII with escape sequences.
   if escape_quotes is nonzero, quote characters will be preceded by
   backslashes as well. */
auto u8_escape(char* buf, int sz, char* src, int escape_quotes) -> int;

/* utility predicates used by the above */
auto octal_digit(char c) -> int;
auto hex_digit(char c) -> int;

/* return a pointer to the first occurrence of ch in s, or NULL if not
   found. character index of found character returned in *charn. */
auto u8_strchr(char* s, uint32_t ch, int* charn) -> char*;

/* same as the above, but searches a buffer of a given size instead of
   a NUL-terminated string. */
auto u8_memchr(char* s, uint32_t ch, size_t sz, int* charn) -> char*;

/* count the number of characters in a UTF-8 string */
auto u8_strlen(const char* s) -> int;

auto u8_is_locale_utf8(const char* locale) -> int;

/* printf where the format string and arguments may be in UTF-8.
   you can avoid this function and just use ordinary printf() if the current
   locale is UTF-8. */
auto u8_vprintf(char* fmt, va_list ap) -> int;
auto u8_printf(char* fmt, ...) -> int;

}  // namespace ballistica

#endif  // BALLISTICA_SHARED_GENERIC_UTF8_H_
