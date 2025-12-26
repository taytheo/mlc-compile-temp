/* Minimal DLPack header for CI syntax checks. Not a full implementation, only
   the types required by tvm-ffi for building sources in syntax-only checks.
   Derived for compatibility with DLPack v1.* interfaces. */
#pragma once

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Device types */
typedef enum {
  kDLCPU = 1,
  kDLCUDA = 2,
  kDLCUDAHost = 3,
  kDLOpenCL = 4,
  kDLVulkan = 7,
  kDLMetal = 8,
  kDLVPI = 9,
  kDLROCM = 10,
  kDLROCMHost = 11,
  kDLExtDev = 12
} DLDeviceType;

typedef struct DLDevice {
  int device_type; /* DLDeviceType but keep as int for compatibility */
  int device_id;
} DLDevice;

/* Data type description */
typedef struct DLDataType {
  uint8_t code;   /* Type code, e.g., kDLFloat, kDLInt, ... */
  uint8_t bits;   /* Number of bits for the type */
  uint16_t lanes; /* Number of lanes for vector types */
} DLDataType;

/* DLTensor */
typedef struct DLTensor {
  void* data;
  DLDevice device;
  int ndim;
  DLDataType dtype;
  int64_t* shape;
  int64_t* strides; /* can be NULL */
  uint64_t byte_offset;
} DLTensor;

/* Managed tensor with deleter */
typedef struct DLManagedTensor {
  DLTensor dl_tensor;
  void* manager_ctx;
  void (*deleter)(struct DLManagedTensor*);
} DLManagedTensor;

#ifdef __cplusplus
}
#endif

