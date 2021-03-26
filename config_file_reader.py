import yaml
import globals
import logging
import sys


def log_options(corrupt_locations):
    logging.info("")
    logging.info("********** Options **********")
    logging.info(" " + globals.STR_HDF5_FILE + ": " + str(globals.HDF5_FILE))
    logging.info(" " + globals.STR_INJECTION_PROBABILITY + ": " + str(globals.INJECTION_PROBABILITY))
    logging.info(" " + globals.STR_INJECTION_TYPE + ": " + str(globals.INJECTION_TYPE))
    logging.info(" " + globals.STR_INJECTION_TRIES + ": " + str(globals.INJECTION_TRIES))
    logging.info(" " + globals.STR_FIRST_BYTE + ": " + str(globals.FIRST_BYTE))
    logging.info(" " + globals.STR_LAST_BYTE + ": " + str(globals.LAST_BYTE))
    logging.info(" " + globals.STR_BIT + ": " + str(globals.BIT))
    logging.info(" " + globals.STR_ALLOW_NaN_VALUES + ": " + str(globals.ALLOW_NaN_VALUES))
    logging.info(" " + globals.STR_USE_RANDOM_LOCATIONS + ": " + str(globals.USE_RANDOM_LOCATIONS))
    logging.info(" " + globals.STR_LOCATIONS_TO_CORRUPT + ":")
    for location in corrupt_locations:
        logging.info("  " + str(location))
    logging.info("********** ------- **********")
    logging.info("")


def read_config_file(config_file_path: str):
    with open(config_file_path) as f:
        logging.info("Reading config file: " + config_file_path)
        data = yaml.load(f, Loader=yaml.Loader)
        globals.HDF5_FILE = data[globals.STR_HDF5_FILE]

        globals.INJECTION_PROBABILITY = float(data[globals.STR_INJECTION_PROBABILITY])
        # read from config file, only if it was not given as an argument
        if globals.INJECTION_TYPE == "":
            globals.INJECTION_TYPE = data[globals.STR_INJECTION_TYPE]

        # read from config file, only if it was not given as an argument
        if globals.INJECTION_TRIES == -1:
            globals.INJECTION_TRIES = float(data[globals.STR_INJECTION_TRIES])

        globals.FIRST_BYTE = int(data[globals.STR_FIRST_BYTE])
        globals.LAST_BYTE = int(data[globals.STR_LAST_BYTE])
        globals.BIT = int(data[globals.STR_BIT])
        globals.ALLOW_NaN_VALUES = bool(data[globals.STR_ALLOW_NaN_VALUES])
        globals.USE_RANDOM_LOCATIONS = bool(data[globals.STR_USE_RANDOM_LOCATIONS])
        globals.LOCATIONS_TO_CORRUPT = data[globals.STR_LOCATIONS_TO_CORRUPT]
        log_options(globals.LOCATIONS_TO_CORRUPT)

    # making the byte interval considering -1
    globals.FIRST_BYTE = 0 if globals.FIRST_BYTE == -1 else globals.FIRST_BYTE
    globals.LAST_BYTE = 7 if globals.LAST_BYTE == -1 else globals.LAST_BYTE

    check_for_error_in_values()


def check_for_error_in_values():
    if \
            globals.FIRST_BYTE > globals.LAST_BYTE or \
            (globals.FIRST_BYTE < 0 and globals.FIRST_BYTE != -1) or \
            globals.FIRST_BYTE > 7 or \
            (globals.LAST_BYTE < 0 and globals.LAST_BYTE != -1) or \
            globals.LAST_BYTE > 7:
        logging.error("first_byte and last_byte must be an interval between [0-7] or -1 for random")
        sys.exit(2)

    if (globals.BIT < 0 and globals.BIT != -1) or \
            globals.BIT > 7:
        logging.error("bit must be a value between [0-7] or -1 for random")
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

    # and implement the functionality when corruption type is count