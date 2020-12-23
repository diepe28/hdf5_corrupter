import random
import h5py
import numpy as np
import sys, getopt
from os import path
import config_file_reader
import globals
import corrupter


def print_tool_ussage_and_exit():
    print("Correct usage of the tool: ")
    print("> hdf5_corrupter.py <arguments>, where the possible arguments are:")
    print("   -h | -help, optional argument, prints this message")
    print("   -c | -configFile \"path/to/config.yaml\", mandatory argument, the tool always needs a config.yaml")
    print("   -p | -printOnly, optional argument, prints the contents of the hdf5 file specified at config file")
    sys.exit(2)

# each item is a tuple: {name, group}
def print_hdf5_item(item: tuple, prefix: str):
    item_name = item[0]
    item_val = item[1]
    print(prefix + item_name + "," + str(type(item_val)))

    if getattr(item_val, "items", None) is not None:
        sub_items = list(item_val.items())
        for sub_item in sub_items:
            print_hdf5_item(sub_item, "\t" + prefix)
        print()
    else:
        #get dataset and print it
        numpy_array = np.array(item_val)
        print(numpy_array)


def print_hdf5_file(input_file: str):
    if path.exists(input_file):
        with h5py.File(input_file, 'r') as hdf:
            base_items = list(hdf.items())
            for item in base_items:
                print_hdf5_item(item, "")


# each item is a tuple: {name, group}
def count_hdf5_item_entries(item: tuple):
    item_val = item[1]
    count = 0

    if getattr(item_val, "items", None) is not None:
        sub_items = list(item_val.items())
        for sub_item in sub_items:
            count += count_hdf5_item_entries(sub_item)

        return count
    else:
        # check if it's dataset and count count its entries
        if getattr(item_val, "shape", None) is not None:
            return np.prod(item_val.shape)


def count_hdf5_file_entries(input_file: str):
    count = 0
    if path.exists(input_file):
        with h5py.File(input_file, 'r') as hdf:
            base_items = list(hdf.items())
            for item in base_items:
                count += count_hdf5_item_entries(item)

    return count

def main():
    #testFlipFloats()
    #corrupter.testCorruptNumpyArrays()

    argument_list = sys.argv[1:]
    short_options = "hc:p"
    long_options = ["help", "configFile=", "printOnly"]
    config_file = ''
    try:
        arguments, values = getopt.getopt(argument_list, short_options, long_options)
    except getopt.error as err:
        print_tool_ussage_and_exit()

    if argument_list.__len__() == 0 or argument_list.__len__() > long_options.__len__():
        print_tool_ussage_and_exit()

    # Evaluate given options
    for current_argument, current_value in arguments:
        if current_argument in ("-c", "--configFile"):
            config_file = current_value
        if current_argument in ("-p", "--printOnly"):
            globals.PRINT_ONLY = True
        elif current_argument in ("-h", "--help"):
            print_tool_ussage_and_exit()

    config_file_reader.read_config_file(config_file)

    if globals.PRINT_ONLY:
        print_hdf5_file(globals.HDF5_FILE)
    else:
        file_entries_count = count_hdf5_file_entries(globals.HDF5_FILE)
        # calculates the number of injection tries, based on the desired corruption percentage
        num_injection_tries = int(globals.MAX_CORRUPTION_PERCENTAGE * file_entries_count / 100)
        print("Will inject at most: " + str(num_injection_tries) + " errors")

        errors_injected = corrupter.corrupt_hdf5_file(globals.HDF5_FILE, globals.LOCATIONS_TO_CORRUPT,
                                    globals.PROB, num_injection_tries,  False)

        print("File corrupted: " + str(errors_injected * 100 / file_entries_count) +
              " %, with a total of: " + str(errors_injected) + " errors injected")

if __name__ == "__main__":
    main()
