import yaml
import globals
import logging


def log_options(corrupt_locations):
    logging.info("")
    logging.info("********** Options **********")
    logging.info(" " + globals.STR_HDF5_FILE + ": " + str(globals.HDF5_FILE))
    logging.info(" " + globals.STR_PROB + ": " + str(globals.PROB))
    logging.info(" " + globals.STR_MAX_CORRUPTION_PERCENTAGE + ": " + str(globals.MAX_CORRUPTION_PERCENTAGE))
    logging.info(" " + globals.STR_BYTE + ": " + str(globals.BYTE))
    logging.info(" " + globals.STR_BIT + ": " + str(globals.BIT))
    logging.info(" " + globals.STR_USE_RANDOM_LOCATIONS + ": " + str(globals.USE_RANDOM_LOCATIONS))
    logging.info(" " + globals.STR_LOCATIONS_TO_CORRUPT + ":")
    for location in corrupt_locations:
        logging.info("  " + str(location))
    logging.info("********** ------- **********")
    logging.info("")


def read_config_file(config_file_path: str):
    with open(config_file_path) as f:
        logging.info("Reading config file: " + config_file_path)
        data = yaml.load(f, Loader=yaml.FullLoader)
        globals.HDF5_FILE = data[globals.STR_HDF5_FILE]
        globals.PROB = float(data[globals.STR_PROB])
        globals.MAX_CORRUPTION_PERCENTAGE = float(data[globals.STR_MAX_CORRUPTION_PERCENTAGE])
        globals.BYTE = int(data[globals.STR_BYTE])
        globals.BIT = int(data[globals.STR_BIT])
        globals.USE_RANDOM_LOCATIONS = bool(data[globals.STR_USE_RANDOM_LOCATIONS])
        globals.LOCATIONS_TO_CORRUPT = data[globals.STR_LOCATIONS_TO_CORRUPT]
        log_options(globals.LOCATIONS_TO_CORRUPT)
