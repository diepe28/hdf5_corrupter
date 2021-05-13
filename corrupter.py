import numpy as np
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


def log_delta(val_type: str, before_val, after_val, changed_bits, scaling_factor=None):
    corruption_type = "by a scale factor: " + str(scaling_factor) if scaling_factor is not None else\
        "at bits: " + str(changed_bits)

    logging.debug(val_type + " location value was corrupted " + corruption_type +
                  "  Delta> " + str(before_val) + " --> " + str(after_val))


# given the range start and range end, it generates a random sample of the given length
def generate_random_sample(start: int, end: int, length: int, allow_0=False):
    random.seed(datetime.now())
    the_range = range(start, end)
    range_length = end - start
    sample = []
    while length > range_length:
        new_sample = random.sample(the_range, range_length)
        sample.extend(new_sample)
        length -= range_length

    new_sample = random.sample(the_range, length)
    sample.extend(new_sample)

    # first_bit should have been decreased by 1 when reading args, then occurrences on first_bit should actually 0
    if allow_0:
        sample = [0 if x == start else x for x in sample]

    return sample


# assumes string have same length
def string_xor(str1: str, str2: str):
    result = ""
    for x, y in zip(str1, str2):
        result += str(int(x) ^ int(y))

    return result


# given the bit mask and desired length, it pads n zeros at start and (length-n-mascLength) zeros at the end, n is rand
def random_pad_mask(masc: str, length: int):
    random.seed(datetime.now())
    masc_length = len(masc)
    start = random.randint(0, length - masc_length)
    zeros_start = '0' * start
    zeros_end = '0' * (length - masc_length - start)
    result = zeros_start + masc + zeros_end
    return result


def bin_to_float(b):
    bf = int_to_bytes(int(b, 2), globals.BYTES_PER_FLOAT)  # 8 bytes needed for IEEE 754 binary64.
    return struct.unpack(globals.PRECISION_CODE, bf)[0]


def int_to_bytes(n, length):  # Helper function
    return decode('%%0%dx' % (length << 1) % n, 'hex')[-length:]


def float_to_bin(num):
    # Struct can provide us with the float packed into bytes. The '!' ensures that
    # it's in network byte order (big-endian) and the 'f' says that it should be
    # packed as a float. Alternatively, for double-precision, you could use 'd'.
    packed = struct.pack(globals.PRECISION_CODE, num)
    # print('Packed: %s' % repr(packed))

    # For each character in the returned string, we'll turn it into its corresponding
    # integer code point
    #
    # [62, 163, 215, 10] = [ord(c) for c in '>\xa3\xd7\n']
    integers = [c for c in packed]
    # print('Integers: %s' % integers)

    # For each integer, we'll convert it to its binary representation.
    binaries = [bin(i) for i in integers]
    # print('Binaries: %s' % binaries)

    # Now strip off the '0b' from each of these
    stripped_binaries = [s.replace('0b', '') for s in binaries]
    # print('Stripped: %s' % stripped_binaries)

    # Pad each byte's binary representation's with 0's to make sure it has all 8 bits:
    #
    # ['00111110', '10100011', '11010111', '00001010']
    padded = [s.rjust(8, '0') for s in stripped_binaries]
    # print('Padded: %s' % padded)

    # At this point, we have each of the bytes for the network byte ordered float
    # in an array as binary strings. Now we just concatenate them to get the total
    # representation of the float:
    return ''.join(padded)


def change_bit_in_binary(binary: str, index: int):
    bit_flipped = "1" if binary[index] == '0' else "0"
    binary = binary[:index] + bit_flipped + binary[index + 1:]
    return binary


def corrupt_int(val: int):
    binary = str(bin(val))[2:]
    chosen_bit = randint(0, len(binary) - 1)
    new_binary = change_bit_in_binary(binary, chosen_bit)
    new_val = int(new_binary, 2)
    return new_val, chosen_bit


