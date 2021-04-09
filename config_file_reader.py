import yaml
import globals
import logging
import sys


def log_options():
    logging.info("")
    logging.info("********** Options **********")
    logging.info(" " + globals.STR_HDF5_FILE + ": " + str(globals.HDF5_FILE))
    logging.info(" " + globals.STR_LOG_FILE_PATH + ": " + str(globals.LOG_FILE_PATH))
    logging.info(" " + globals.STR_INJECTION_PROBABILITY + ": " + str(globals.INJECTION_PROBABILITY))
    logging.info(" " + globals.STR_INJECTION_TYPE + ": " + str(globals.INJECTION_TYPE))
    logging.info(" " + globals.STR_INJECTION_TRIES + ": " + str(globals.INJECTION_TRIES))
    logging.info(" " + globals.STR_FIRST_BIT + ": " + str(globals.FIRST_BIT))
    logging.info(" " + globals.STR_LAST_BIT + ": " + str(globals.LAST_BIT))
    logging.info(" " + globals.STR_ALLOW_SIGN_CHANGE + ": " + str(globals.ALLOW_SIGN_CHANGE))
    logging.info(" " + globals.STR_ALLOW_NaN_VALUES + ": " + str(globals.ALLOW_NaN_VALUES))
    logging.info(" " + globals.STR_USE_RANDOM_LOCATIONS + ": " + str(globals.USE_RANDOM_LOCATIONS))
    logging.info(" " + globals.STR_LOCATIONS_TO_CORRUPT + ":")
    for location in globals.LOCATIONS_TO_CORRUPT:
        logging.info("  " + str(location))
    logging.info("********** ------- **********")
    logging.info("")


def read_config_file(config_file_path: str):
    with open(config_file_path) as f:
        data = yaml.load(f, Loader=yaml.Loader)

        # read values from config file, only if not given via arguments
        if globals.HDF5_FILE == "":
            globals.HDF5_FILE = data[globals.STR_HDF5_FILE]

        if globals.LOG_FILE_PATH == "":
            globals.LOG_FILE_PATH = data[globals.STR_LOG_FILE_PATH]

        if not globals.LOG_FILE_PATH.endswith('/'):
            globals.LOG_FILE_PATH += "/"

        if globals.INJECTION_PROBABILITY == -1:
            globals.INJECTION_PROBABILITY = float(data[globals.STR_INJECTION_PROBABILITY])

        if globals.INJECTION_TYPE == "":
            globals.INJECTION_TYPE = data[globals.STR_INJECTION_TYPE]

        if globals.INJECTION_TRIES == -1:
            globals.INJECTION_TRIES = float(data[globals.STR_INJECTION_TRIES])

        # values only available through config file
        globals.FIRST_BIT = int(data[globals.STR_FIRST_BIT])
        globals.LAST_BIT = int(data[globals.STR_LAST_BIT])
        globals.ALLOW_SIGN_CHANGE = bool(data[globals.STR_ALLOW_SIGN_CHANGE])
        globals.ALLOW_NaN_VALUES = bool(data[globals.STR_ALLOW_NaN_VALUES])
        globals.USE_RANDOM_LOCATIONS = bool(data[globals.STR_USE_RANDOM_LOCATIONS])
        globals.LOCATIONS_TO_CORRUPT = data[globals.STR_LOCATIONS_TO_CORRUPT]

        # if first bit (sign-bit) not in range, then increase by 1 the start of range
        if globals.ALLOW_SIGN_CHANGE and globals.FIRST_BIT > 0:
            globals.FIRST_BIT -= 1


def check_for_error_in_values():
    if \
            globals.FIRST_BIT > globals.LAST_BIT or \
            globals.FIRST_BIT < 0 or \
            globals.FIRST_BIT > 63 or \
            globals.LAST_BIT < 0 or \
            globals.LAST_BIT > 63:
        logging.error("first_bit and last_bit must be an interval between [0-63]")
        sys.exit(2)

    if globals.INJECTION_TYPE not in globals.CORRUPTION_TYPE_VALUES:
        logging.error("Corruption type not recognized. It must be either \"percentage\" or \"count\"")
        sys.exit(2)

    if globals.INJECTION_TYPE == globals.STR_PERCENTAGE and \
            (globals.INJECTION_TRIES < 0 or globals.INJECTION_TRIES > 1):
        logging.error("Injection tries for corruption type \"percentage\" must be a value between [0-1]")
        sys.exit(2)

    if globals.INJECTION_TYPE == globals.STR_COUNT:
        # truncate to integer value
        int_value = int(globals.INJECTION_TRIES)
        logging.info("Truncating  " + str(globals.INJECTION_TRIES) + " to " + str(int_value))
        globals.INJECTION_TRIES = int_value

        if globals.INJECTION_TRIES < 1:
            logging.error("Injection tries for corruption type \"count\" must be a positive integer")
            sys.exit(2)