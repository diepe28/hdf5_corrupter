import yaml
import globals
import logging
import argparse
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
    if globals.FLOAT_PRECISION == "auto":
        logging.info(" Bit range is calculated based on value precision")
    else:
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
        logging.info(" Will save the injection sequence to: " + globals.INJECTION_SEQUENCE_PATH)
    if globals.LOAD_INJECTION_SEQUENCE:
        logging.info(" [WARNING] Ignoring corruption settings. Using injection sequence from file: " +
                     str(globals.INJECTION_SEQUENCE_PATH))
    logging.info(" " + globals.USE_RANDOM_LOCATIONS_STR + ": " + str(globals.USE_RANDOM_LOCATIONS))
    logging.info(" " + globals.LOCATIONS_TO_CORRUPT_STR + ":")
    for location in globals.LOCATIONS_TO_CORRUPT:
        logging.info("  " + str(location))
    logging.info("********** ------- **********")
    logging.info("")


def set_arguments_parser(parser: object):
    parser.add_argument("--configFile", type=str,
                        help="\"path/to/config.yaml\", incompatible with other argument settings. If given,"
                             " all settings will be read from the YAML file")

    parser.add_argument("--hdf5File", type=str,
                        help="\"path/to/file.h5\", path to the hdf5 file to corrupt.")

    parser.add_argument("--locationsToCorrupt", nargs="+",
                        help="The internal location of the hdf5 file to corrupt")

    parser.add_argument("--logFilePath", type=str,
                        help="\"path/to/logs/\", path where to save the log files.")

    parser.add_argument("--floatPrecision", type=str,
                        help="<value>, auto, 64, 32 or 16, the number of bits to use for each float value")

    parser.add_argument("--firstBit", type=int,
                        help="first bit to inject errors [0-floatPrecision-1], leftmost is sign-bit, next are "
                             "exp bits and the rest is mantissa. it must be <= than last_bit.")

    parser.add_argument("--lastBit", type=int,
                        help="last bit to inject errors [0-floatPrecision-1], must be >= than first_byte. If "
                             "both values are equal, injection will only happen on that bit")

    parser.add_argument("--injectionProbability", type=float,
                        help="value of injection probability")

    parser.add_argument("--injectionType", type=str,
                        help="can be either \"percentage\" or \"count\".")

    parser.add_argument("--injectionTries", type=int,
                        help="value in [0-1] or int > 0, depending on injection_type, respectively.")

    parser.add_argument("--scalingFactor", type=int,
                        help="incompatible with bit range or bit mask. Multiplies every value by this scaling factor")

    parser.add_argument("--bitMask", type=str,
                        help="incompatible with scaling_factor or burst. Uses a bit mask to corrupt the values. Eg,"
                             "\"101101\". The first bit to apply the mask in each value is randomly selected from "
                             "[0 to 63-bitMaskLength]")

    parser.add_argument("--burst", type=int,
                        help="default: 1, incompatible with scaling factor or bit mask. "
                             "It is the number of injection attempts per value")

    parser.add_argument("--saveInjectionSequence", nargs=2, action="store",
                        help="\"path/to/sequence.json\" saveIndexes?,"
                             "Incompatible with --loadInjectionSequence, "
                             "saves the injection sequence to the given file with/without indexes")

    parser.add_argument("--loadInjectionSequence", type=str,
                        help="\"path/to/sequence.json\", Incompatible with --saveInjectionSequence, uses the injection"
                             "sequence from the file. The following settings will be ignored: 'use_random_locations',"
                             "'locations_to_corrupt','injectionProbability','injectionType','injectionTries'")

    parser.add_argument("--allowSignChange", action="store_true",
                        help="Even if the sign-bit (0) is not included in the bit range, it enables bit flips on it.")

    parser.add_argument("--useRandomLocations", action="store_true",
                        help="Chooses random locations on the file to inject errors, if true it will ignore the "
                             "list of locations to corrupt")

    parser.add_argument("--allowNaNValues", action="store_true",
                        help="When flipping a bit of a float, the corruption mechanism allows the resulting binary to "
                             "represent a NaN or +-Inf.")

    parser.add_argument("--onlyPrint", action="store_true",
                        help="prints the contents of the hdf5 file specified and exits")


