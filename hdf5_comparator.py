import h5py
import numpy as np
import sys, getopt
import os
from dataclasses import dataclass
import numpy.linalg
import hdf5_common
import logging

os.environ["OMP_NUM_THREADS"] = "1"


def print_tool_usage_and_exit():
    print("Correct usage of the tool: ")
    print("> hdf<5_comparator.py <arguments>, where the possible arguments are:")
    print("   -h | --help, optional argument, prints this message")
    print("   -b | --beforeFile \"path/to/beforeFile.h5\", path to the before hdf5 file .")
    print("   -a | --afterFile \"path/to/afterFile.h5\", path to the after hdf5 file .")
    print("   -l | --locationsToCompare, optional argument, a list of locations paths inside the hdf5 file to compare, "
          "it will compare all the leaf objects inside such locations. If not given it will use all locations")
    print("   -p | --printDetails, optional argument, If given, prints the diffs for each object compared")
    logging.critical("Wrong use of the tool... exiting")
    sys.exit(2)


@dataclass
class Diff:
    entries_count: float
    diff_count: float
    euclidean_distance: float
    diffs: []


def diff_print(dd: Diff, tabs: str, prefix: str):
    if dd.diff_count > 0 and dd.entries_count > 0:
        diff_percentage = str(dd.diff_count * 100 / dd.entries_count)
        distance = "" if dd.euclidean_distance == -1 else " Euclidean distance: " + str(dd.euclidean_distance)
        txt = "{tabs_str} {prefix_str} {diff_count_str} diff count. Representing {percentage_str}%. {distance_str}\n" \
              "{tabs_str} Actual diffs: {diffs}\n".\
            format(tabs_str=tabs, prefix_str=prefix, diff_count_str=dd.diff_count, percentage_str=diff_percentage,
                   distance_str=distance, diffs=dd.diffs)
        print(txt)


def compare_datasets(before_dataset, after_dataset):
    if before_dataset.ndim != after_dataset.ndim:
        return Diff(entries_count=0, diff_count=0, euclidean_distance=-1, diffs=[])

    if after_dataset.ndim == 0:
        diff_count = 1 if before_dataset[()] != after_dataset[()] else 0
        entries_count = 1
        euclidean_dist = -1
        diffs = []
    else:
        before_narray = np.array(before_dataset).flatten()
        after_narray = np.array(after_dataset).flatten()

        # calculates the diffs of entries in the arrays that are different
        diffs = [abs(y-x)/x for (x, y) in zip(before_narray, after_narray) if x != y]
        diff_count = diffs.__len__()

        euclidean_dist = numpy.linalg.norm(before_narray - after_narray)
        entries_count = np.prod(before_dataset.shape)

    return Diff(entries_count, diff_count, euclidean_dist, diffs)


def compare_files(before_file: str, after_file: str, locations_to_use: [], print_details: bool):
    if os.path.exists(before_file) and os.path.exists(after_file):
        before_locations = hdf5_common.get_hdf5_file_leaf_locations(before_file)
        after_locations = hdf5_common.get_hdf5_file_leaf_locations(after_file)
        final_locations = []

        if before_locations.__len__() > after_locations.__len__():
            print("Before file has less locations than after file, using before file locations for comparison.")
        elif before_locations.__len__() < after_locations.__len__():
            print("After file has less locations than after file, using After file locations for comparison.")
            locations_to_use = after_locations

        # creates list of all children locations for each base location
        for base_location in locations_to_use:
            child_locations = hdf5_common.get_full_location_paths([base_location], before_locations)
            final_locations.append(child_locations)

        with h5py.File(before_file, 'r') as before_hdf5:
            with h5py.File(after_file, 'r') as after_hdf5:
                for children_locations in final_locations:
                    base_location_diff = Diff(0, 0, -1, [])
                    for location in children_locations:
                        before_dataset = before_hdf5.get(location)
                        after_dataset = after_hdf5.get(location)
                        if before_dataset is not None and after_dataset is not None:
                            dataset_diff = compare_datasets(before_dataset, after_dataset)
                            base_location_diff.diff_count += dataset_diff.diff_count
                            base_location_diff.entries_count += dataset_diff.entries_count
                            base_location_diff.diffs.extend(dataset_diff.diffs)
                            if print_details:
                                diff_print(dataset_diff, "\t\t", "Object: \"" + location + "\" has: ")
                        else:
                            print("Object: " + location + " does not exits in both files... skipping it")

                    base_location = hdf5_common.get_base_locations_for(location, base_locations=locations_to_use)
                    if base_location_diff.diff_count == 0:
                        print("\n--\"" + base_location + "\" has not differences ---")
                    else:
                        print("\n--Summary of comparison for \"" + base_location + "\" ---")
                        diff_print(base_location_diff, "\t", "")

    else:
        print("One of the files does not exits! Exiting the tool...")
        sys.exit(2)


# /home/diego/Documents/hdf5_files/check_model_pytorch-original.h5
# /home/diego/Documents/hdf5_files/check_model_pytorch.h5
def main():
    argument_list = sys.argv[1:]
    short_options = "hb:a:l:p"
    long_options = ["help", "beforeFile=", "afterFile=", "locationsToCompare=", "printDetails"]
    before_file_path = ""
    after_file_path = ""
    locations_to_compare = []
    print_details = False

    try:
        arguments, values = getopt.getopt(argument_list, short_options, long_options)
    except getopt.error as err:
        print_tool_usage_and_exit()

    if argument_list.__len__() == 0 or argument_list.__len__() > len(long_options) * 2:
        print_tool_usage_and_exit()

    # Validate argument
    for current_argument, current_value in arguments:
        if current_argument in ("-b", "--beforeFile"):
            before_file_path = current_value
        if current_argument in ("-a", "--afterFile"):
            after_file_path = current_value
        if current_argument in ("-l", "--locationsToCompare"):
            locations_to_compare = current_value.strip('[]').split(',')
        if current_argument in ("-p", "--printDetails"):
            print_details = True
        elif current_argument in ("-h", "--help"):
            print_tool_usage_and_exit()

    # before_file_path = "/home/diego/Documents/hdf5_files/check_model_pytorch-original.h5"
    # after_file_path = "/home/diego/Documents/hdf5_files/check_model_pytorch.h5"
    locations_to_compare = [x.strip() for x in locations_to_compare]
    print("***--- HDF5 file comparison ---***")
    print(" Before File: " + before_file_path)
    print(" After File:  " + after_file_path)
    print(" Will compare every leaf object within locations: " + str(locations_to_compare) + "\n")
    compare_files(before_file_path, after_file_path, locations_to_compare, print_details)


if __name__ == "__main__":
    main()
