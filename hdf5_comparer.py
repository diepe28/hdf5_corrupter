import h5py
import numpy as np
import sys, getopt
import os
from dataclasses import dataclass
import hdf5_common
import logging

os.environ["OMP_NUM_THREADS"] = "1"


def print_tool_ussage_and_exit():
    print("Correct usage of the tool: ")
    print("> hdf<5_comparer.py <arguments>, where the possible arguments are:")
    print("   -h | --help, optional argument, prints this message")
    print("   -b | --beforeFile \"path/to/beforeFile.h5\", path to the before hdf5 file .")
    print("   -a | --afterFile \"path/to/afterFile.h5\", path to the after hdf5 file .")
    logging.critical("Wrong use of the tool... exiting")
    sys.exit(2)


@dataclass
class Diff:
    entries_count: float
    diff_count: float


def diff_print(dd: Diff, prefix: str):
    if dd.diff_count > 0 and dd.entries_count > 0:
        diff_percentage = str(dd.diff_count * 100 / dd.entries_count)
        print(prefix + str(dd.diff_count) + " diffs. Representing " + diff_percentage + "% of difference")


def compare_datasets(before_dataset, after_dataset):

    if before_dataset.ndim != after_dataset.ndim:
        return Diff(0, 0)

    if after_dataset.ndim == 0:
        diff_count = 1 if before_dataset[()] != after_dataset[()] else 0
        entries_count = 1
    else:
        # diffs_narray = np.subtract(before_dataset, after_dataset)
        before_narray = np.array(before_dataset)
        after_narray = np.array(after_dataset)
        diffs_narray = before_narray - after_narray

        #actual_diffs = filter(lambda x: x != 0, diffs_narray)
        actual_diffs = [x for x in diffs_narray.flatten() if x != 0]
        diff_count = actual_diffs.__len__()
        entries_count = np.prod(before_dataset.shape)

    return Diff(entries_count, diff_count)


def compare_files(before_file: str, after_file: str):
    if os.path.exists(before_file) and os.path.exists(after_file):
        before_locations = hdf5_common.get_hdf5_file_leaf_locations(before_file)
        after_locations = hdf5_common.get_hdf5_file_leaf_locations(after_file)
        locations_to_use = before_locations

        if before_locations.__len__() > after_locations.__len__():
            print("Before file has less locations than after file, using before file locations for comparison.")
        elif before_locations.__len__() < after_locations.__len__():
            print("After file has less locations than after file, using After file locations for comparison.")
            locations_to_use = after_locations

        file_diff = Diff(0, 0)
        with h5py.File(before_file, 'r') as before_hdf5:
            with h5py.File(after_file, 'r') as after_hdf5:
                for location in locations_to_use:
                    before_dataset = before_hdf5.get(location)
                    after_dataset = after_hdf5.get(location)
                    if before_dataset is not None and after_dataset is not None:
                        dataset_diff = compare_datasets(before_dataset, after_dataset)
                        file_diff.diff_count += dataset_diff.diff_count
                        file_diff.entries_count += dataset_diff.entries_count
                        diff_print(dataset_diff, "\t Location: " + location + " has: ")
                    else:
                        print("Location: " + location + " does not exits in both files... skipping it")

        return file_diff

    else:
        print("One of the files does not exits! Exiting the tool...")
        sys.exit(2)


#/home/diego/Documents/hdf5_files/check_model_pytorch-original.h5
#/home/diego/Documents/hdf5_files/check_model_pytorch.h5
def main():
    argument_list = sys.argv[1:]
    short_options = "hb:a:"
    long_options = ["help", "beforeFile=", "afterFile="]
    before_file_path = ""
    after_file_path = ""

    try:
        arguments, values = getopt.getopt(argument_list, short_options, long_options)
    except getopt.error as err:
        print_tool_ussage_and_exit()

    if argument_list.__len__() == 0 or argument_list.__len__() > len(long_options) * 2:
        print_tool_ussage_and_exit()

    # Validate argument
    for current_argument, current_value in arguments:
        if current_argument in ("-b", "--beforeFile"):
            before_file_path = current_value
        if current_argument in ("-a", "--afterFile"):
            after_file_path = current_value
        elif current_argument in ("-h", "--help"):
            print_tool_ussage_and_exit()

    before_file_path = "/home/diego/Documents/hdf5_files/check_model_pytorch-original.h5"
    after_file_path = "/home/diego/Documents/hdf5_files/check_model_pytorch.h5"
    print("***--- HDF5 file comparison ---***")
    print(" Before File: " + before_file_path)
    print(" After File:  " + after_file_path)
    file_diff = compare_files(before_file_path, after_file_path)
    print(" ")
    diff_print(file_diff, " Files have: ")


if __name__ == "__main__":
    main()
