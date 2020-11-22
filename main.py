import numpy as np
import h5py
import sys, getopt
import random
from os import path


def print_tool_ussage():
    print("hdf5Corrupter.py -h <help> -i <inputFile> -p <pathToCorrupt>")


def corrupt_value(val: float):
    return val + 100


def get_random_indexes(dataset):
    indexes = [0] * dataset.ndim
    currentDim = 0
    for dimLenght in dataset.shape:
        ranIndex = random.randint(0,dimLenght-1)
        indexes[currentDim] = ranIndex
        currentDim += 1

    return indexes


def corrupt_dataset(dataset, prints_enabled: bool = True):
    indexes = get_random_indexes(dataset)
    if prints_enabled:
        print("will corrupt at: " + str(indexes))
    if dataset.ndim == 1:
        dataset[indexes[0]] = corrupt_value(dataset[indexes[0]])
    elif dataset.ndim == 2:
        dataset[indexes[0],indexes[1]] = corrupt_value(dataset[indexes[0],indexes[1]])
    elif dataset.ndim == 3:
        dataset[indexes[0], indexes[1], indexes[2]] =\
            corrupt_value(dataset[indexes[0], indexes[1], indexes[2]])


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


def corrupt_hdf5_file(input_file: str, path_to_corrupt: str, prints_enabled: bool = True):
    if path.exists(input_file):
        with h5py.File(input_file, 'a') as hdf:
            # ls = list(hdf.keys())
            dataset = hdf.get(path_to_corrupt)

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
        print("File: " + input_file + " does not exist... exiting application")
        exit(2)


def main():
    argument_list = sys.argv[1:]
    short_options = "hi:p:"
    long_options = ["help", "inputFile=", "pathToCorrupt="]
    input_file = ''
    path_to_corrupt = ''
    try:
        arguments, values = getopt.getopt(argument_list, short_options, long_options)
    except getopt.error as err:
        # Output error, and return with an error code
        print(str(err))
        sys.exit(2)

    # Evaluate given options
    for current_argument, current_value in arguments:
        if current_argument in ("-i", "--inputFile"):
            input_file = current_value
        elif current_argument in ("-h", "--help"):
            print_tool_ussage()
        elif current_argument in ("-p", "--pathToCorrupt"):
            print("path to corrupt is (%s)" % current_value)
            path_to_corrupt = current_value

    corrupt_hdf5_file(input_file, path_to_corrupt)

if __name__ == "__main__":
    main()