import json
import sys, getopt
import os
from os import path
import config_file_reader
import globals
import corrupter
import hdf5_common
import logging
from datetime import datetime

os.environ["OMP_NUM_THREADS"] = "1"


def print_tool_usage_and_exit():
    print("Correct usage of the tool: ")
    print("> hdf<5_corrupter.py <arguments>, where the possible arguments are:")
    print("  -h | --help, optional argument, prints this message")
    print("  -c | --configFile \"path/to/config.yaml\", mandatory argument, the tool always needs a config.yaml")
    print("  -f | --hdf5File \"path/to/file.h5\", path to the hdf5 file to corrupt."
          "\t\t\t*Overwrites value from config file*")
    print("  -l | --logFilePath \"path/to/logs/\", path where to save the log files."
          "\t\t*Overwrites value from config file*")
    print("  -d | --firstBit <value>, first bit to inject errors (0-63), leftmost is sign-bit, next 11 are exp bits "
          "and the rest is mantissa. it must be <= than last_bit..\t\t\t*Overwrites value from config file*")
    print("  -e | --lastBit <value>, last bit to inject errors (0-63), it must be >= than first_byte. If both values"
          " are the same, injection will only happen on that bit...\t\t\t*Overwrites value from config file*")
    print("  -p | --injectionProbability <value>, value of injection probability."
          "\t\t\t*Overwrites value from config file*")
    print("  -t | --injectionType <type>, where type can be either \"percentage\" or \"count\"."
          "\t*Overwrites value from config file*")
    print("  -k | --injectionTries <value>, value in [0-1] or int > 0, depending on injection_type, respectively."
          "\t*Overwrites value from config file*")
    print("  -a | --scalingFactor <value>, optional, if used it ignores the bit range and multiplies every value"
          "by this scaling factor")
    print("  -s | --saveInjectionSequence, optional, incompatible with -i, saves the injection sequence to a file")
    print("  -i | --injectionSequencePath \"path/to/sequence.json\", optional, incompatible with -s, uses the injection"
          "injection sequence from the file for the injection. If used, the following settings will be ignored: "
          "'use_random_locations','locations_to_corrupt','injectionProbability','injectionType','injectionTries'")
    print("  -o | --onlyPrint, optional, prints the contents of the hdf5 file specified and exits")
    logging.critical("Wrong use of the tool... exiting")
    sys.exit(2)


def read_arguments(argument_list):
    short_options = "hc:f:l:d:e:p:t:k:a:si:o"
    long_options = ["help", "configFile=", "hdf5File=", "logFilePath=", "firstBit=", "lastBit=",
                    "injectionProbability=", "injectionType=", "injectionTries=", "scalingFactor=",
                    "saveInjectionSequence", "injectionSequencePath=", "onlyPrint"]
    try:
        arguments, values = getopt.getopt(argument_list, short_options, long_options)
    except getopt.error as err:
        print_tool_usage_and_exit()

    if argument_list.__len__() == 0 or argument_list.__len__() > len(long_options) * 2:
        print_tool_usage_and_exit()

    # Validate argument
    for current_argument, current_value in arguments:
        if current_argument in ("-c", "--configFile"):
            globals.CONFIG_FILE_PATH = current_value
        if current_argument in ("-f", "--hdf5File"):
            globals.HDF5_FILE = current_value
        if current_argument in ("-l", "--logFilePath"):
            globals.LOG_FILE_PATH = current_value
        if current_argument in ("-d", "--firstBit"):
            globals.FIRST_BIT = int(current_value)
        if current_argument in ("-e", "--lastBit"):
            globals.LAST_BIT = int(current_value)
        if current_argument in ("-p", "--injectionProbability"):
            globals.INJECTION_PROBABILITY = float(current_value)
        if current_argument in ("-t", "--injectionType"):
            globals.INJECTION_TYPE = current_value
        if current_argument in ("-k", "--injectionTries"):
            globals.INJECTION_TRIES = float(current_value)
        if current_argument in ("-a", "--scalingFactor"):
            globals.SCALING_FACTOR = float(current_value)
        if current_argument in ("-s", "--saveInjectionSequence"):
            globals.SAVE_INJECTION_SEQUENCE = True
        if current_argument in ("-i", "--injectionSequencePath"):
            globals.INJECTION_SEQUENCE_PATH = current_value
        if current_argument in ("-o", "--onlyPrint"):
            globals.ONLY_PRINT = True
        elif current_argument in ("-h", "--help"):
            print_tool_usage_and_exit()

    if globals.SAVE_INJECTION_SEQUENCE and globals.INJECTION_SEQUENCE_PATH != "":
        print("-s (--saveInjectionSequence) and -i (--injectionSequencePath) are incompatible options")
        print_tool_usage_and_exit()


