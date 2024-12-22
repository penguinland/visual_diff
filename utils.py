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
        self.top = (r, c)
        self.bottom = (r, c)

    def get_root(self):
        if self._root is self:
            return self

        self._root = self._root.get_root()
        return self._root

    def size(self):
        return self.get_root()._size

    def merge(self, other):
        if self.size() > other.size():
            large_root = self.get_root()
            small_root = other.get_root()
        else:
            large_root = other.get_root()
            small_root = self.get_root()

        large_root._size += small_root.size()
        small_root._root = large_root

        if sum(small_root.top) < sum(large_root.top):
            # The top of the small section is further towards the top-left
            # corner. Use it as the new top.
            large_root.top = small_root.top

        if sum(small_root.bottom) > sum(large_root.bottom):
            # The bottom of the small section is further towards the
            # bottom-right corner. Use it as the new bottom.
            large_root.bottom = small_root.bottom

    def __str__(self):
        root = self.get_root()
        return (f"(Segment size {root.size()} "
                f"from ({root.top_r}, {root.top_c}) "
                f"to ({root.bottom_r}, {root.bottom_c}))")
