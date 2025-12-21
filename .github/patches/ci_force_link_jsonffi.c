// Small C file used by CI to force-embed a recognizable symbol/string into
// compiled object files when the patched json_ffi unit is not included in
// the system-built objects. This is only used as a last-resort fallback to
// make debugging easier and satisfy CI presence checks.

#include <stdint.h>

#if defined(__APPLE__)
__attribute__((used)) __attribute__((visibility("default")))
#else
__attribute__((used))
#endif
const char* MLCJSONFFIEngineForceLink = "MLCJSONFFIEngineForceLink_v1";
