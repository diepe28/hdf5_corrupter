import yaml
import globals


def print_options(corrupt_locations):
    print()
    print("********** Options **********")
    print(" " + globals.STR_HDF5_FILE + ": " + str(globals.HDF5_FILE))
    print(" " + globals.STR_PROB + ": " + str(globals.PROB))
    print(" " + globals.STR_MAX_CORRUPTION_PERCENTAGE + ": " + str(globals.MAX_CORRUPTION_PERCENTAGE))
    print(" " + globals.STR_SINGLE_INJ + ": " + str(globals.SINGLE_INJ))
    print(" " + globals.STR_BYTE + ": " + str(globals.BYTE))
    print(" " + globals.STR_BIT + ": " + str(globals.BIT))
    print(" " + globals.STR_LOCATIONS_TO_CORRUPT + ":")
    for location in corrupt_locations:
        print("  " + str(location))
    print("********** ------- **********")
    print()


def read_config_file(config_file_path, prints_enabled: bool = True):
    with open(config_file_path) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        globals.HDF5_FILE = data[globals.STR_HDF5_FILE]
        globals.PROB = float(data[globals.STR_PROB])
        globals.MAX_CORRUPTION_PERCENTAGE = float(data[globals.STR_MAX_CORRUPTION_PERCENTAGE])
        globals.SINGLE_INJ = data[globals.STR_SINGLE_INJ] == 1
        globals.BYTE = int(data[globals.STR_BYTE])
        globals.BIT = int(data[globals.STR_BIT])
        globals.LOCATIONS_TO_CORRUPT = data[globals.STR_LOCATIONS_TO_CORRUPT]
        if prints_enabled:
            print_options(globals.LOCATIONS_TO_CORRUPT)
