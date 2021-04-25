import yaml
import globals
import logging
import sys

import hdf5_common


def log_options():
    logging.info("")
    logging.info("********** Options **********")
    logging.info(" " + globals.HDF5_FILE_STR + ": " + str(globals.HDF5_FILE))
    logging.info(" " + globals.LOG_FILE_PATH_STR + ": " + str(globals.LOG_FILE_PATH))
    logging.info(" " + globals.INJECTION_PROBABILITY_STR + ": " + str(globals.INJECTION_PROBABILITY))
    logging.info(" " + globals.INJECTION_TYPE_STR + ": " + str(globals.INJECTION_TYPE))
    logging.info(" " + globals.INJECTION_TRIES_STR + ": " + str(globals.INJECTION_TRIES))
    logging.info(" " + globals.FIRST_BIT_STR + ": " + str(globals.FIRST_BIT))
    logging.info(" " + globals.LAST_BIT_STR + ": " + str(globals.LAST_BIT))
    logging.info(" " + globals.ALLOW_SIGN_CHANGE_STR + ": " + str(globals.ALLOW_SIGN_CHANGE))
    logging.info(" " + globals.ALLOW_NaN_VALUES_STR + ": " + str(globals.ALLOW_NaN_VALUES))
    if globals.SAVE_INJECTION_SEQUENCE:
        logging.info(" " + globals.SAVE_INJECTION_SEQUENCE_STR + ": TRUE")
    if globals.INJECTION_SEQUENCE_PATH != "":
        logging.info(" Using injection sequence from file: " + str(globals.INJECTION_SEQUENCE_PATH))
    logging.info(" " + globals.USE_RANDOM_LOCATIONS_STR + ": " + str(globals.USE_RANDOM_LOCATIONS))
    logging.info(" " + globals.LOCATIONS_TO_CORRUPT_STR + ":")
    for location in globals.LOCATIONS_TO_CORRUPT:
        logging.info("  " + str(location))
    logging.info("********** ------- **********")
    logging.info("")


def read_config_file(config_file_path: str):
    with open(config_file_path) as f:
        data = yaml.load(f, Loader=yaml.Loader)

        # read values from config file, only if not given via arguments
        if globals.HDF5_FILE == "":
            globals.HDF5_FILE = data[globals.HDF5_FILE_STR]

        if globals.LOG_FILE_PATH == "":
            globals.LOG_FILE_PATH = data[globals.LOG_FILE_PATH_STR]

        if globals.INJECTION_PROBABILITY == -1:
            globals.INJECTION_PROBABILITY = float(data[globals.INJECTION_PROBABILITY_STR])

        if globals.INJECTION_TYPE == "":
            globals.INJECTION_TYPE = data[globals.INJECTION_TYPE_STR]

        if globals.INJECTION_TRIES == -1:
            globals.INJECTION_TRIES = float(data[globals.INJECTION_TRIES_STR])

        if globals.SAVE_INJECTION_SEQUENCE_STR in data and not globals.SAVE_INJECTION_SEQUENCE:
            globals.SAVE_INJECTION_SEQUENCE = bool(data[globals.SAVE_INJECTION_SEQUENCE_STR])

        if globals.INJECTION_SEQUENCE_PATH_STR in data and globals.INJECTION_SEQUENCE_PATH == "":
            globals.INJECTION_SEQUENCE_PATH = data[globals.INJECTION_SEQUENCE_PATH_STR]

        # values only available through config file
        globals.FIRST_BIT = int(data[globals.FIRST_BIT_STR])
        globals.LAST_BIT = int(data[globals.LAST_BIT_STR])
        globals.ALLOW_SIGN_CHANGE = bool(data[globals.ALLOW_SIGN_CHANGE_STR])
        globals.ALLOW_NaN_VALUES = bool(data[globals.ALLOW_NaN_VALUES_STR])
        globals.USE_RANDOM_LOCATIONS = bool(data[globals.USE_RANDOM_LOCATIONS_STR])
        globals.LOCATIONS_TO_CORRUPT = data[globals.LOCATIONS_TO_CORRUPT_STR]


def check_for_error_in_values():
    if \
            globals.FIRST_BIT > globals.LAST_BIT or \
            globals.FIRST_BIT < 0 or \
            globals.FIRST_BIT > 63 or \
            globals.LAST_BIT < 0 or \
            globals.LAST_BIT > 63:
        hdf5_common.handle_error("first_bit and last_bit must be an interval between [0-63]")

    if globals.INJECTION_TYPE not in globals.INJECTION_TYPE_VALUES:
        hdf5_common.handle_error("Injection type not recognized. It must be either \"percentage\" or \"count\"")

    if globals.INJECTION_TYPE == globals.PERCENTAGE_STR and \
            (globals.INJECTION_TRIES < 0 or globals.INJECTION_TRIES > 1):
        hdf5_common.handle_error("Injection tries for corruption type \"percentage\" must be a value between [0-1]")

    if globals.INJECTION_TYPE == globals.COUNT_STR:
        # truncate to integer value
        int_value = int(globals.INJECTION_TRIES)
        logging.info("Truncating  " + str(globals.INJECTION_TRIES) + " to " + str(int_value))
        globals.INJECTION_TRIES = int_value

        if globals.INJECTION_TRIES < 1:
            hdf5_common.handle_error("Injection tries for corruption type \"count\" must be a positive integer")

    if globals.SAVE_INJECTION_SEQUENCE and globals.INJECTION_SEQUENCE_PATH != "":
        hdf5_common.handle_error("'saveInjectionSequence' and 'injectionSequencePath' are incompatible options")
