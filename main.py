import h5py
import numpy as np
import sys, getopt
from os import path
import config_file_reader
import globals
import corrupter


def print_tool_ussage():
    print("hdf5Corrupter.py -h <help> -c <configFile>")


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


def main():
    #testFlipFloats()
    #corrupter.testCorruptNumpyArrays()

    argument_list = sys.argv[1:]
    short_options = "hc:"
    long_options = ["help", "configFile="]
    config_file = ''
    try:
        arguments, values = getopt.getopt(argument_list, short_options, long_options)
    except getopt.error as err:
        # Output error, and return with an error code
        print(str(err))
        sys.exit(2)

    # Evaluate given options
    for current_argument, current_value in arguments:
        if current_argument in ("-c", "--configFile"):
            config_file = current_value
        elif current_argument in ("-h", "--help"):
            print_tool_ussage()

    config_file_reader.read_config_file(config_file)
    if globals.PRINT_ONLY:
        print_hdf5_file(globals.HDF5_FILE)
    else:
        corrupter.corrupt_hdf5_file(globals.HDF5_FILE, globals.LOCATIONS_TO_CORRUPT)


if __name__ == "__main__":
    main()