def corrupt_float_at_bits(val: float, chosen_bits: []):
    successful_bits = chosen_bits.copy()
    new_val = val
    for bit in chosen_bits:
        binary = float_to_bin(new_val)
        new_binary = change_bit_in_binary(binary, bit)
        temp_val = bin_to_float(new_binary)
        if not globals.ALLOW_NaN_VALUES and (math.isnan(temp_val) or math.isinf(temp_val)):
            successful_bits.remove(bit)
        else:
            # successful corruption
            new_val = temp_val

    failed_attempts = len(chosen_bits) - len(successful_bits)
    if failed_attempts > 0:
        start = 0 if globals.FIRST_BIT is None else globals.FIRST_BIT
        end = 63 if globals.LAST_BIT is None else globals.LAST_BIT
        new_val, other_successful_bits =\
            corrupt_float_at_bits(new_val, generate_random_sample(
                start=start,
                end=end,
                length=failed_attempts,
                allow_0=globals.ALLOW_SIGN_CHANGE
            ))
        successful_bits.extend(other_successful_bits)

    return new_val, successful_bits


# returns list with the indexes of all the 1s on the mask
def get_corrupted_bits_from_mask(mask: str):
    corrupted_bits = []
    for i in range(0, len(mask)):
        if mask[i] == '1':
            corrupted_bits.append(i)

    return corrupted_bits


# corrupts a float value using a bit mask
def corrupt_float_using_mask(val: float, mask: str):
    return _corrupt_float_using_mask(val, mask, random_pad_mask(mask, globals.FLOAT_PRECISION))


# aux method
def _corrupt_float_using_mask(val: float, mask: str, full_mask: str):
    val_binary = float_to_bin(val)
    new_binary = string_xor(val_binary, full_mask)
    temp_val = bin_to_float(new_binary)
    if not globals.ALLOW_NaN_VALUES and (math.isnan(temp_val) or math.isinf(temp_val)):
        return corrupt_float_using_mask(val, mask)

    return temp_val, get_corrupted_bits_from_mask(full_mask)


# Given a corruption probability, it tries to corrupt the value at injection_burs-different bits
def try_corrupt_value(val, corruption_prob: float, injection_burst: int):
    random.seed(datetime.now())
    chosen_bits = None
    if random.random() < corruption_prob:
        str_val_type = str(type(val))
        if globals.SCALING_FACTOR is None:
            if "int" in str_val_type:
                new_val, chosen_bits = corrupt_int(val)
                log_delta("Int", val, new_val, chosen_bits)
            else:
                # Injection with bit range
                if globals.BIT_MASK is None:
                    chosen_bits = generate_random_sample(
                        start=globals.FIRST_BIT,
                        end=globals.LAST_BIT,
                        length=injection_burst,
                        allow_0=globals.ALLOW_SIGN_CHANGE
                    )
                    new_val, chosen_bits = corrupt_float_at_bits(val, chosen_bits)
                    log_delta("Float", val, new_val, chosen_bits)

                # Injection with bit mask
                else:
                    new_val, chosen_bits = corrupt_float_using_mask(val, globals.BIT_MASK)
                    log_delta("Float", val, new_val, chosen_bits)

        # Injection with scaling factor
        else:
            new_val = val * globals.SCALING_FACTOR
            chosen_bits = [-2]  # -2, so it counts the injection
            log_delta("", val, new_val, -1, globals.SCALING_FACTOR)

        return new_val, chosen_bits

    logging.debug("Did not corrupt value at the index")
    return val, chosen_bits


# given the bit to flip, it corrupts the value changing that bit
def corrupt_value_at_bits(val, chosen_bits: []):
    str_val_type = str(type(val))
    if "int" in str_val_type:
        new_val, chosen_bits = corrupt_int(val)
        log_delta("Int", val, new_val, chosen_bits)
    else:
        new_val, chosen_bits = corrupt_float_at_bits(val, chosen_bits)
        log_delta("Float", val, new_val, chosen_bits)

    return new_val, chosen_bits


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


