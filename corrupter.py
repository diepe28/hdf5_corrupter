import globals
import random
import h5py
import numpy as np
import sys
import struct
import logging
import math
from os import path
from codecs import decode
from random import randint
from datetime import datetime


def bin_to_float(b):
    bf = int_to_bytes(int(b, 2), 8)  # 8 bytes needed for IEEE 754 binary64.
    return struct.unpack('>d', bf)[0]


def int_to_bytes(n, length):  # Helper function
    return decode('%%0%dx' % (length << 1) % n, 'hex')[-length:]


def float_to_bin(value):  # For testing.
    [d] = struct.unpack(">Q", struct.pack(">d", value))
    return '{:064b}'.format(d)


def change_bit_in_binary(binary: str, index: int):
    bit_flipped = "1" if binary[index] == '0' else "0"
    binary = binary[:index] + bit_flipped + binary[index + 1:]
    return binary


def corrupt_value(val, corruption_prob: float):
    random.seed(datetime.now())
    if random.random() < corruption_prob:
        str_val_type = str(type(val))
        chosen_bit = randint(globals.FIRST_BIT, globals.LAST_BIT)

        # if chosen bit is new first_bit (first_bit should have been decreased by 1 when reading args)
        # then chosen bit should actually be the sign-bit (0)
        if globals.ALLOW_SIGN_CHANGE and chosen_bit == globals.FIRST_BIT:
            chosen_bit = 0

        if "int" in str_val_type:
            binary = str(bin(val))[2:]
            chosen_bit = randint(0, len(binary)-1)
            new_binary = change_bit_in_binary(binary, chosen_bit)
            new_val = int(new_binary, 2)
            logging.debug("Int location value was corrupted at bit: " + str(chosen_bit) +
                          "  Delta> " + str(val) + " --> " + str(new_val))
            return new_val, True
        else:
            binary = float_to_bin(val)
            new_binary = change_bit_in_binary(binary, chosen_bit)
            new_val = bin_to_float(new_binary)
            if not globals.ALLOW_NaN_VALUES and (math.isnan(new_val) or math.isinf(new_val)):
                logging.debug("Could not corrupt value at the index because it was a NaN or Inf... trying again")
                return corrupt_value(val, corruption_prob)

            logging.debug("Float location value was corrupted at bit: " + str(chosen_bit) +
                          "  Delta> " + str(val) + " --> " + str(new_val))
            return new_val, True
    logging.debug("Did not corrupt value at the index")
    return val, False


# given a dataset, returns a random index based on its shape
def __get_random_indexes(dataset):
    random.seed(datetime.now())
    dimensions = 1 if dataset.ndim == 0 else dataset.ndim
    indexes = [0] * dimensions
    current_dim = 0
    for dimLength in dataset.shape:
        ranIndex = random.randint(0, dimLength-1)
        indexes[current_dim] = ranIndex
        current_dim += 1

    return indexes


def corrupt_dataset(dataset, corruption_prob: float):
    success = False
    r_pos = __get_random_indexes(dataset)
    logging.debug("Indexes to corrupt: " + str(r_pos))
    if dataset.ndim == 0:
        dataset[()], success = corrupt_value(dataset[()], corruption_prob)
    elif dataset.ndim == 1:
        dataset[r_pos[0]], success = corrupt_value(dataset[r_pos[0]], corruption_prob)
    elif dataset.ndim == 2:
        dataset[r_pos[0], r_pos[1]], success = corrupt_value(dataset[r_pos[0], r_pos[1]], corruption_prob)
    elif dataset.ndim == 3:
        dataset[r_pos[0], r_pos[1], r_pos[2]], success = \
            corrupt_value(dataset[r_pos[0], r_pos[1], r_pos[2]], corruption_prob)
    elif dataset.ndim == 4:
        dataset[r_pos[0], r_pos[1], r_pos[2], r_pos[3]], success = \
            corrupt_value(dataset[r_pos[0], r_pos[1], r_pos[2],  r_pos[3]], corruption_prob)
    # more than 4 is very unlikely... right?

    return success


def corrupt_hdf5_file(input_file: str, locations_to_corrupt, corruption_prob: float,
                      num_injection_tries: int, prints_enabled: bool = True):
    if path.exists(input_file):
        errors_injected = 0
        logging.info("----------- Corrupting file, main loop -----------")
        with h5py.File(input_file, 'a') as hdf:
            locations_count = locations_to_corrupt.__len__()

            while num_injection_tries > 0:
                # randomly calculates the next location to corrupt
                next_location_index = random.randrange(0, locations_count-1) if locations_count > 1 else 0
                location = locations_to_corrupt[next_location_index]
                logging.debug("Will try to corrupt at: " + str(location))

                dataset = hdf.get(location)
                if dataset is not None:
                    # if prints_enabled:
                    #   numpy_array = np.array(dataset)
                    #   print("dataset before")
                    #   print(numpy_array)

                    if corrupt_dataset(dataset, corruption_prob):
                        errors_injected += 1

                    # if prints_enabled:
                    #   numpy_array = np.array(dataset)
                    #   print("dataset after")
                    #   print(numpy_array)
                else:
                    logging.error(str(location) + " doesn't exist or it is not supported for error injection")

                num_injection_tries -= 1
        return errors_injected
    else:
        logging.error("Specified file does not exist... exiting the tool")
        sys.exit(2)