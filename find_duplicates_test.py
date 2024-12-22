#!/usr/bin/env python3
import numpy
import unittest

import find_duplicates
import visual_diff


class TestGetLengths(unittest.TestCase):
    def setUp(self):
        contents = 'print(hello(1, 2)) and print(hello("hi", 2))'
        data = visual_diff.get_tokens(contents, "python")
        self.matrix = visual_diff.make_matrix(data.tokens, data.tokens)

    @staticmethod
    def debug_differences(expected, actual):
        print("expected:")
        print(expected)
        print("actual:")
        print(actual)
        print("diff:")
        print(expected - actual)
        print("total", numpy.sum(expected - actual))

    def test_compare_to_self(self):
        expected = numpy.array([
            #p  (  h  (  1  ,  2  )  )  a  p  (  h  (  "  ,  2  )  )
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0],  # print
            [0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 8, 0, 1, 0, 0, 0, 0, 0],  # (
            [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0],  # hello
            [0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 8, 0, 0, 0, 0, 0],  # (
            [0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],  # 1
            [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0, 0],  # ,
            [0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0],  # 2
            [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 8, 1],  # )
            [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 8],  # )
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # and
            [8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],  # print
            [0, 8, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0],  # (
            [0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],  # hello
            [0, 1, 0, 8, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0],  # (
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],  # "hi"
            [0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],  # ,
            [0, 0, 0, 0, 1, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],  # 2
            [0, 0, 0, 0, 0, 0, 0, 8, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],  # )
            [0, 0, 0, 0, 0, 0, 0, 1, 8, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],  # )
            ])
        actual = find_duplicates.get_lengths(self.matrix, True)
        #self.debug_differences(expected, actual)
        self.assertTrue((expected - actual == 0).all())

    def test_compare_to_other(self):
        expected = numpy.array([
            # p  (  h  (  1  ,  2  )  )  a  p  (  h  (  "  ,  2  )  ) 
            [19, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0],  # print
            [ 0,19, 0, 1, 0, 0, 0, 0, 0, 0, 0, 8, 0, 1, 0, 0, 0, 0, 0],  # (
            [ 0, 0,19, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0],  # hello
            [ 0, 1, 0,19, 0, 0, 0, 0, 0, 0, 0, 1, 0, 8, 0, 0, 0, 0, 0],  # (
            [ 0, 0, 0, 0,19, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],  # 1
            [ 0, 0, 0, 0, 0,19, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0, 0],  # ,
            [ 0, 0, 0, 0, 1, 0,19, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0],  # 2
            [ 0, 0, 0, 0, 0, 0, 0,19, 1, 0, 0, 0, 0, 0, 0, 0, 0, 8, 1],  # )
            [ 0, 0, 0, 0, 0, 0, 0, 1,19, 0, 0, 0, 0, 0, 0, 0, 0, 1, 8],  # )
            [ 0, 0, 0, 0, 0, 0, 0, 0, 0,19, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # and
            [ 8, 0, 0, 0, 0, 0, 0, 0, 0, 0,19, 0, 0, 0, 0, 0, 0, 0, 0],  # print
            [ 0, 8, 0, 1, 0, 0, 0, 0, 0, 0, 0,19, 0, 1, 0, 0, 0, 0, 0],  # (
            [ 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0,19, 0, 0, 0, 0, 0, 0],  # hello
            [ 0, 1, 0, 8, 0, 0, 0, 0, 0, 0, 0, 1, 0,19, 0, 0, 0, 0, 0],  # (
            [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,19, 0, 0, 0, 0],  # "hi"
            [ 0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0,19, 0, 0, 0],  # ,
            [ 0, 0, 0, 0, 1, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0,19, 0, 0],  # 2
            [ 0, 0, 0, 0, 0, 0, 0, 8, 1, 0, 0, 0, 0, 0, 0, 0, 0,19, 1],  # )
            [ 0, 0, 0, 0, 0, 0, 0, 1, 8, 0, 0, 0, 0, 0, 0, 0, 0, 1,19]   # )
            ])
        actual = find_duplicates.get_lengths(self.matrix, False)
        #self.debug_differences(expected, actual)
        self.assertTrue((expected - actual == 0).all())


if __name__ == '__main__':
    unittest.main()
