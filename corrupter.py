import globals
import random
import h5py
import sys
import struct
import logging
import math
from os import path
from codecs import decode
from random import randint
from datetime import datetime
import hdf5_common


def log_delta(val_type: str, before_val, after_val, changed_bit, scaling_factor = None):
    corruption_type = "by a scale factor: " + str(scaling_factor) if scaling_factor is not None else\
        "at bit: " + str(changed_bit)

    logging.debug(val_type + " location value was corrupted " + corruption_type +
                  "  Delta> " + str(before_val) + " --> " + str(after_val))


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


def corrupt_int(val: int):
    binary = str(bin(val))[2:]
    chosen_bit = randint(0, len(binary) - 1)
    new_binary = change_bit_in_binary(binary, chosen_bit)
    new_val = int(new_binary, 2)
    log_delta("Int", val, new_val, chosen_bit)
    return new_val, chosen_bit


def corrupt_float(val: float, chosen_bit: int):
    binary = float_to_bin(val)
    new_binary = change_bit_in_binary(binary, chosen_bit)
    new_val = bin_to_float(new_binary)
    if not globals.ALLOW_NaN_VALUES and (math.isnan(new_val) or math.isinf(new_val)):
        logging.debug("Could not corrupt value at the index because it was a NaN or Inf... trying again")
        return try_corrupt_value(val, 1)

    log_delta("Float", val, new_val, chosen_bit)
    return new_val, chosen_bit


# given a corruption probability, it tries to corrupt the value
def try_corrupt_value(val, corruption_prob: float):
    random.seed(datetime.now())
    if random.random() < corruption_prob:
        str_val_type = str(type(val))
        if globals.SCALING_FACTOR is None:
            if "int" in str_val_type:
                new_val, chosen_bit = corrupt_int(val)
            else:
                chosen_bit = randint(globals.FIRST_BIT, globals.LAST_BIT)
                # if chosen bit is new first_bit (first_bit should have been decreased by 1 when reading args)
                # then chosen bit should actually be the sign-bit (0)
                if globals.ALLOW_SIGN_CHANGE and chosen_bit == globals.FIRST_BIT:
                    chosen_bit = 0

                new_val, chosen_bit = corrupt_float(val, chosen_bit)
        else:
            new_val = val * globals.SCALING_FACTOR
            chosen_bit = -2  # -2, so it counts the injection
            log_delta("", val, new_val, -1, globals.SCALING_FACTOR)

        return new_val, chosen_bit

    logging.debug("Did not corrupt value at the index")
    return val, -1


# given the bit to flip, it corrupts the value changing that bit
def corrupt_value_at_bit(val, chosen_bit: int):
    str_val_type = str(type(val))
    if "int" in str_val_type:
        new_val, chosen_bit = corrupt_int(val)
    else:
        new_val, chosen_bit = corrupt_float(val, chosen_bit)

    return new_val, chosen_bit


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


# Tries to corrupt the given dataset with the given probability
def try_corrupt_dataset(dataset, corruption_prob: float):
    corrupted_bit = -1
    r_pos = __get_random_indexes(dataset)
    logging.debug("Indexes to corrupt: " + str(r_pos))
    if dataset.ndim == 0:
        dataset[()], corrupted_bit = try_corrupt_value(dataset[()], corruption_prob)
    elif dataset.ndim == 1:
        dataset[r_pos[0]], corrupted_bit = try_corrupt_value(dataset[r_pos[0]], corruption_prob)
    elif dataset.ndim == 2:
        dataset[r_pos[0], r_pos[1]], corrupted_bit = \
            try_corrupt_value(dataset[r_pos[0], r_pos[1]], corruption_prob)
    elif dataset.ndim == 3:
        dataset[r_pos[0], r_pos[1], r_pos[2]], corrupted_bit = \
            try_corrupt_value(dataset[r_pos[0], r_pos[1], r_pos[2]], corruption_prob)
    elif dataset.ndim == 4:
        dataset[r_pos[0], r_pos[1], r_pos[2], r_pos[3]], corrupted_bit = \
            try_corrupt_value(dataset[r_pos[0], r_pos[1], r_pos[2], r_pos[3]], corruption_prob)
    # more than 4 is very unlikely... right?

    return corrupted_bit


