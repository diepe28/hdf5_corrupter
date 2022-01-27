import h5py
import numpy as np
import sys, getopt
import os
import settings_reader
import globals
import corrupter
import logging

os.environ["OMP_NUM_THREADS"] = "1"


def handle_error(error_message, arg_parser: object):
    error_message = "CRITICAL: " + error_message + "\n"
    print(error_message)
    logging.error(error_message)
    arg_parser.print_help()
    sys.exit(2)


# each item is a tuple: {name, group}
def print_hdf5_item(item: tuple, prefix: str):
    item_name = item[0]
    item_val = item[1]
    item_info = prefix + "\"" + item_name + "\" --- Type: " + str(type(item_val))

    if getattr(item_val, "items", None) is not None:
        logging.info(item_info)
        sub_items = list(item_val.items())
        for sub_item in sub_items:
            print_hdf5_item(sub_item, "\t" + prefix)
        logging.info("")
    else:
        # get dataset and print info about it, not the data
        numpy_array = np.array(item_val)
        # print(numpy_array)
        if numpy_array is not None:
            item_info += " --- Dimensions: ["
            if numpy_array.ndim > 0:
                total_values_count = numpy_array.shape[0]
                item_info += str(numpy_array.shape[0])
                for i in range(1, len(numpy_array.shape)):
                    total_values_count *= numpy_array.shape[i]
                    item_info += " , " + str(numpy_array.shape[i])
                item_info += "]"
            else:
                item_info += "0]"
            item_info += " --- Value Count: " + str(total_values_count)
            logging.info(item_info)


def print_hdf5_file(input_file: str):
    logging.info("Printing only the HDF5 file")
    if os.path.exists(input_file):
        with h5py.File(input_file, 'r') as hdf:
            base_items = list(hdf.items())
            for item in base_items:
                print_hdf5_item(item, "")
    else:
        logging.error("Specified file does not exist... exiting the tool")
        sys.exit(2)


# each item is a tuple: {name, group}
def count_hdf5_item_entries(item: tuple):
    item_val = item[1]
    count = 0

    # if it has the "items" property it means it is not a leaf
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
    if os.path.exists(input_file):
        with h5py.File(input_file, 'r') as hdf:
            base_items = list(hdf.items())
            for item in base_items:
                count += count_hdf5_item_entries(item)
    else:
        logging.error("Specified file does not exist... exiting the tool")
        sys.exit(2)

    logging.debug("Number of entries in the file: " + str(count))
    return count


# each item is a tuple: {name, group}
def __get_hdf5_file_leaf_locations(item: tuple, leaf_locations: list, prefix: str):
    """ Stores in @leaf_locations all the leaves of the tree
    :param item: a node of the tree with {item_name, item_val}, where val can be a list of its children
    :param leaf_locations: the list where the leaves are added
    :param prefix: the current full path name
    :return: nothing
    """
    item_name = prefix + item[0]
    item_val = item[1]

    # if it has the "items" property it means it is not a leaf
    if getattr(item_val, "items", None) is not None:
        sub_items = list(item_val.items())
        for sub_item in sub_items:
            __get_hdf5_file_leaf_locations(sub_item, leaf_locations, item_name + "/")

    else:
        leaf_locations.append(item_name)


def get_hdf5_file_leaf_locations(input_file: str):
    leaf_locations = []
    logging.info("Calculating locations to inject errors in the file")
    if os.path.exists(input_file):
        with h5py.File(input_file, 'r') as hdf:
            base_items = list(hdf.items())
            for item in base_items:
                __get_hdf5_file_leaf_locations(item, leaf_locations, "/")
    else:
        error_message = "Specified file does not exist... exiting the tool"
        print(error_message)
        logging.error(error_message)
        sys.exit(2)

    logging.debug("Number of locations to inject errors: " + str(len(leaf_locations)))
    return leaf_locations


def get_full_location_paths(locations_to_corrupt: [], all_location_paths: []):
    """ Given the paths to corrupt, it calculates all the full location paths within each path
    Example: locations_to_corrupt = ["conv1", "conv2"], and within each one of them there are two objects, so
    it will return ["conv1/object1", "conv1/object2", "conv2/object1", "conv2/object2"]
    :param locations_to_corrupt:
    :param all_location_paths:
    :return:
    """
    full_location_paths = []
    for corruptible_location in locations_to_corrupt:
        location_exists = False
        for full_path in all_location_paths:
            if full_path.startswith(corruptible_location):
                full_location_paths.append(full_path)
                location_exists = True
        if not location_exists:
            error_message = "There are no locations with the prefix: " + corruptible_location + "... exiting tool"
            print(error_message)
            logging.error(error_message)
            sys.exit(2)

    return full_location_paths


# given a path it returns all full locations within that path
def get_full_location_paths_for(given_path: str, all_paths: []):
    full_paths = []
    for full_path in all_paths:
        if full_path.startswith(given_path):
            full_paths.append(full_path)

    return full_paths


# returns the base location of a given location
def get_base_locations_for(current_location: str, base_locations: []):
    for base_location in base_locations:
        if current_location.startswith(base_location):
            return base_location

    return ""