def read_arguments(arguments):
    globals.ARG_PARSER = argparse.ArgumentParser()
    set_arguments_parser(globals.ARG_PARSER)
    args = globals.ARG_PARSER.parse_args(arguments)

    # the only param compatible either with config file or arguments
    if args.onlyPrint is not None:
        globals.ONLY_PRINT = args.onlyPrint

    if args.configFile is not None:
        globals.CONFIG_FILE_PATH = args.configFile
        read_config_file(globals.CONFIG_FILE_PATH)
    else:
        if args.hdf5File is not None:
            globals.HDF5_FILE = args.hdf5File

        if args.logFilePath is not None:
            globals.LOG_FILE_PATH = args.logFilePath

        if args.floatPrecision is not None:
            globals.FLOAT_PRECISION = args.floatPrecision

        if args.firstBit is not None:
            globals.FIRST_BIT = args.firstBit

        if args.lastBit is not None:
            globals.LAST_BIT = args.lastBit

        if args.injectionProbability is not None:
            globals.INJECTION_PROBABILITY = args.injectionProbability

        if args.injectionType is not None:
            globals.INJECTION_TYPE = args.injectionType

        if args.injectionTries is not None:
            globals.INJECTION_TRIES = args.injectionTries

        if args.scalingFactor is not None:
            globals.SCALING_FACTOR = args.scalingFactor

        if args.burst is not None:
            globals.BURST = args.burst

        if args.bitMask is not None:
            globals.BIT_MASK = args.bitMask

        if args.saveInjectionSequence is not None:
            globals.SAVE_INJECTION_SEQUENCE = True
            globals.INJECTION_SEQUENCE_PATH = args.saveInjectionSequence[0]
            globals.INJECTION_SEQUENCE_SAVE_INDEXES = args.saveInjectionSequence[1].lower() == "true"

        if args.loadInjectionSequence is not None:
            globals.LOAD_INJECTION_SEQUENCE = True
            globals.INJECTION_SEQUENCE_PATH = args.loadInjectionSequence

        if args.allowSignChange is not None:
            globals.ALLOW_SIGN_CHANGE = args.allowSignChange

        if args.allowNaNValues is not None:
            globals.ALLOW_NaN_VALUES = args.allowNaNValues

        if args.useRandomLocations is not None:
            globals.USE_RANDOM_LOCATIONS = args.useRandomLocations

        if args.locationsToCorrupt is not None:
            globals.LOCATIONS_TO_CORRUPT = args.locationsToCorrupt


def read_config_file(config_file_path: str):
    with open(config_file_path) as f:
        data = yaml.load(f, Loader=yaml.Loader)

        # read values from config file
        globals.HDF5_FILE = data[globals.HDF5_FILE_STR]
        globals.LOG_FILE_PATH = data[globals.LOG_FILE_PATH_STR]
        globals.INJECTION_PROBABILITY = float(data[globals.INJECTION_PROBABILITY_STR])
        globals.INJECTION_TYPE = data[globals.INJECTION_TYPE_STR]
        globals.INJECTION_TRIES = float(data[globals.INJECTION_TRIES_STR])
        globals.ALLOW_SIGN_CHANGE = bool(data[globals.ALLOW_SIGN_CHANGE_STR])
        globals.ALLOW_NaN_VALUES = bool(data[globals.ALLOW_NaN_VALUES_STR])
        globals.USE_RANDOM_LOCATIONS = bool(data[globals.USE_RANDOM_LOCATIONS_STR])
        globals.LOCATIONS_TO_CORRUPT = data[globals.LOCATIONS_TO_CORRUPT_STR]
        globals.SAVE_INJECTION_SEQUENCE = bool(data[globals.SAVE_INJECTION_SEQUENCE_STR])

        # values that might be in the config file
        if globals.INJECTION_SEQUENCE_PATH_STR in data:
            globals.INJECTION_SEQUENCE_PATH = data[globals.INJECTION_SEQUENCE_PATH_STR]

        if globals.FLOAT_PRECISION_STR in data:
            globals.FLOAT_PRECISION = data[globals.FLOAT_PRECISION_STR]

        if globals.SCALING_FACTOR_STR in data:
            globals.SCALING_FACTOR = float(data[globals.SCALING_FACTOR_STR])

        if globals.BIT_MASK_STR in data:
            globals.BIT_MASK = data[globals.BIT_MASK_STR]

        if globals.FIRST_BIT_STR in data:
            globals.FIRST_BIT = int(data[globals.FIRST_BIT_STR])

        if globals.LAST_BIT_STR in data:
            globals.LAST_BIT = int(data[globals.LAST_BIT_STR])

        if globals.BURST_STR in data:
            globals.BURST = int(data[globals.BURST_STR])


