#!/usr/bin/env python3
from parameterized import parameterized
import PIL.Image
import PIL.ImageChops
import unittest

import find_duplicates
import tokenizer
import utils


class TestGetLengths(unittest.TestCase):
    @staticmethod
    def generate_image(filename_a, filename_b):
        data_a = tokenizer.get_file_tokens(f"examples/{filename_a}")
        data_b = tokenizer.get_file_tokens(f"examples/{filename_b}")
        matrix = utils.make_matrix(data_a.tokens, data_b.tokens)
        hues = find_duplicates.get_hues(matrix, (filename_a == filename_b))
        actual_matrix = utils.to_hsv_matrix(matrix, hues)
        actual_image = PIL.Image.fromarray(actual_matrix, mode="HSV")
        # We need to convert to RGB space before comparing. In HSV space, there
        # are lots of triples that should be considered identical (e.g., when
        # the value is 0, it doesn't matter what the saturation is).
        return actual_image.convert(mode="RGB")

    def assertImagesMatch(self, expected_filename, actual_image):
        expected_image = PIL.Image.open(f"test_images/{expected_filename}")
        # This used to be a `self.assertEqual`, but when it fails, formatting
        # the error message takes forever.
        self.assertTrue(list(actual_image.getdata()) ==
                        list(expected_image.getdata()))

    @parameterized.expand((("cpp_example.hpp",),
                          ("index.js",),
                          ("lsbattle_entity_wireframe.py",),
                          ("pointsprite.py",),
                          ("server.go",),
                          ))
    def test_single_file(self, filename):
        actual_image = self.generate_image(filename, filename)
        # Surely there's a better way to replace a file extension, but I can't
        # think of it right now.
        image_filename = f"{filename.split('.')[0]}.png"
        self.assertImagesMatch(image_filename, actual_image)


    @parameterized.expand((("gpsnmea.go", "gpsrtk.go", "gps.png"),
                          ))
    def test_two_files(self, filename_a, filename_b, image_filename):
        actual_image = self.generate_image(filename_a, filename_b)
        self.assertImagesMatch(image_filename, actual_image)


if __name__ == '__main__':
    unittest.main()
