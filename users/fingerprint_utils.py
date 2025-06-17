import ctypes
import base64
import threading
import time
from ctypes import c_char, c_int, c_ubyte, c_uint, c_void_p, byref, create_string_buffer, POINTER, CFUNCTYPE

# Constants from the SDK headers
DPFPDD_SUCCESS = 0
DPFPDD_E_MORE_DATA = -2147483635
DPFJ_FMD_ANSI_378_2004 = 0x001B0001
DPFPDD_IMG_FMT_PIXEL_BUFFER = 0
DPFPDD_IMG_PROC_DEFAULT = 0
MAX_FMD_SIZE = 1590  # As defined in dpfj.h

# Structures from the SDK headers
class DPFPDD_DEV_INFO(ctypes.Structure):
    _fields_ = [
        ("size", c_uint),
        ("name", c_char * 1024),
        # ... other fields if needed
    ]

class DPFPDD_CAPTURE_PARAM(ctypes.Structure):
    _fields_ = [
        ("size", c_uint),
        ("image_fmt", c_uint),
        ("image_proc", c_uint),
        ("image_res", c_uint),
    ]

class DPFPDD_CAPTURE_RESULT(ctypes.Structure):
    _fields_ = [
        ("size", c_uint),
        ("success", c_int),
        ("quality", c_uint),
        ("score", c_uint),
        ("info", c_void_p), # Simplified for this example
    ]

class Fingerprint:
    def __init__(self):
        self.dpfpdd = None
        self.dpfj = None
        self.dev = c_void_p(None)
        self.dev_info = DPFPDD_DEV_INFO()
        self.dev_info.size = ctypes.sizeof(self.dev_info)
        self._load_libraries()
        self._initialize_device()

    def _load_libraries(self):
        try:
            # Load the SDK libraries
            self.dpfpdd = ctypes.WinDLL(r"C:\Program Files\DigitalPersona\U.are.U SDK\Windows\Lib\x64\dpfpdd.dll")
            self.dpfj = ctypes.WinDLL(r"C:\Program Files\DigitalPersona\U.are.U SDK\Windows\Lib\x64\dpfj.dll")
        except (WindowsError, ImportError):
            raise ImportError("Could not load DigitalPersona SDK libraries. This may be due to a 32-bit/64-bit architecture mismatch or an incorrect SDK installation.")

    def _initialize_device(self):
        if self.dpfpdd.dpfpdd_init() != DPFPDD_SUCCESS:
            raise Exception("Failed to initialize DigitalPersona SDK.")

        dev_count = c_uint(1)
        if self.dpfpdd.dpfpdd_query_devices(byref(dev_count), byref(self.dev_info)) != DPFPDD_SUCCESS:
            self.dpfpdd.dpfpdd_exit()
            raise Exception("No fingerprint reader found.")

        if self.dpfpdd.dpfpdd_open(self.dev_info.name, byref(self.dev)) != DPFPDD_SUCCESS:
            self.dpfpdd.dpfpdd_exit()
            raise Exception("Failed to open fingerprint reader.")

    def enroll_finger(self):
        """Captures a fingerprint and returns the FMD (Fingerprint Minutiae Data)."""
        fmd_buffer = create_string_buffer(MAX_FMD_SIZE)
        fmd_size = c_uint(MAX_FMD_SIZE)

        capture_param = DPFPDD_CAPTURE_PARAM(
            size=ctypes.sizeof(DPFPDD_CAPTURE_PARAM),
            image_fmt=DPFPDD_IMG_FMT_PIXEL_BUFFER,
            image_proc=DPFPDD_IMG_PROC_DEFAULT,
            image_res=500  # Standard resolution
        )
        capture_result = DPFPDD_CAPTURE_RESULT()
        capture_result.size = ctypes.sizeof(capture_result)
        image_buffer_size = c_uint(0)
        
        # First call to get the required image buffer size
        if self.dpfpdd.dpfpdd_capture(self.dev, byref(capture_param), -1, byref(capture_result), byref(image_buffer_size), None) != DPFPDD_E_MORE_DATA:
            raise Exception("Failed to get image buffer size.")

        image_buffer = create_string_buffer(image_buffer_size.value)

        # Second call to actually capture the image
        if self.dpfpdd.dpfpdd_capture(self.dev, byref(capture_param), -1, byref(capture_result), byref(image_buffer_size), image_buffer) != DPFPDD_SUCCESS:
            raise Exception("Failed to capture fingerprint.")

        if not capture_result.success:
            raise Exception(f"Fingerprint capture failed with quality: {capture_result.quality}")

        # Extract features to create FMD
        if self.dpfj.dpfj_create_fmd_from_raw(image_buffer, image_buffer_size.value, 500, 500, 500, 0, 0, DPFJ_FMD_ANSI_378_2004, fmd_buffer, byref(fmd_size)) != DPFPDD_SUCCESS:
            raise Exception("Failed to create FMD from raw image.")

        return fmd_buffer.raw[:fmd_size.value]

    def identify_finger(self, fmds_to_compare, scanned_fmd_b64):
        """
        Compares a newly captured fingerprint against a list of existing FMDs.
        Returns the index of the matching FMD in the list, or None if no match is found.
        """
        # Decode the base64url encoded fmd
        scanned_fmd = base64.urlsafe_b64decode(scanned_fmd_b64)

        # Prepare the array of FMD pointers for the identify function
        fmd_array = (ctypes.POINTER(c_ubyte) * len(fmds_to_compare))()
        fmd_size_array = (c_uint * len(fmds_to_compare))()

        for i, fmd_data in enumerate(fmds_to_compare):
            fmd_buffer = create_string_buffer(fmd_data)
            fmd_array[i] = ctypes.cast(fmd_buffer, ctypes.POINTER(c_ubyte))
            fmd_size_array[i] = len(fmd_data)

        class DPFJ_CANDIDATE(ctypes.Structure):
            _fields_ = [("size", c_uint), ("fmd_idx", c_uint), ("view_idx", c_uint)]

        candidate_count = c_uint(1)
        candidates = (DPFJ_CANDIDATE * 1)()
        candidates[0].size = ctypes.sizeof(DPFJ_CANDIDATE)
        
        # The threshold needs to be determined from the SDK documentation or experimentation.
        # A lower value means a stricter match.
        threshold = 2147483647 // 10  # Example threshold

        result = self.dpfj.dpfj_identify(
            DPFJ_FMD_ANSI_378_2004, scanned_fmd, len(scanned_fmd), 0,
            DPFJ_FMD_ANSI_378_2004, len(fmds_to_compare), fmd_array, fmd_size_array,
            threshold, byref(candidate_count), candidates
        )

        if result == DPFPDD_SUCCESS and candidate_count.value > 0:
            return candidates[0].fmd_idx
        
        return None

    def __del__(self):
        if self.dev and self.dpfpdd:
            self.dpfpdd.dpfpdd_close(self.dev)
        if self.dpfpdd:
            self.dpfpdd.dpfpdd_exit()