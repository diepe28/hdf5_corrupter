from dataclasses import dataclass

ONLY_PRINT = False

INJECTION_PROBABILITY = -1
INJECTION_PROBABILITY_STR = "injection_probability"

INJECTION_TYPE = ""
INJECTION_TYPE_STR = "injection_type"
COUNT_STR = "count"
PERCENTAGE_STR = "percentage"
INJECTION_TYPE_VALUES = [PERCENTAGE_STR, COUNT_STR]

INJECTION_TRIES = -1
INJECTION_TRIES_STR = "injection_tries"

FIRST_BIT = 0
FIRST_BIT_STR = "first_bit"

LAST_BIT = 63
LAST_BIT_STR = "last_bit"

ALLOW_SIGN_CHANGE = True
ALLOW_SIGN_CHANGE_STR = "allow_sign_change"

USE_RANDOM_LOCATIONS = True
USE_RANDOM_LOCATIONS_STR = "use_random_locations"

ALLOW_NaN_VALUES = False
ALLOW_NaN_VALUES_STR = "allow_NaN_values"

ALL_LOCATIONS = []
LOCATIONS_TO_CORRUPT = []
LOCATIONS_TO_CORRUPT_STR = "locations_to_corrupt"

HDF5_FILE = ""
HDF5_FILE_STR = "hdf5_file"

LOG_FILE_PATH = ""
LOG_FILE_PATH_STR = "log_file_path"

SAVE_INJECTION_SEQUENCE = -1
SAVE_INJECTION_SEQUENCE_STR = "save_injection_sequence"

INJECTION_SEQUENCE = {}