# Corrupts a random value in a dataset at the chosen bit
def corrupt_dataset_using_bit(dataset, chosen_bit: int):
    r_pos = __get_random_indexes(dataset)
    logging.debug("Indexes to corrupt: " + str(r_pos))
    if dataset.ndim == 0:
        dataset[()], corrupted_bit = corrupt_value_at_bit(dataset[()], chosen_bit)
    elif dataset.ndim == 1:
        dataset[r_pos[0]], corrupted_bit = corrupt_value_at_bit(dataset[r_pos[0]], chosen_bit)
    elif dataset.ndim == 2:
        dataset[r_pos[0], r_pos[1]], corrupted_bit = \
            corrupt_value_at_bit(dataset[r_pos[0], r_pos[1]], chosen_bit)
    elif dataset.ndim == 3:
        dataset[r_pos[0], r_pos[1], r_pos[2]], corrupted_bit = \
            corrupt_value_at_bit(dataset[r_pos[0], r_pos[1], r_pos[2]], chosen_bit)
    elif dataset.ndim == 4:
        dataset[r_pos[0], r_pos[1], r_pos[2], r_pos[3]], corrupted_bit = \
            corrupt_value_at_bit(dataset[r_pos[0], r_pos[1], r_pos[2], r_pos[3]], chosen_bit)
    # more than 4 is very unlikely... right?


# Tries to corrupt the input file at the given locations, with the given probability, num_injection_attempts times
def try_corrupt_hdf5_file(input_file: str, locations_to_corrupt, corruption_prob: float,
                          num_injection_attempts: int):
    if path.exists(input_file):
        errors_injected = 0
        logging.info("----------- Corrupting file, main loop -----------")
        with h5py.File(input_file, 'a') as hdf:
            locations_count = locations_to_corrupt.__len__()

            while num_injection_attempts > 0:
                random.seed(datetime.now())
                # randomly calculates the next location to corrupt
                next_location_index = random.randint(0, locations_count-1) if locations_count > 1 else 0
                location = locations_to_corrupt[next_location_index]
                logging.debug("Will try to corrupt at: " + str(location))

                dataset = hdf.get(location)
                if dataset is not None:
                    corrupted_bit = try_corrupt_dataset(dataset, corruption_prob)
                    if corrupted_bit != -1:
                        errors_injected += 1
                    if globals.SAVE_INJECTION_SEQUENCE:
                        base_location = hdf5_common.get_base_locations_for(location, globals.BASE_LOCATIONS)
                        if base_location in globals.INJECTION_SEQUENCE:
                            globals.INJECTION_SEQUENCE[base_location].append(corrupted_bit)
                        else:
                            globals.INJECTION_SEQUENCE.update({base_location: [corrupted_bit]})
                else:
                    logging.error(str(location) + " doesn't exist or it is not supported for error injection")
                    sys.exit(-1)

                num_injection_attempts -= 1
        return errors_injected
    else:
        logging.error("Specified file does not exist... exiting the tool")
        sys.exit(2)


def corrupt_hdf5_file_based_on_sequence(input_file: str, injection_sequence: {}, locations_to_corrupt: []):
    if path.exists(input_file):
        logging.info("----------- Corrupting file based on sequence, main loop -----------")
        with h5py.File(input_file, 'a') as hdf:
            random.seed(datetime.now())
            for injection_path in injection_sequence:
                inner_locations = hdf5_common.get_full_location_paths_for(injection_path, locations_to_corrupt)
                locations_count = inner_locations.__len__()
                for bit in injection_sequence[injection_path]:
                    next_location_index = random.randint(0, locations_count-1) if locations_count > 1 else 0
                    location = inner_locations[next_location_index]
                    logging.debug("Will corrupt at: " + str(location))
                    dataset = hdf.get(location)
                    if dataset is not None:
                        corrupt_dataset_using_bit(dataset, bit)
    else:
        logging.error("Specified file does not exist... exiting the tool")
        sys.exit(2)


