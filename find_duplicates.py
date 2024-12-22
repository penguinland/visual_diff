import numpy


_MAX_TOKEN_CHAIN = 100  # Sequences at least this long get the most extreme hue


class _SegmentUnionFind:
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

    def __str__(self):  # Used solely for debugging
        root = self.get_root()
        return (f"(Segment size {root.size()} "
                f"from ({root.top_r}, {root.top_c}) "
                f"to ({root.bottom_r}, {root.bottom_c}))")


def _get_lengths(matrix, is_single_file):
    """
    Matrix is a 2D numpy array of unit8s. We return a 2D numpy array of uint32s,
    which are a measure of how long a chain of nonzero values from the original
    matrix is.

    If is_single_file is set, the main diagonal will be all 1's, because a file
    shouldn't count as a duplicate of itself.
    """
    nr, nc = matrix.shape

    # Initialization: segment_matrix has the same shape as matrix, but is either
    # full of 0's or _SegmentUnionFind objects. segments will be a list (or
    # later a set) containing those same objects.
    segment_matrix = numpy.zeros((nr, nc), dtype=numpy.object_)
    segments = []
    for r in range(nr):
        for c in range(nc):
            if r == c and is_single_file:
                continue  # Skip pixels on the main diagonal
            if matrix[r, c] != 0:
                new_segment = _SegmentUnionFind(r, c)
                segment_matrix[r, c] = new_segment
                segments.append(new_segment)

    while segments:
        # The maximum distance to look over is the smallest distance that is as
        # far as any segment can reach. That way, small segments near each
        # other get to grow without a large, far-away segment inserting itself,
        # but we don't waste time looking at too small a distance that needs to
        # be repeated later.
        max_distance = min(segment.size() for segment in segments)

        segments_to_consider_again = []
        for current in segments:
            current = current.get_root()

            to_merge = _find_mergeable_segment(
                    current, segment_matrix, max_distance)
            if to_merge is not None:
                current.merge(to_merge)

            if current.size() > max_distance:
                segments_to_consider_again.append(current)

        # We might have added segments that were later joined together. Remove
        # duplicates before joining again.
        segments = set()
        for segment in segments_to_consider_again:
            segments.add(segment.get_root())

    # Finally, output the final sizes of all the SegmentUnionFinds as the final
    # scores.
    scores = numpy.zeros((nr, nc), dtype=numpy.uint32)
    for r in range(nr):
        for c in range(nc):
            if segment_matrix[r, c] != 0:
                scores[r, c] = segment_matrix[r, c].size()
            elif r == c and is_single_file:
                # We didn't merge these with anything, but should still count
                # them in the final output.
                scores[r, c] = 1
    return scores


def _find_mergeable_segment(current, segment_matrix, max_distance):
    """
    current is a _SegmentUnionFind, and segment_matrix is a 2D array of such
    objects. We return the largest _SegmentUnionFind below-right of current that
    we can merge with, or None if none are available. We only look at most
    max_distance away from the location diagonal from current's bottom-right
    corner (using the Manhattan distance).

    Two segments are mergeable if the Manhattan distance between the
    bottom-right end of one and the top-left end of the other is at most 2 more
    than both their sizes (the purpose of the 2 being that two segments
    immediately diagonal from each other should be considered a distance 0
    apart).
    """
    nr, nc = segment_matrix.shape

    best_candidate = None
    best_candidate_size = -1
    def update_candidate(candidate):
        nonlocal best_candidate, best_candidate_size
        if candidate.size() > best_candidate_size:
            best_candidate = candidate
            best_candidate_size = candidate.size()

    r, c = current.bottom
    for i in range(max_distance):
        for j in range(max_distance - i):
            cand_r = r + 1 + i
            cand_c = c + 1 + j
            if cand_r >= nr or cand_c >= nc:
                # We're out-of-bounds, so skip looking further in this row, and
                # go on to the next row.
                break
            candidate = segment_matrix[cand_r, cand_c]
            if candidate == 0:
                continue
            candidate = candidate.get_root()

            cand_end_r, cand_end_c = candidate.top
            dist = abs(r + 1 - cand_end_r) + abs(c + 1 - cand_end_c)
            if dist > candidate.size() or dist > current.size():
                continue
            update_candidate(candidate)
    return best_candidate


def get_hues(matrix, is_single_file):
    scores = _get_lengths(matrix, is_single_file)
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
