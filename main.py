import numpy as np
import h5py
import sys, getopt
import random
from os import path
import yaml

import struct
import binascii
import ctypes

import config_file_reader
import globals

def print_tool_ussage():
    print("hdf5Corrupter.py -h <help> -c <configFile>")


def corrupt_value(val: float):
    return val + 128


# give a dataset, returns a random index based on its shape
def get_random_indexes(dataset):
    indexes = [0] * dataset.ndim
    currentDim = 0
    for dimLength in dataset.shape:
        ranIndex = random.randint(0,dimLength-1)
        indexes[currentDim] = ranIndex
        currentDim += 1

    return indexes


def corrupt_dataset(dataset, prints_enabled: bool = True):
    r_pos = get_random_indexes(dataset)
    if prints_enabled:
        print("will try to corrupt at: " + str(r_pos))
    if dataset.ndim == 1:
        dataset[r_pos[0]] = corrupt_value(dataset[r_pos[0]])
    elif dataset.ndim == 2:
        dataset[r_pos[0],r_pos[1]] = corrupt_value(dataset[r_pos[0],r_pos[1]])
    elif dataset.ndim == 3:
        dataset[r_pos[0], r_pos[1], r_pos[2]] =\
            corrupt_value(dataset[r_pos[0], r_pos[1], r_pos[2]])
    # more than 3 is very unlikely
    elif dataset.ndim == 4:
        dataset[r_pos[0], r_pos[1], r_pos[2], r_pos[3]] =\
            corrupt_value(dataset[r_pos[0], r_pos[1], r_pos[2],  r_pos[3]])


def testCorruptNumpyArrays():
    arr = np.array([[[1, 2, 3], [4, 5, 6]], [[7, 8, 9], [10, 11, 12]]])
    print("narray before")
    print(arr)
    corrupt_dataset(arr)
    print("narray after")
    print(arr)

    arr = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9])
    print("narray before")
    print(arr)
    corrupt_dataset(arr)
    print("narray after")
    print(arr)

    arr = np.array([[1, 2, 3, 4, 5],
                    [6, 7, 8, 9, 10],
                    [11, 12, 13, 14, 15]])

    print("narray before")
    print(arr)
    corrupt_dataset(arr)
    print("narray after")
    print(arr)


def corrupt_hdf5_file(input_file: str, locations_to_corrupt: str, prints_enabled: bool = True):
    if path.exists(input_file):
        errors_injected = 0
        with h5py.File(input_file, 'a') as hdf:
            # ls = list(hdf.keys())

            for location in locations_to_corrupt:
                print("trying to corrupt at " + str(location))

                dataset = hdf.get(location)
                if(dataset is not None):
                    if prints_enabled:
                        numpy_array = np.array(dataset)
                        print("dataset before")
                        print(numpy_array)

                    corrupt_dataset(dataset)

                    if prints_enabled:
                        numpy_array = np.array(dataset)
                        print("dataset after")
                        print(numpy_array)
                else:
                    print("Error: Location " + str(location) + " does not exist in the file")
    else:
        print("File: " + input_file + " does not exist... exiting application")
        exit(2)

def set_bit(value, n):
    return value | (1 << n)


def float_to_bits(value: float):
    valueStr = ""
    for index in range(8):
        valueStr = str(value >> index & 1) + valueStr

    return valueStr


def testFlipFloats():
    print(float_to_bits(2))
    print(float_to_bits(3))
    print(float_to_bits(4))
    print(float_to_bits(5))
    print(float_to_bits(6))
    #print('0x' + str(binascii.hexlify(struct.pack('<d', 5.2))))
    f = ctypes.c_float(5.2)
    print(ctypes.c_int.from_address(ctypes.addressof(f)).value)
    exit(2)


def main():
    #testFlipFloats()
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
    corrupt_hdf5_file(globals.HDF5_FILE, globals.LOCATIONS_TO_CORRUPT)

if __name__ == "__main__":
    main()