#!/usr/bin/env python3
import unittest

import generate_report


class TestGenerateReports(unittest.TestCase):
    def test_file_against_self(self):
        actual = generate_report.compare_files("examples/pointsprite.py",
                                               "examples/pointsprite.py",
                                               "python", 100)
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
        actual = generate_report.compare_all_files(
            ["examples/gpsnmea.go", "examples/gpsrtk.go"], "go", 100)
        expected = [
            "Found duplicated code between examples/gpsnmea.go and examples/gpsrtk.go:",
            "    413 tokens on lines 61-123 and lines 77-144",
            "Found duplicated code between examples/gpsrtk.go and examples/gpsrtk.go:",
            "    120 tokens on lines 270-308 and lines 304-344",
            "    116 tokens on lines 344-355 and lines 479-490",
            "    142 tokens on lines 387-415 and lines 438-464",
            "    362 tokens on lines 551-610 and lines 559-618",
            "    305 tokens on lines 551-602 and lines 567-618",
            "    251 tokens on lines 551-594 and lines 575-618",
            "    212 tokens on lines 551-586 and lines 583-618",
            "    130 tokens on lines 551-570 and lines 599-618",
            "    164 tokens on lines 554-578 and lines 594-618",
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
