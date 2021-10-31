import unittest
import hdf5_common
import hdf5_comparator


class TestComparator(unittest.TestCase):

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