def are_settings_incompatible():
    incompatible_settings = 0

    if globals.FLOAT_PRECISION == "auto":
        incompatible_settings += 1
    if globals.BURST > 1 or globals.FIRST_BIT is not None or globals.LAST_BIT is not None:
        incompatible_settings += 1
    if globals.SCALING_FACTOR is not None:
        incompatible_settings += 1
    if globals.BIT_MASK is not None:
        if len(globals.BIT_MASK) > int(globals.FLOAT_PRECISION):
            hdf5_common.handle_error("Length of bit mask must be <= float_precision", globals.ARG_PARSER)
        incompatible_settings += 1

    # if bit-range, scaling factor and bit mask are not provided, by default will use a bit-range
    if incompatible_settings == 0:
        globals.FIRST_BIT = 0
        globals.LAST_BIT = int(globals.FLOAT_PRECISION) - 1

    return incompatible_settings > 1


def get_error_in_settings():
    error_msg = None

    if globals.INJECTION_TYPE == globals.COUNT_STR:
        # truncate to integer value
        globals.INJECTION_TRIES = int(globals.INJECTION_TRIES)

    if globals.HDF5_FILE is None:
        error_msg = "HDF5 file must be provided"

    elif globals.FLOAT_PRECISION is None or \
            (globals.FLOAT_PRECISION != "16" and globals.FLOAT_PRECISION != "32" and
             globals.FLOAT_PRECISION != "64" and globals.FLOAT_PRECISION != "auto"):
        error_msg = "Float precision must be submitted and must be 16, 32, 64 or auto"

    elif globals.FLOAT_PRECISION == "auto" and\
            (globals.FIRST_BIT is not None and globals.LAST_BIT is not None) or \
            globals.SCALING_FACTOR is not None or \
            globals.BIT_MASK is not None:
        error_msg = "Float Precision is set to 'auto'. Therefore a bit range, " \
                    "scaling factor or bit masks are not allowed"

    elif globals.FIRST_BIT is not None and globals.LAST_BIT is not None and\
            (globals.FIRST_BIT > globals.LAST_BIT or
             globals.FIRST_BIT < 0 or
             globals.FIRST_BIT > int(globals.FLOAT_PRECISION) - 1 or
             globals.LAST_BIT < 0 or
             globals.LAST_BIT > int(globals.FLOAT_PRECISION) - 1):
        error_msg = "Float Precision is set to: " + str(globals.FLOAT_PRECISION) + " so "\
                     "first_bit and last_bit must be an interval between "\
                     "[0-" + str(int(globals.FLOAT_PRECISION) - 1) + "]"

    elif globals.INJECTION_TYPE not in globals.INJECTION_TYPE_VALUES:
        error_msg = "Injection type not given or not recognized. "\
                    "It must be either \"percentage\" or \"count\""

    elif globals.INJECTION_TYPE == globals.PERCENTAGE_STR and \
            (globals.INJECTION_TRIES < 0 or globals.INJECTION_TRIES > 1):
        error_msg = "Injection tries for corruption type \"percentage\" must be a value between [0-1]"

    elif globals.INJECTION_TRIES < 1:
        error_msg = "Injection tries for corruption type \"count\" must be given and it must be a positive integer"

    elif globals.BURST is not None and globals.BURST < 1:
        error_msg = "Injection burst must be a positive integer"

    elif are_settings_incompatible():
        error_msg = "bit range (also burst), scaling factor, bit mask are incompatible settings"

    elif globals.SAVE_INJECTION_SEQUENCE and globals.LOAD_INJECTION_SEQUENCE:
        error_msg = "'saveInjectionSequence' is not compatible with loadInjectionSequence"

    elif globals.SAVE_INJECTION_SEQUENCE and \
            (globals.SCALING_FACTOR is not None or globals.BIT_MASK is not None):
        error_msg = "'saveInjectionSequence' is not compatible with scaling factor or bit mask"

    elif not globals.LOCATIONS_TO_CORRUPT and not globals.USE_RANDOM_LOCATIONS:
        error_msg = "Locations to corrupt must be provided when not using random locations"

    return error_msg


def init_corrupter():
    error_msg = get_error_in_settings()
    if error_msg is not None:
        hdf5_common.handle_error(error_msg, globals.ARG_PARSER)

    log_options()

    if globals.FLOAT_PRECISION is None or globals.FLOAT_PRECISION == "auto":
        # at the start, precision settings are set for 32-bit floats
        globals.set_precision_settings(32)
    else:
        globals.set_precision_settings(int(globals.FLOAT_PRECISION))
