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
    print(f"finished initializing {i} segments")

    while segment_heap:  # While we still have segments left
        current = heap_pop(segment_heap).get_root()
        #print("")
        to_merge = find_mergeable_segment(current, segments)
        #print(f"best we found was {to_merge}")

        if to_merge is not None:
            #print(f"merging {to_merge} with {current}")
            merge_index = to_merge.index
            current.merge(to_merge)
            #print(f"...resulting in {current.get_root()}")
            reheapify(segment_heap, merge_index)

    # Finally, output the final sizes of all the SegmentUnionFinds as the final
    # scores.
    scores = numpy.zeros((nr, nc), dtype=numpy.uint32)
    for r in range(nr):
        for c in range(nc):
            if segments[r, c] != 0:
                scores[r, c] = segments[r, c].size()
            elif r == c and is_single_file:
                # We didn't merge these with anything, but should still count
                # them in the final output.
                scores[r, c] = 1
    return scores


def find_mergeable_segment(current, segments):
    """
    current is a SegmentUnionFind, and segments is a 2D list of such objects.
    We return the largest SegmentUnionFind we can merge with current, or None if
    none are available.

    Two segments are mergeable if the Manhattan distance between them is smaller
    than both their sizes.
    """
    #print(f"top of find_mergeable_segment: {current}")
    size = current.size()

    best_candidate = None
    best_candidate_size = -1
    def update_candidate(candidate):
        nonlocal best_candidate, best_candidate_size
        if candidate.size() > best_candidate_size:
            #print("found better candidate!")
            best_candidate = candidate
            best_candidate_size = candidate.size()

    r, c = current.bottom_r, current.bottom_c
    for i in range(size):
        for j in range(size):
            cand_r = r + i + 1
            cand_c = c + j + 1
            if cand_r >= segments.shape[0] or cand_c >= segments.shape[1]:
                continue
            candidate = segments[cand_r, cand_c]
            if candidate == 0:
                continue
            candidate = candidate.get_root()
            #print(f"considering candidate found at ({cand_r}, {cand_c}): {candidate}")
            cand_end_r = candidate.top_r
            cand_end_c = candidate.top_c
            # The 2 is the distance from an endpoint to the closest place to
            # search (a diagonal step away).
            dist = abs(r - cand_end_r) + abs(c - cand_end_c) - 2
            if dist > size or dist > candidate.size():
                #print("candidate too far away")
                continue
            update_candidate(candidate)

    r, c = current.top_r, current.top_c
    for i in range(size):
        for j in range(size):
            cand_r = r - i - 1
            cand_c = c - j - 1
            if cand_r < 0 or cand_c < 0:
                continue
            candidate = segments[cand_r, cand_c]
            if candidate == 0:
                continue
            candidate = candidate.get_root()
            #print(f"considering candidate found at ({cand_r}, {cand_c}): {candidate}")
            cand_end_r = candidate.bottom_r
            cand_end_c = candidate.bottom_c
            dist = abs(r - cand_end_r) + abs(c - cand_end_c) - 2
            if dist > size or dist > candidate.size():
                #print("candidate too far away")
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
