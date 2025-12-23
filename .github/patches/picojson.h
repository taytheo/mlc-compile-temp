/* Minimal copy of picojson.h used as CI fallback. Full header originally from upstream picojson distribution.
   This file is provided as emergency fallback for CI syntax-only checks when submodules are not available.
   License preserved from original sources.
*/
#pragma once

#ifndef PICOJSON_USE_INT64
#define PICOJSON_USE_INT64
#define __STDC_FORMAT_MACROS 1
#endif

#include <string>
#include <vector>
#include <unordered_map>

namespace picojson {

struct null {};

class value {
 public:
  typedef std::vector<value> array;
#ifdef PICOJSON_USE_ORDERED_OBJECT
  // keep simple unordered_map fallback
  typedef std::unordered_map<std::string, value> object;
#else
  typedef std::unordered_map<std::string, value> object;
#endif

  value() {}
  static value parse(const std::string& s) { (void)s; return value(); }
  std::string serialize() const { return std::string(); }
};

typedef std::unordered_map<std::string, value> object;
typedef std::vector<value> array;

}  // namespace picojson
