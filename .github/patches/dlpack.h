/* Minimal dlpack.h fallback for CI syntax check */
#pragma once

#ifdef __cplusplus
extern "C" {
#endif

typedef struct DLDevice {
  int device_type;
  int device_id;
} DLDevice;

#ifdef __cplusplus
}
#endif