def determine_locations_to_corrupt():
    globals.ALL_LOCATIONS = hdf5_common.get_hdf5_file_leaf_locations(globals.HDF5_FILE)

    if globals.INJECTION_SEQUENCE_PATH != "":
        if path.exists(globals.INJECTION_SEQUENCE_PATH):
            json_content = open(globals.INJECTION_SEQUENCE_PATH, 'r').read()
            globals.INJECTION_SEQUENCE = json.loads(json_content)
            globals.BASE_LOCATIONS = globals.INJECTION_SEQUENCE.keys()
            globals.LOCATIONS_TO_CORRUPT = hdf5_common.get_full_location_paths(globals.BASE_LOCATIONS,
                                                                               globals.ALL_LOCATIONS)
        else:
            hdf5_common.handle_error("File does not exists: " + globals.INJECTION_SEQUENCE_PATH)
    else:
        if globals.USE_RANDOM_LOCATIONS:
            logging.info("Will inject errors at random locations")
            globals.LOCATIONS_TO_CORRUPT = globals.BASE_LOCATIONS = globals.ALL_LOCATIONS
        else:
            globals.BASE_LOCATIONS = globals.LOCATIONS_TO_CORRUPT
            globals.LOCATIONS_TO_CORRUPT = hdf5_common.get_full_location_paths(globals.LOCATIONS_TO_CORRUPT,
                                                                               globals.ALL_LOCATIONS)


def save_injection_sequence(json_file_name: str):
    if globals.SAVE_INJECTION_SEQUENCE:
        # serializing injection sequence to json
        injection_sequence_content = json.dumps(globals.INJECTION_SEQUENCE, indent=2)
        with open(json_file_name, "w") as injection_sequence_file:
            injection_sequence_file.write(injection_sequence_content)


# params: -c "config-chainer.yaml" -t "percentage" -k 0.005 -o
def main():
    read_arguments(sys.argv[1:])
    config_file_reader.read_config_file(globals.CONFIG_FILE_PATH)

    config_file_name = os.path.basename(globals.CONFIG_FILE_PATH).rsplit('.', 1)[0]
    now = datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
    log_file_name = globals.LOG_FILE_PATH + config_file_name + "_" + now + "_corruption.log"
    logging.basicConfig(filename=log_file_name, filemode='w', format='%(levelname)s - %(message)s',
                        level=logging.DEBUG)

    config_file_reader.check_for_error_in_values()
    config_file_reader.log_options()

    if globals.ONLY_PRINT:
        hdf5_common.print_hdf5_file(globals.HDF5_FILE)
    else:
        determine_locations_to_corrupt()

        if globals.INJECTION_SEQUENCE_PATH != "":
            corrupter.corrupt_hdf5_file_based_on_sequence(globals.HDF5_FILE, globals.INJECTION_SEQUENCE,
                                                          globals.LOCATIONS_TO_CORRUPT)

        # normal injection
        else:
            # if first bit (sign-bit) not in range and ALLOW_SIGN_CHANGE is true, then increase by 1 the start of range
            if globals.ALLOW_SIGN_CHANGE and globals.FIRST_BIT > 0:
                globals.FIRST_BIT -= 1

            file_entries_count = hdf5_common.count_hdf5_file_entries(globals.HDF5_FILE)
            # calculates the number of injection attempts, based on the desired corruption percentage
            if globals.INJECTION_TYPE == globals.PERCENTAGE_STR:
                num_injection_tries = int(globals.INJECTION_TRIES * file_entries_count / 100)
            # Corruption type = "Count"
            else:
                num_injection_tries = globals.INJECTION_TRIES

            logging.info("Will inject at most: " + str(num_injection_tries) + " errors")
            logging.info("Will inject errors in bytes: [" + str(globals.FIRST_BIT) + "-" + str(globals.LAST_BIT) + "]")

            errors_injected = corrupter.corrupt_hdf5_file(globals.HDF5_FILE, globals.LOCATIONS_TO_CORRUPT,
                                                          globals.INJECTION_PROBABILITY, num_injection_tries)

            logging.info("File corrupted: " + str(errors_injected * 100 / file_entries_count) +
                         " %, with a total of: " + str(errors_injected) + " errors injected")
            save_injection_sequence(globals.LOG_FILE_PATH + "injectionSequence_" + now + ".json")


if __name__ == "__main__":
    main()
