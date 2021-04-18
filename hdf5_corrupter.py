import h5py
import numpy as np
import sys, getopt
import os
import config_file_reader
import globals
import corrupter
import hdf5_common
import logging
from datetime import datetime

os.environ["OMP_NUM_THREADS"] = "1"

def print_tool_ussage_and_exit():
    print("Correct usage of the tool: ")
    print("> hdf<5_corrupter.py <arguments>, where the possible arguments are:")
    print("   -h | --help, optional argument, prints this message")
    print("   -c | --configFile \"path/to/config.yaml\", mandatory argument, the tool always needs a config.yaml")
    print("   -f | --hdf5File \"path/to/file.h5\", path to the hdf5 file to corrupt."
          "\t\t\t*Overwrites value from config file*")
    print("   -l | --logFilePath \"path/to/logs/\", path where to save the log files."
          "\t\t*Overwrites value from config file*")
    print("   -p | --injectionProbability <value>, value of injection probability."
          "\t\t\t*Overwrites value from config file*")
    print("   -t | --injectionType <type>, where type can be either \"percentage\" or \"count\"."
          "\t*Overwrites value from config file*")
    print("   -k | --injectionTries <value>, value in [0-1] or int > 0, depending on injection_type, respectively."
          "\t*Overwrites value from config file*")

    print("   -o | --onlyPrint, optional argument, prints the contents of the hdf5 file specified and exits")
    logging.critical("Wrong use of the tool... exiting")
    sys.exit(2)

# params: -c "config-chainer.yaml" -t "percentage" -k 0.005 -o
def main():
    argument_list = sys.argv[1:]
    short_options = "hc:f:l:t:k:p:o"
    long_options = ["help", "configFile=", "hdf5File=", "logFilePath=", "injectionType=", "injectionTries=",
                    "injectionProbability=",  "onlyPrint"]
    config_file_path = ''
    try:
        arguments, values = getopt.getopt(argument_list, short_options, long_options)
    except getopt.error as err:
        print_tool_ussage_and_exit()

    max_arg_count = 8 # all 5 arguments and the 3 values
    if argument_list.__len__() == 0 or argument_list.__len__() > len(long_options) * 2:
        print_tool_ussage_and_exit()

    # Validate argument
    for current_argument, current_value in arguments:
        if current_argument in ("-c", "--configFile"):
            config_file_path = current_value
        if current_argument in ("-f", "--hdf5File"):
            globals.HDF5_FILE = current_value
        if current_argument in ("-l", "--logFilePath"):
            globals.LOG_FILE_PATH = current_value
        if current_argument in ("-o", "--onlyPrint"):
            globals.ONLY_PRINT = True
        if current_argument in ("-p", "--injectionProbability"):
            globals.INJECTION_PROBABILITY = float(current_value)
        if current_argument in ("-t", "--injectionType"):
            globals.INJECTION_TYPE = current_value
        if current_argument in ("-k", "--injectionTries"):
            globals.INJECTION_TRIES = float(current_value)
        elif current_argument in ("-h", "--help"):
            print_tool_ussage_and_exit()

    config_file_reader.read_config_file(config_file_path)

    # path = os.path.dirname(config_file_path)
    # if path == "":
    #    path = "."
    config_file_name = os.path.basename(config_file_path).rsplit('.', 1)[0]
    now = datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
    log_file_name = globals.LOG_FILE_PATH + config_file_name + "_" + now + "_corruption.log"
    logging.basicConfig(filename=log_file_name, filemode='w', format='%(levelname)s - %(message)s',
                        level=logging.DEBUG)

    config_file_reader.check_for_error_in_values()
    config_file_reader.log_options()

    # if first bit (sign-bit) not in range and ALLOW_SIGN_CHANGE is true, then increase by 1 the start of range
    if globals.ALLOW_SIGN_CHANGE and globals.FIRST_BIT > 0:
        globals.FIRST_BIT -= 1

    if globals.ONLY_PRINT:
        hdf5_common.print_hdf5_file(globals.HDF5_FILE)
    else:
        if globals.USE_RANDOM_LOCATIONS:
            logging.info("Will inject errors at random locations")
            globals.LOCATIONS_TO_CORRUPT = hdf5_common.get_hdf5_file_leaf_locations(globals.HDF5_FILE)

        file_entries_count = hdf5_common.count_hdf5_file_entries(globals.HDF5_FILE)
        # calculates the number of injection tries, based on the desired corruption percentage
        if globals.INJECTION_TYPE == globals.STR_PERCENTAGE:
            num_injection_tries = int(globals.INJECTION_TRIES * file_entries_count / 100)
        # Corruption type = "Count"
        else:
            num_injection_tries = globals.INJECTION_TRIES

        logging.info("Will inject at most: " + str(num_injection_tries) + " errors")
        logging.info("Will inject errors in bytes: [" + str(globals.FIRST_BIT) + "-" + str(globals.LAST_BIT) + "]")

        errors_injected = corrupter.corrupt_hdf5_file(globals.HDF5_FILE, globals.LOCATIONS_TO_CORRUPT,
                                                      globals.INJECTION_PROBABILITY, num_injection_tries, False)

        logging.info("File corrupted: " + str(errors_injected * 100 / file_entries_count) +
                     " %, with a total of: " + str(errors_injected) + " errors injected")


if __name__ == "__main__":
    main()
