import numpy

from utils import SegmentUnionFind, reheapify, heap_pop


_MAX_TOKEN_CHAIN = 100  # Sequences at least this long get the most extreme hue


def get_lengths(matrix, is_single_file):
    """
    Matrix is a 2D numpy array of bools. We return a 2D numpy array of ints,
    where each int corresponds to one of the bools. The ints are a measure of
    how long a chain of bools is.

    If is_single_file is set, the main diagonal of the scores are all 1's,
    because a file shouldn't count as a duplicate of itself.
    """
    nr, nc = matrix.shape
    distance_template = numpy.square(numpy.arange(nr)[:, None] +
                                     numpy.arange(nc))

    # Initialization: segments has the same shape is matrix, but is either full
    # of Nonetype or SegmentUnionFind objects. segment_heap is a minheap
    # containing those same objects.
    segments = numpy.zeros((nr, nc), dtype=numpy.object_)
    i = 0
    segment_heap = []
    for r in range(nr):
        for c in range(nc):
            if r == c and is_single_file:
                continue  # Skip pixels on the main diagonal
            if matrix[r, c] != 0:
                segments[r, c] = SegmentUnionFind(r, c, i)
                segment_heap.append(segments[r, c])
                i += 1

    while segment_heap:  # While we still have segments left
        current = heap_pop(segment_heap)
        to_merge = find_mergeable_segment(current, segments)
        if to_merge is not None:
            merge_index = to_merge.index
            current.merge(to_merge)
            reheapify(segment_heap, merge_index)

    # Finally, output the final sizes of all the SegmentUnionFinds as the final
    # scores.
    scores = numpy.zeros((nr, nc), dtype=numpy.uint32)
    for r in range(nr):
        for c in range(nc):
            if segments[r, c] is not None:
                scores[r, c] = segments[r, c].size()
            elif r == c and is_single_file:
                # We didn't merge these with anything, but should still count
                # them in the final output.
                scores[r, c] = 1
    return scores


def get_hues(matrix, is_single_file):
    scores = get_lengths(matrix, is_single_file)
    # Cut everything off at the max, then divide by the max to put all values
    # between 0 and 1.
    scores = numpy.minimum(
        _MAX_TOKEN_CHAIN, numpy.astype(scores, numpy.float32))
    scores /= _MAX_TOKEN_CHAIN
    # Get the hues to go from blue (lowest score) up to red (highest). Red has
    # hue 0, while blue is roughly 170.
    scores = 1 - scores
    scores *= 170
    scores = numpy.astype(scores, numpy.uint8)
    return scores
