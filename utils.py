import collections
import numpy

# The tokens is a list of tokens contained in a file.
# The lines is a list of strings containing the file contents.
# The boundaries is a list of ((start_row, start_col), (end_row, end_col))
#     tuples for each token.
FileInfo = collections.namedtuple("FileInfo", ["tokens", "lines", "boundaries"])


def to_hsv_matrix(matrix, hues):
    """
    The matrix is a 2D array of uint8's. The hues are either None or another 2D
    array of the same shape.

    We return a 3D array representing an HSV image of the matrix, optionally
    colored by the hues.
    """
    result = numpy.zeros([*matrix.shape, 3], numpy.uint8)
    result[:, :, 2] = matrix * 255
    if hues is not None:
        result[:, :, 0] = hues
        result[:, :, 1] = 255  # Saturation
    return result


class SegmentUnionFind:
    """
    UnionFind is sometimes named DisjointSet. Our data structure is different
    from the usual one because it represents a set of duplicated tokens, with a
    top-right and bottom-left coordinate, in addition to the size.
    """
    def __init__(self, r, c):
        self._size = 1
        self._root = self
        self._top_r = r
        self._top_c = c
        self._bottom_r = r
        self._bottom_c = c

    def _get_root(self):
        if self._root is self:
            return self

        self._root = self._root._get_root()
        return self._root

    def size(self):
        return self._get_root()._size

    def merge(self, other):
        if self.size() > other.size():
            large_root = self._get_root()
            small_root = other._get_root()
        else:
            large_root = other._get_root()
            small_root = self._get_root()

        small_root._root = large_root
        large_root._size += small_root.size()

        large_root._top_r, large_root._top_c = min(
            (small_root._top_r, small_root._top_c),
            (large_root._top_r, large_root._top_c))
        large_root._bottom_r, large_root._bottom_c = max(
            (small_root._bottom_r, small_root._bottom_c),
            (large_root._bottom_r, large_root._bottom_c))
