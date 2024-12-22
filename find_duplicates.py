import numpy

from utils import SegmentUnionFind


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

    # Initialization: segment_matrix has the same shape is matrix, but is either
    # full of 0's or SegmentUnionFind objects. segments is a list or set
    # containing those same objects.
    segment_matrix = numpy.zeros((nr, nc), dtype=numpy.object_)
    segments = []
    for r in range(nr):
        for c in range(nc):
            if r == c and is_single_file:
                continue  # Skip pixels on the main diagonal
            if matrix[r, c] != 0:
                new_segment = SegmentUnionFind(r, c)
                segment_matrix[r, c] = new_segment
                segments.append(new_segment)

    while segments:  # While we still have segments left
        # The maximum distance to look over is the smallest distance that is as
        # far as any segment can reach. That way, small segments near each
        # other get to grow without a large, far-away segment inserting itself,
        # and we don't waste time looking at too-small a distance that needs to
        # be repeated later.
        max_distance = min(segment.size() for segment in segments)

        if max_distance > _MAX_TOKEN_CHAIN:
            # All remaining segments are so long that they'll already get the
            # most extreme color. Don't bother merging further.
            break

        segments_to_consider_again = []
        for current in segments:
            current = current.get_root()
            to_merge = find_mergeable_segment(
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


def find_mergeable_segment(current, segment_matrix, max_distance=None):
    """
    current is a SegmentUnionFind, and segment_matrix is a 2D array of such
    objects. We return the largest SegmentUnionFind we can merge with current,
    or None if none are available.

    Two segments are mergeable if the Manhattan distance between them is smaller
    than both their sizes.
    """
    if max_distance is None:
        max_distance = current.size()
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
        for j in range(max_distance):
            cand_r = r + i + 1
            cand_c = c + j + 1
            if cand_r >= nr or cand_c >= nc:
                # We're out-of-bounds, so skip looking further in this row, and
                # go on to the next row.
                break
            candidate = segment_matrix[cand_r, cand_c]
            if candidate == 0:
                continue
            candidate = candidate.get_root()
            cand_end_r, cand_end_c = candidate.top
            # The 2 is the distance from an endpoint to the closest place to
            # search (a diagonal step away).
            dist = abs(r - cand_end_r) + abs(c - cand_end_c) - 2
            if any(dist > x for x in
                   (max_distance, candidate.size(), current.size())):
                continue
            update_candidate(candidate)
    return best_candidate


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
