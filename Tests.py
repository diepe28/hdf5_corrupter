import unittest

import globals
import hdf5_common
import hdf5_comparator
import settings_reader


class ComparatorTests(unittest.TestCase):

    def test_equal_files(self):
        file_path = "TestFiles/Comparator/Before.h5"
        locations_to_compare = hdf5_common.get_hdf5_file_leaf_locations(file_path)
        diffs = hdf5_comparator.compare_files(file_path, file_path, locations_to_compare, print_details=False)
        files_diff = diffs[0]
        self.assertEqual(files_diff.diff_count, 0, "Should be 0")

    def test_small_diff_files(self):
        before_file_path = "TestFiles/Comparator/Before.h5"
        after_file_path = "TestFiles/Comparator/After.h5"
        locations_to_compare = hdf5_common.get_hdf5_file_leaf_locations(before_file_path)
        diffs = hdf5_comparator.compare_files(before_file_path, after_file_path, locations_to_compare, print_details=False)
        files_diff = diffs[0]
        self.assertEqual(files_diff.diff_count, 3, "Should be 3")


class SettingReaderTests(unittest.TestCase):
    def test_arguments_case1(self):
        hdf5_file = '/home/diego/Documents/hdf5_files/newFiles/ckpt_ch_alexnet_e_10.h5'
        log_file_path = '/home/diego/PycharmProjects/hdf5_corrupter/log-'
        locations_to_corrupt = ['/predictor/conv1/b', '/predictor/conv1']

        my_arguments = [
            '--hdf5File',
            hdf5_file,
            '--floatPrecision',
            '16',
            '--allowSignChange',
            '--logFilePath',
            log_file_path,
            '--injectionType',
            'count',
            '--injectionTries',
            '10',
            '--locationsToCorrupt',
            locations_to_corrupt[0],
            locations_to_corrupt[1],
        ]

        settings_reader.read_arguments(my_arguments)
        settings_reader.init_corrupter()
        self.assertEqual(globals.HDF5_FILE, hdf5_file)
        self.assertEqual(globals.FLOAT_PRECISION, 16)
        self.assertEqual(globals.ALLOW_SIGN_CHANGE, True)
        self.assertEqual(globals.LOG_FILE_PATH, log_file_path)
        self.assertEqual(globals.INJECTION_TYPE, "count")
        self.assertEqual(globals.INJECTION_TRIES, 10)
        self.assertEqual(len(globals.LOCATIONS_TO_CORRUPT), 2)
        self.assertEqual(globals.LOCATIONS_TO_CORRUPT[0], locations_to_corrupt[0])
        self.assertEqual(globals.LOCATIONS_TO_CORRUPT[1], locations_to_corrupt[1])


