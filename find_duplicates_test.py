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

    def test_compare_to_self(self):
        expected = numpy.array([
            #p  (  h  (  1  ,  2  )  )  a  p  (  h  (  "  ,  2  )  )
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0],  # print
            [0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 7, 0, 2, 0, 0, 0, 0, 0],  # (
            [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0],  # hello
            [0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 2, 0, 7, 0, 0, 0, 0, 0],  # (
            [0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0],  # 1
            [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 0, 0],  # ,
            [0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 0],  # 2
            [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 7, 2],  # )
            [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 7],  # )
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # and
            [7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],  # print
            [0, 7, 0, 2, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0],  # (
            [0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],  # hello
            [0, 2, 0, 7, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0],  # (
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],  # "hi"
            [0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],  # ,
            [0, 0, 0, 0, 2, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],  # 2
            [0, 0, 0, 0, 0, 0, 0, 7, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2],  # )
            [0, 0, 0, 0, 0, 0, 0, 2, 7, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2],  # )
            ])
        actual = find_duplicates.get_lengths(self.matrix, True)
        self.assertTrue((expected == actual).all())

    def test_compare_to_other(self):
        expected = numpy.array([
            # p  (  h  (  1  ,  2  )  )  a  p  (  h  (  "  ,  2  )  ) 
            [20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0],  # print
            [ 0,20, 0,15, 0, 0, 0, 0, 0, 0, 0, 7, 0, 2, 0, 0, 0, 0, 0],  # (
            [ 0, 0,20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0],  # hello
            [ 0,15, 0,20, 0, 0, 0, 0, 0, 0, 0, 2, 0, 7, 0, 0, 0, 0, 0],  # (
            [ 0, 0, 0, 0,20, 0,12, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0],  # 1
            [ 0, 0, 0, 0, 0,20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 0, 0],  # ,
            [ 0, 0, 0, 0,12, 0,20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 0],  # 2
            [ 0, 0, 0, 0, 0, 0, 0,20,11, 0, 0, 0, 0, 0, 0, 0, 0, 7, 2],  # )
            [ 0, 0, 0, 0, 0, 0, 0,11,20, 0, 0, 0, 0, 0, 0, 0, 0, 1, 7],  # )
            [ 0, 0, 0, 0, 0, 0, 0, 0, 0,20, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # and
            [ 7, 0, 0, 0, 0, 0, 0, 0, 0, 0,20, 0, 0, 0, 0, 0, 0, 0, 0],  # print
            [ 0, 7, 0, 2, 0, 0, 0, 0, 0, 0, 0,20, 0, 5, 0, 0, 0, 0, 0],  # (
            [ 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0,20, 0, 0, 0, 0, 0, 0],  # hello
            [ 0, 2, 0, 7, 0, 0, 0, 0, 0, 0, 0, 5, 0,20, 0, 0, 0, 0, 0],  # (
            [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,20, 0, 0, 0, 0],  # "hi"
            [ 0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0,20, 0, 0, 0],  # ,
            [ 0, 0, 0, 0, 2, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0,20, 0, 0],  # 2
            [ 0, 0, 0, 0, 0, 0, 0, 7, 1, 0, 0, 0, 0, 0, 0, 0, 0,20, 2],  # )
            [ 0, 0, 0, 0, 0, 0, 0, 2, 7, 0, 0, 0, 0, 0, 0, 0, 0, 2,20]   # )
            ])

        actual = find_duplicates.get_lengths(self.matrix, False)
        self.assertTrue((expected == actual).all())


if __name__ == '__main__':
    unittest.main()
