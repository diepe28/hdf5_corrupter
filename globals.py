from dataclasses import dataclass

ONLY_PRINT = False
CONFIG_FILE_PATH = ""

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

# a list of all the full paths of the hdf5 file
ALL_LOCATIONS = []
# the list of the base (prefix) locations given in the config file
BASE_LOCATIONS = []
# the actual list of corruptible locations
LOCATIONS_TO_CORRUPT = []
LOCATIONS_TO_CORRUPT_STR = "locations_to_corrupt"

HDF5_FILE = ""
HDF5_FILE_STR = "hdf5_file"

LOG_FILE_PATH = ""
LOG_FILE_PATH_STR = "log_file_path"

SAVE_INJECTION_SEQUENCE = False
SAVE_INJECTION_SEQUENCE_STR = "save_injection_sequence"

INJECTION_SEQUENCE_PATH = ""
INJECTION_SEQUENCE_PATH_STR = "injection_sequence_path"
INJECTION_SEQUENCE = {}
