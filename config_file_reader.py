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
    logging.info(" " + globals.FLOAT_PRECISION_STR + ": " + str(globals.FLOAT_PRECISION))
    logging.info(" " + globals.FIRST_BIT_STR + ": " + str(globals.FIRST_BIT))
    logging.info(" " + globals.LAST_BIT_STR + ": " + str(globals.LAST_BIT))
    if globals.BURST is not None:
        logging.info(" Injection burst (num of changed bits per value): " + str(globals.BURST))
    logging.info(" " + globals.ALLOW_SIGN_CHANGE_STR + ": " + str(globals.ALLOW_SIGN_CHANGE))
    logging.info(" " + globals.ALLOW_NaN_VALUES_STR + ": " + str(globals.ALLOW_NaN_VALUES))

    if globals.SCALING_FACTOR is not None:
        logging.info(" [WARNING] Ignoring bit range and burst value, using scaling factor: " +
                     str(globals.SCALING_FACTOR))

    if globals.BIT_MASK is not None:
        logging.info(" [WARNING] Ignoring bit range, burst value, using bit mask: " +
                     str(globals.BIT_MASK))

    if globals.SAVE_INJECTION_SEQUENCE:
        logging.info(" " + globals.SAVE_INJECTION_SEQUENCE_STR + ": TRUE")
    if globals.INJECTION_SEQUENCE_PATH != "":
        logging.info(" [WARNING] Ignoring corruption settings. Using injection sequence from file: " +
                     str(globals.INJECTION_SEQUENCE_PATH))
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

        if globals.FLOAT_PRECISION_STR in data and globals.FLOAT_PRECISION is None:
            globals.FLOAT_PRECISION = int(data[globals.FLOAT_PRECISION_STR])

        if globals.SCALING_FACTOR_STR in data and globals.SCALING_FACTOR is None:
            globals.SCALING_FACTOR = float(data[globals.SCALING_FACTOR_STR])

        if globals.BIT_MASK_STR in data and globals.BIT_MASK is None:
            globals.BIT_MASK = data[globals.BIT_MASK_STR]

        if globals.FIRST_BIT_STR in data and globals.FIRST_BIT is None:
            globals.FIRST_BIT = int(data[globals.FIRST_BIT_STR])

        if globals.LAST_BIT_STR in data and globals.LAST_BIT is None:
            globals.LAST_BIT = int(data[globals.LAST_BIT_STR])

        if globals.BURST is None:
            if globals.BURST_STR in data:
                globals.BURST = int(data[globals.BURST_STR])
            else:
                if globals.FIRST_BIT is not None and globals.LAST_BIT:
                    globals.BURST = 1  # default value: 1 injection attempt per value

        # values only available through config file
        globals.ALLOW_SIGN_CHANGE = bool(data[globals.ALLOW_SIGN_CHANGE_STR])
        globals.ALLOW_NaN_VALUES = bool(data[globals.ALLOW_NaN_VALUES_STR])
        globals.USE_RANDOM_LOCATIONS = bool(data[globals.USE_RANDOM_LOCATIONS_STR])
        globals.LOCATIONS_TO_CORRUPT = data[globals.LOCATIONS_TO_CORRUPT_STR]


def check_for_error_in_values():
    if globals.FLOAT_PRECISION is None or (globals.FLOAT_PRECISION != 32 and globals.FLOAT_PRECISION != 64):
        hdf5_common.handle_error("Float precision must be submitted and must be 32 or 64")

    if globals.FIRST_BIT is not None and globals.LAST_BIT is not None and\
            (globals.FIRST_BIT > globals.LAST_BIT or
             globals.FIRST_BIT < 0 or
             globals.FIRST_BIT > globals.FLOAT_PRECISION - 1 or
             globals.LAST_BIT < 0 or
             globals.LAST_BIT > globals.FLOAT_PRECISION - 1):
        hdf5_common.handle_error("first_bit and last_bit must be an interval between"
                                 " [0-" + globals.FLOAT_PRECISION - 1 + "]")

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

    if globals.BURST is not None and globals.BURST < 1:
        hdf5_common.handle_error("Injection burst must be a positive integer")

    incompatible_settings = 0
    if globals.BURST is not None or globals.FIRST_BIT is not None or globals.LAST_BIT is not None:
        incompatible_settings += 1
    if globals.SCALING_FACTOR is not None:
        incompatible_settings += 1
    if globals.BIT_MASK is not None:
        if len(globals.BIT_MASK) > globals.FLOAT_PRECISION:
            hdf5_common.handle_error("Length of bit mask must be <= float_precision")
        incompatible_settings += 1

    if incompatible_settings > 1:
        hdf5_common.handle_error("bit range, scaling factor, bit mask are incompatible settings")

    if globals.SAVE_INJECTION_SEQUENCE and \
            (globals.INJECTION_SEQUENCE_PATH != "" or globals.SCALING_FACTOR is not None or
             globals.BIT_MASK is not None):
        hdf5_common.handle_error("'saveInjectionSequence' is not compatible with "
                                 "'injection sequence path' or scaling factor or bit mask")
