#!/usr/bin/env python3
import numpy
from parameterized import parameterized
import PIL.Image
import PIL.ImageChops
import unittest

import find_duplicates
import tokenizer
import utils


class TestGetLengths(unittest.TestCase):
    @parameterized.expand((("cpp_example.hpp",),
                          ("index.js",),
                          ("lsbattle_entity_wireframe.py",),
                          ("pointsprite.py",),
                          ("server.go",),
                          ))
    def test_single_file(self, filename):
        data = tokenizer.get_file_tokens(f"examples/{filename}")
        matrix = utils.make_matrix(data.tokens, data.tokens)
        hues = find_duplicates.get_hues(matrix, True)
        temporary_matrix = utils.to_hsv_matrix(matrix, hues)
        # We need to convert to RGB space before comparing. In HSV space, there
        # are lots of triples that should be considered identical (e.g., when
        # the value is 0, it doesn't matter what the saturation is).
        actual_image = PIL.Image.fromarray(temporary_matrix,
                                           mode="HSV").convert(mode="RGB")
        actual_matrix = numpy.array(actual_image.getdata()).reshape(
                actual_image.size[1], actual_image.size[0], 3)

        # Surely there's a better way to replace a file extension, but I can't
        # think of it right now.
        image_filename = f"test_images/{filename.split('.')[0]}.png"
        expected_image = PIL.Image.open(image_filename)
        expected_matrix = numpy.array(expected_image.getdata()).reshape(
                expected_image.size[1], expected_image.size[0], 3)
        #print("actual:", actual_matrix[:10, :10, :])
        #print("expected:", expected_matrix[:10, :10, :])
        for r in range(expected_matrix.shape[0]):
            for c in range(expected_matrix.shape[1]):

                e = expected_matrix[r, c, :]
                a = actual_matrix[r, c, :]
                if (e != a).any():
                    print(f"pixel {r}, {c} differs! Expected {e} but got {a}, "
                          f"for '{data.tokens[r]}' at {data.boundaries[r]} vs. "
                          f"for '{data.tokens[c]}' at {data.boundaries[c]} vs. "
                          )
        self.assertLess(numpy.sum(actual_matrix != expected_matrix), 1)


if __name__ == '__main__':
    unittest.main()
