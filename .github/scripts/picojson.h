/* Minimal copy of picojson.h used as CI fallback (scripts copy). */
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
  typedef std::unordered_map<std::string, value> object;

  value() {}
  static value parse(const std::string& s) { (void)s; return value(); }
  std::string serialize() const { return std::string(); }
};

typedef std::unordered_map<std::string, value> object;
typedef std::vector<value> array;

}  // namespace picojson
