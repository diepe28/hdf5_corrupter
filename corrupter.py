import globals
import random
from os import path
import h5py
import numpy as np
import sys
from codecs import decode
import struct
from random import randint


def bin_to_float(b):
    bf = int_to_bytes(int(b, 2), 8)  # 8 bytes needed for IEEE 754 binary64.
    return struct.unpack('>d', bf)[0]


def int_to_bytes(n, length):  # Helper function
    return decode('%%0%dx' % (length << 1) % n, 'hex')[-length:]


def float_to_bin(value):  # For testing.
    [d] = struct.unpack(">Q", struct.pack(">d", value))
    return '{:064b}'.format(d)


def __change_bit(binary: str, index: int):
    # print("Flipping bit at position:" + str(index))
    bit = "1" if binary[index] == '0' else "0"
    binary = binary[:index] + bit + binary[index + 1:]
    return binary


# floats have 8 bytes so: byte and bit in [0-7], -1 means random
def change_bit(binary: str, byte: int, bit: int):
    if byte == -1:
        byte = randint(0, 7)
    if bit == -1:
        bit = randint(0, 7)

    index = byte * 8 + bit
    return __change_bit(binary, index)


# todo, what about when the value is an integer
def corrupt_value(val: float, corruption_prob: float):
    if random.random() < corruption_prob:
        binary = float_to_bin(val)
        new_binary = change_bit(binary, globals.BYTE, globals.BIT)
        new_val = bin_to_float(new_binary)
        return new_val, True
    return val, False


# given a dataset, returns a random index based on its shape
def __get_random_indexes(dataset):
    dimensions = 1 if dataset.ndim == 0 else dataset.ndim
    indexes = [0] * dimensions
    current_dim = 0
    for dimLength in dataset.shape:
        ranIndex = random.randint(0, dimLength-1)
        indexes[current_dim] = ranIndex
        current_dim += 1

    return indexes


def corrupt_dataset(dataset, corruption_prob: float, prints_enabled: bool = True):
    success = False
    r_pos = __get_random_indexes(dataset)
    if dataset.ndim == 0:
        dataset[()], success = corrupt_value(dataset[()], corruption_prob)
    elif dataset.ndim == 1:
        dataset[r_pos[0]], success = corrupt_value(dataset[r_pos[0]], corruption_prob)
    elif dataset.ndim == 2:
        dataset[r_pos[0], r_pos[1]], success = corrupt_value(dataset[r_pos[0], r_pos[1]], corruption_prob)
    elif dataset.ndim == 3:
        dataset[r_pos[0], r_pos[1], r_pos[2]], success = \
            corrupt_value(dataset[r_pos[0], r_pos[1], r_pos[2]], corruption_prob)
    # more than 3 is very unlikely
    elif dataset.ndim == 4:
        dataset[r_pos[0], r_pos[1], r_pos[2], r_pos[3]], success = \
            corrupt_value(dataset[r_pos[0], r_pos[1], r_pos[2],  r_pos[3]], corruption_prob)
    if success and prints_enabled:
        print("Corruption position: " + str(r_pos))
    return success


def corrupt_hdf5_file(input_file: str, locations_to_corrupt: str, corruption_prob: float,
                      num_injection_tries: int, prints_enabled: bool = True):
    if path.exists(input_file):
        errors_injected = 0
        with h5py.File(input_file, 'a') as hdf:
            locations_count = locations_to_corrupt.__len__()

            while num_injection_tries > 0:
                # randomly calculates the next location to corrupt
                next_location_index = random.randrange(1, locations_count)
                location = locations_to_corrupt[next_location_index]
                if prints_enabled:
                    print("Trying to corrupt at " + str(location))

                dataset = hdf.get(location)
                if dataset is not None:
                    # if prints_enabled:
                    # numpy_array = np.array(dataset)
                    # if prints_enabled:
                    #    print("dataset before")
                    #    print(numpy_array)

                    if corrupt_dataset(dataset, corruption_prob, prints_enabled):
                        errors_injected += 1

                    # if prints_enabled:
                    # numpy_array = np.array(dataset)
                    # if prints_enabled:
                    #    print("dataset after")
                    #    print(numpy_array)
                else:
                    print("Error: Location " + str(location) + " does not exist in the file")

                num_injection_tries -= 1
        return errors_injected
    else:
        print("File: " + input_file + " does not exist... exiting application")
        exit(2)


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
    sys.exit(2)