#!/usr/bin/env python3
import unittest

import generate_report
import tokenizer


class TestGenerateReports(unittest.TestCase):
    def test_file_against_self(self):
        pointsprite_info = tokenizer.get_file_tokens("examples/pointsprite.py")
        actual = list(generate_report.compare_files(
                pointsprite_info, pointsprite_info, 100))
        expected = [
            "Found duplicated code between examples/pointsprite.py and examples/pointsprite.py:",
            "    706 tokens on lines 28-121 and lines 121-295",
            "    126 tokens on lines 90-105 and lines 104-121",
            "    126 tokens on lines 90-105 and lines 280-295",
            "    126 tokens on lines 104-121 and lines 266-281",
            "    126 tokens on lines 266-281 and lines 280-295",
            ]
        self.assertEqual(expected, actual)

    def test_file_pair(self):
        nmea_info = tokenizer.get_file_tokens("examples/gpsnmea.go")
        rtk_info = tokenizer.get_file_tokens("examples/gpsrtk.go")
        actual = list(generate_report.compare_all_files(
                [nmea_info, rtk_info], 100))
        expected = [
            "Found duplicated code between examples/gpsnmea.go and examples/gpsrtk.go:",
            "    413 tokens on lines 69-131 and lines 85-152",
            "Found duplicated code between examples/gpsrtk.go and examples/gpsrtk.go:",
            "    120 tokens on lines 278-316 and lines 312-352",
            "    116 tokens on lines 352-363 and lines 487-498",
            "    142 tokens on lines 395-423 and lines 446-472",
            "    362 tokens on lines 559-618 and lines 567-626",
            "    305 tokens on lines 559-610 and lines 575-626",
            "    251 tokens on lines 559-602 and lines 583-626",
            "    212 tokens on lines 559-594 and lines 591-626",
            "    130 tokens on lines 559-578 and lines 607-626",
            "    164 tokens on lines 562-586 and lines 602-626",
            ]
        self.assertEqual(expected, actual)

    def test_file_globbing(self):
        actual = generate_report.find_all_files(
            ["examples/*.py", "examples/*.?pp"])
        expected = {
            "python": ["examples/lsbattle_entity_wireframe.py",
                       "examples/pointsprite.py"],
            "cpp": ["examples/cpp_example.hpp",
                    "examples/viam_mlmodelservice_triton_impl.cpp"],
        }
        # To make the tests deterministic, sort each value.
        actual_sorted = {k: sorted(v) for k, v in actual.items()}
        self.assertEqual(expected, actual_sorted)


if __name__ == '__main__':
    unittest.main()
