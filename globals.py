from enum import Enum

ARG_PARSER = None

ONLY_PRINT = False
CONFIG_FILE_PATH = ""

INJECTION_PROBABILITY = 1
INJECTION_PROBABILITY_STR = "injection_probability"

INJECTION_TYPE = ""
INJECTION_TYPE_STR = "injection_type"
COUNT_STR = "count"
PERCENTAGE_STR = "percentage"
INJECTION_TYPE_VALUES = [PERCENTAGE_STR, COUNT_STR]

INJECTION_TRIES = -1
INJECTION_TRIES_STR = "injection_tries"

FIRST_BIT = None
FIRST_BIT_STR = "first_bit"

LAST_BIT = None
LAST_BIT_STR = "last_bit"

ALLOW_SIGN_CHANGE = True
ALLOW_SIGN_CHANGE_STR = "allow_sign_change"

USE_RANDOM_LOCATIONS = False
USE_RANDOM_LOCATIONS_STR = "use_random_locations"

ALLOW_NaN_VALUES = False
ALLOW_NaN_VALUES_STR = "allow_NaN_values"

# a list of all the full paths of the hdf5 file
ALL_LOCATIONS = []
# the list of the base (prefix) locations given in the config file
BASE_LOCATIONS = []
# the actual list of corruptible locations
LOCATIONS_TO_CORRUPT = []
LOCATIONS_TO_CORRUPT_STR = "locations_to_corrupt"

HDF5_FILE = None
HDF5_FILE_STR = "hdf5_file"

LOG_FILE_PATH = ""
LOG_FILE_PATH_STR = "log_file_path"

SAVE_INJECTION_SEQUENCE = False
SAVE_INJECTION_SEQUENCE_STR = "save_injection_sequence"

LOAD_INJECTION_SEQUENCE = False
LOAD_INJECTION_SEQUENCE_STR = "load_injection_sequence"

INJECTION_SEQUENCE_PATH = ""
INJECTION_SEQUENCE_PATH_STR = "injection_sequence_path"
INJECTION_SEQUENCE_SAVE_INDEXES = False
INJECTION_SEQUENCE = {}

SCALING_FACTOR = None
SCALING_FACTOR_STR = "scaling_factor"

BURST = 1
BURST_STR = "burst"

BIT_MASK = None
BIT_MASK_STR = "bit_mask"

FLOAT_PRECISION = None
FLOAT_PRECISION_STR = "float_precision"

PRECISION_CODE = None
BYTES_PER_FLOAT = None


def set_precision_settings(float_precision_val):
    """
    Sets the precision settings based on the given precision
    :param float_precision_val: The current float precision
    """
    global BYTES_PER_FLOAT
    global PRECISION_CODE
    if float_precision_val == 64:
        BYTES_PER_FLOAT = 8
        PRECISION_CODE = '!d'
    elif float_precision_val == 32:
        BYTES_PER_FLOAT = 4
        PRECISION_CODE = '!f'
    else:
        BYTES_PER_FLOAT = 2
        PRECISION_CODE = '!e'


# Error Messages
class SettingErrors(Enum):
    MISSING_HDF5_FILE = 1
    MISSING_LOCATIONS_TO_CORRUPT = 2
    WRONG_FLOAT_PRECISION = 3
    WRONG_BIT_RANGE = 4
    WRONG_INJECTION_TYPE = 5
    WRONG_PERCENTAGE_INJECTION_TRIES = 6
    WRONG_COUNT_INJECTION_TRIES = 7
    WRONG_INJECTION_BURST = 8
    WRONG_BIT_MASK = 9
    INCOMPATIBLE_INJECTION_MODE = 10
    INCOMPATIBLE_INJECTION_SEQUENCE_WITH_NO_BIT_RANGE = 11
    INCOMPATIBLE_INJECTION_SEQUENCE_READ_WRITE = 12


ERRORS = {
    SettingErrors.MISSING_HDF5_FILE: "HDF5 file must be provided",
    SettingErrors.MISSING_LOCATIONS_TO_CORRUPT: "",
    SettingErrors.WRONG_FLOAT_PRECISION: "Float precision must be submitted and must be 16, 32, 64 or auto",
    SettingErrors.WRONG_BIT_RANGE: "",
    SettingErrors.WRONG_INJECTION_TYPE: "",
    SettingErrors.WRONG_PERCENTAGE_INJECTION_TRIES: "",
    SettingErrors.WRONG_COUNT_INJECTION_TRIES: "",
    SettingErrors.WRONG_INJECTION_BURST: "",
    SettingErrors.WRONG_BIT_MASK: "",
    SettingErrors.INCOMPATIBLE_INJECTION_MODE: "",
    SettingErrors.INCOMPATIBLE_INJECTION_SEQUENCE_WITH_NO_BIT_RANGE: "",
    SettingErrors.INCOMPATIBLE_INJECTION_SEQUENCE_READ_WRITE: ""
}



