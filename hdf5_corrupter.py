import json
import sys
import os
from os import path
import settings_reader
import globals
import corrupter
import hdf5_common
import logging
from datetime import datetime

os.environ["OMP_NUM_THREADS"] = "1"


def determine_locations_to_corrupt():
    globals.ALL_LOCATIONS = hdf5_common.get_hdf5_file_leaf_locations(globals.HDF5_FILE)

    if globals.LOAD_INJECTION_SEQUENCE:
        if path.exists(globals.INJECTION_SEQUENCE_PATH):
            json_content = open(globals.INJECTION_SEQUENCE_PATH, 'r').read()
            globals.INJECTION_SEQUENCE = json.loads(json_content)
            globals.BASE_LOCATIONS = globals.INJECTION_SEQUENCE.keys()
            globals.LOCATIONS_TO_CORRUPT = hdf5_common.get_full_location_paths(globals.BASE_LOCATIONS,
                                                                               globals.ALL_LOCATIONS)
        else:
            hdf5_common.handle_error("File does not exists: " + globals.INJECTION_SEQUENCE_PATH, globals.ARG_PARSER)
    else:
        if globals.USE_RANDOM_LOCATIONS:
            logging.info("Will inject errors at random locations")
            globals.LOCATIONS_TO_CORRUPT = globals.BASE_LOCATIONS = globals.ALL_LOCATIONS
        else:
            globals.BASE_LOCATIONS = globals.LOCATIONS_TO_CORRUPT
            globals.LOCATIONS_TO_CORRUPT = hdf5_common.get_full_location_paths(globals.LOCATIONS_TO_CORRUPT,
                                                                               globals.ALL_LOCATIONS)


def save_injection_sequence():
    if globals.SAVE_INJECTION_SEQUENCE:
        json_file_name = globals.INJECTION_SEQUENCE_PATH
        if not json_file_name.endswith('.json'):
            json_file_name = json_file_name + ".json"
        # serializing injection sequence to json
        injection_sequence_content = json.dumps(globals.INJECTION_SEQUENCE, indent=2)
        with open(json_file_name, "w") as injection_sequence_file:
            injection_sequence_file.write(injection_sequence_content)


def main():

    settings_reader.read_arguments(sys.argv[1:])

    config_file_name = os.path.basename(globals.CONFIG_FILE_PATH).rsplit('.', 1)[0]
    now = datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
    log_file_name = globals.LOG_FILE_PATH + config_file_name + "_" + now + "_corruption.log"
    logging.basicConfig(filename=log_file_name, filemode='w', format='%(levelname)s - %(message)s',
                        level=logging.DEBUG)

    settings_reader.init_corrupter()

    if globals.ONLY_PRINT:
        hdf5_common.print_hdf5_file(globals.HDF5_FILE)
    else:
        determine_locations_to_corrupt()

        if globals.LOAD_INJECTION_SEQUENCE:
            corrupter.corrupt_hdf5_file_based_on_sequence(globals.HDF5_FILE, globals.INJECTION_SEQUENCE,
                                                          globals.LOCATIONS_TO_CORRUPT)
        # normal injection
        else:
            # if first bit (sign-bit) not in range and ALLOW_SIGN_CHANGE is true, then increase by 1 the start of range
            # This makes it easier to generate random samples
            if globals.ALLOW_SIGN_CHANGE and globals.FIRST_BIT is not None and globals.FIRST_BIT > 0:
                globals.FIRST_BIT -= 1
                logging.info("Sign change is allowed")

            file_entries_count = hdf5_common.count_hdf5_file_entries(globals.HDF5_FILE)
            # calculates the number of injection attempts, based on the desired corruption percentage
            if globals.INJECTION_TYPE == globals.PERCENTAGE_STR:
                num_injection_tries = int(globals.INJECTION_TRIES * file_entries_count / 100)
            # Corruption type = "Count"
            else:
                num_injection_tries = globals.INJECTION_TRIES

            logging.info("Will inject at most: " + str(num_injection_tries) + " errors")

            errors_injected = corrupter.try_corrupt_hdf5_file(globals.HDF5_FILE, globals.LOCATIONS_TO_CORRUPT,
                                                              globals.INJECTION_PROBABILITY, num_injection_tries,
                                                              globals.BURST)

            logging.info("File corrupted: " + str(errors_injected * 100 / file_entries_count) +
                         " %, with a total of: " + str(errors_injected) + " errors injected")
            #save_injection_sequence(globals.LOG_FILE_PATH + "injectionSequence_" + now + ".json")
            save_injection_sequence()


if __name__ == "__main__":
    main()