# Tries to corrupt the given dataset at a random index with the given probability
def try_corrupt_dataset(dataset, corruption_prob: float, injection_burst: int):
    corrupted_bits = None
    r_pos = __get_random_indexes(dataset)
    logging.debug("Indexes to corrupt: " + str(r_pos))
    if dataset.ndim == 0:
        dataset[()], corrupted_bits = try_corrupt_value(dataset[()], corruption_prob, injection_burst)
    elif dataset.ndim == 1:
        dataset[r_pos[0]], corrupted_bits = try_corrupt_value(dataset[r_pos[0]], corruption_prob, injection_burst)
    elif dataset.ndim == 2:
        dataset[r_pos[0], r_pos[1]], corrupted_bits = \
            try_corrupt_value(dataset[r_pos[0], r_pos[1]], corruption_prob, injection_burst)
    elif dataset.ndim == 3:
        dataset[r_pos[0], r_pos[1], r_pos[2]], corrupted_bits = \
            try_corrupt_value(dataset[r_pos[0], r_pos[1], r_pos[2]], corruption_prob, injection_burst)
    elif dataset.ndim == 4:
        dataset[r_pos[0], r_pos[1], r_pos[2], r_pos[3]], corrupted_bits = \
            try_corrupt_value(dataset[r_pos[0], r_pos[1], r_pos[2], r_pos[3]], corruption_prob, injection_burst)
    # more than 4 is very unlikely... right?

    return corrupted_bits


# Corrupts a random value in a dataset at the chosen bits
def corrupt_dataset_using_bits(dataset, chosen_bits: []):
    r_pos = __get_random_indexes(dataset)
    logging.debug("Indexes to corrupt: " + str(r_pos))
    if dataset.ndim == 0:
        dataset[()], corrupted_bit = corrupt_value_at_bits(dataset[()], chosen_bits)
    elif dataset.ndim == 1:
        dataset[r_pos[0]], corrupted_bit = corrupt_value_at_bits(dataset[r_pos[0]], chosen_bits)
    elif dataset.ndim == 2:
        dataset[r_pos[0], r_pos[1]], corrupted_bit = \
            corrupt_value_at_bits(dataset[r_pos[0], r_pos[1]], chosen_bits)
    elif dataset.ndim == 3:
        dataset[r_pos[0], r_pos[1], r_pos[2]], corrupted_bit = \
            corrupt_value_at_bits(dataset[r_pos[0], r_pos[1], r_pos[2]], chosen_bits)
    elif dataset.ndim == 4:
        dataset[r_pos[0], r_pos[1], r_pos[2], r_pos[3]], corrupted_bit = \
            corrupt_value_at_bits(dataset[r_pos[0], r_pos[1], r_pos[2], r_pos[3]], chosen_bits)
    # more than 4 is very unlikely... right?


# Tries to corrupt the input file at the given locations, with the given probability, num_injection_attempts times
def try_corrupt_hdf5_file(input_file: str, locations_to_corrupt, corruption_prob: float,
                          num_injection_attempts: int, injection_burst: int):
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
                    corrupted_bits = try_corrupt_dataset(dataset, corruption_prob, injection_burst)
                    if corrupted_bits is not None:
                        errors_injected += 1
                    if globals.SAVE_INJECTION_SEQUENCE:
                        base_location = hdf5_common.get_base_locations_for(location, globals.BASE_LOCATIONS)
                        if base_location in globals.INJECTION_SEQUENCE:
                            globals.INJECTION_SEQUENCE[base_location].append(corrupted_bits)
                        else:
                            globals.INJECTION_SEQUENCE.update({base_location: [corrupted_bits]})
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
                for bits in injection_sequence[injection_path]:
                    next_location_index = random.randint(0, locations_count-1) if locations_count > 1 else 0
                    location = inner_locations[next_location_index]
                    logging.debug("Will corrupt at: " + str(location))
                    dataset = hdf.get(location)
                    if dataset is not None:
                        corrupt_dataset_using_bits(dataset, bits)
    else:
        logging.error("Specified file does not exist... exiting the tool")
        sys.exit(2)


