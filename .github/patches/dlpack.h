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

/* Data type codes (compatibility constants) */
typedef enum {
  kDLInt = 0,
  kDLUInt = 1,
  kDLFloat = 2,
  kDLOpaqueHandle = 3,
  kDLBfloat = 4,
  kDLBool = 5,
  /* extended / experimental codes (placeholders) */
  kDLFloat8_e3m4 = 128,
  kDLFloat8_e4m3 = 129,
  kDLFloat8_e4m3b11fnuz = 130,
  kDLFloat8_e4m3fn = 131,
  kDLFloat8_e4m3fnuz = 132,
  kDLFloat8_e5m2 = 133,
  kDLFloat8_e5m2fnuz = 134,
  kDLFloat8_e8m0fnu = 135,
  kDLFloat6_e2m3fn = 136,
  kDLFloat6_e3m2fn = 137
} DLDataTypeCode;

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

/* Versioned managed tensor used by some consumers */
typedef struct DLManagedTensorVersioned {
  DLTensor dl_tensor;
  void* manager_ctx;
  void (*deleter)(struct DLManagedTensorVersioned*);
  int version;
} DLManagedTensorVersioned;

#ifdef __cplusplus
}
#endif

