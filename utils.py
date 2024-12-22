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
    def __init__(self, r, c, index):
        self._size = 1
        self._root = self
        self.top_r = r
        self.top_c = c
        self.bottom_r = r
        self.bottom_c = c
        self.index = index  # Indicates location within a minheap array

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

        large_root.top_r, large_root.top_c = min(
            (small_root.top_r, small_root.top_c),
            (large_root.top_r, large_root.top_c))
        large_root.bottom_r, large_root.bottom_c = max(
            (small_root.bottom_r, small_root.bottom_c),
            (large_root.bottom_r, large_root.bottom_c))

    def __str__(self):
        root = self.get_root()
        return (f"(Segment size {root.size()} "
                f"from ({root.top_r}, {root.top_c}) "
                f"to ({root.bottom_r}, {root.bottom_c}))")



def reheapify(heap, index):
    """
    heap is a list of SegmentUnionFinds that are their own roots, in nearly heap
    order (each element has smaller size than its two children, located at twice
    its index). The "nearly" part is that the item at the given index has grown
    in size, and might need to be pushed further into the (min)heap.
    """
    n = len(heap)
    left_child_index = 2 * index
    right_child_index = left_child_index + 1

    if left_child_index >= n:
        return  # The index is a leaf.

    if right_child_index >= n:  # The right child doesn't exist
        child_index = left_child_index
    else:  # Both children exist. Find the smallest one.
        if heap[left_child_index].size() < heap[right_child_index].size():
            child_index = left_child_index
        else:
            child_index = right_child_index

    if heap[child_index].size() >= heap[index].size():
        return  # We're already still in heap order!

    # Otherwise, swap them and recurse
    heap[index], heap[child_index] = heap[child_index], heap[index]
    heap[index      ].index = index
    heap[child_index].index = child_index
    reheapify(heap, child_index)


def heap_pop(heap):
    """
    heap is a list of SegmentUnionFinds, in heap order. We return the smallest
    item, while keeping the rest of the heap ordered.
    """
    # Swap the smallest value (the one to return) with the very end element.
    heap[0], heap[-1] = heap[-1], heap[0]
    heap[0].index = 0
    minimum = heap.pop()
    reheapify(heap, 0)
    return minimum
