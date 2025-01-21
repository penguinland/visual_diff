import numpy
from typing import Iterable, Optional, Self


# Sequences at least this long get the most extreme hue
_MAX_TOKEN_CHAIN: int = 100


_Coordinates = tuple[int, int]  # Syntactic sugar


class _SegmentUnionFind:
    """
    UnionFind is sometimes named DisjointSet. Our data structure is different
    from the usual one because it represents a set of duplicated tokens, with a
    top-right and bottom-left coordinate, in addition to the size.
    """
    # Save memory by telling Python exactly what fields we use, which means the
    # Python interpreter doesn't allocate a dict for all the extra fields we
    # might add later. This reduces the memory usage of _SegmentUnionFind by
    # roughly two thirds.
    __slots__ = ("_size", "_root", "top", "bottom")

    def __init__(self, r: int, c: int, size: int):
        """
        The arguments passed in are the coordinates of the top-left pixel, and
        the number of pixels on a straight diagonal line to the end of this
        segment. We do this to avoid allocating a bunch of 1-pixel segments
        that are either never going to be used or about to be joined with their
        immediate diagonals.
        """
        self._size = size
        self._root: Optional[Self] = None
        self.top = (r, c)
        self.bottom = (r + size - 1, c + size - 1)

    def get_root(self) -> Self:
        if self._root is None:
            return self

        self._root = self._root.get_root()
        return self._root

    def size(self) -> int:
        return self.get_root()._size

    def merge(self, other: Self) -> None:
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

    def __str__(self) -> str:  # Used solely for debugging
        root = self.get_root()
        return f"(Segment size {root.size()} from {root.top} to {root.bottom})"


def _initialize_segments(
    matrix: numpy.ndarray, is_single_file: bool
) -> tuple[list[_SegmentUnionFind], dict[_Coordinates, _SegmentUnionFind]]:
    """
    Returns a tuple of (segments, pixel_to_segment). These are a list of
    _SegmentUnionFinds and a dict mapping pixel coordinates to the
    _SegmentUnionFinds they make up (same ones as in the list). Each
    _SegmentUnionFind has size at least 2: these have already merged as many
    immediate-diagonal neighbors as possible.
    """
    nr, nc = matrix.shape

    segments = []
    pixel_to_segment = {}
    for r in range(nr):
        for c in range(nc):
            if matrix[r, c] == 0:
                continue
            # An optimization: lone pixels that don't have anything immediately
            # diagonal from them can never grow. So, as we initialize things,
            # grow each segment as long as it can be with a straight diagonal,
            # and don't bother initializing anything of size 1.
            if (r, c) in pixel_to_segment:
                continue  # Already added as part of a contiguous segment.
            if r == c and is_single_file:
                continue  # Skip pixels on the main diagonal

            # See whether this segment is more than just a dot.
            size = 1
            while (r + size < nr and c + size < nc and
                   matrix[r + size, c + size] != 0):
                size += 1

            if size == 1:  # Trivial segment: don't bother
                continue
            # Otherwise, we've found a nontrivial segment. Add it in!
            new_segment = _SegmentUnionFind(r, c, size)
            segments.append(new_segment)
            for i in range(size):
                pixel_to_segment[(r + i, c + i)] = new_segment
    return segments, pixel_to_segment


def _get_pixel_to_segment(
    matrix: numpy.ndarray, is_single_file: bool
) -> dict[_Coordinates, _SegmentUnionFind]:
    """
    matrix is a 2D numpy array of uint8s. is_single_file is a boolean. We return
    a map from (row, col) pairs to _SegmentUnionFinds for each pixel set in the
    original matrix. If is_single_file is set, we do not include pixels on the
    main diagonal, because a file shouldn't count as a duplicate of itself.
    """
    segments: Iterable[_SegmentUnionFind]
    segments, pixel_to_segment = _initialize_segments(matrix, is_single_file)
    while segments:
        # To prevent flaky tests, we need to be deterministic, which means we
        # need to sort the segments. Try merging the largest ones first, and
        # among ties, go for the ones closest to the top-left corner first. If
        # there are still ties, just pick some arbitrary order.
        def key(
            segment: _SegmentUnionFind
        ) -> tuple[int, int, int, int, int, int]:
            root = segment.get_root()
            return (-root.size(), sum(root.top), *root.top, *root.bottom)
        segments = sorted(segments, key=key)

        # The maximum distance to look over is the smallest distance that is as
        # far as any segment can reach. That way, small segments near each
        # other get to grow without a large, far-away segment inserting itself,
        # but we don't waste time looking at too small a distance that needs to
        # be repeated later.
        max_distance = min(segment.size() for segment in segments)
        # Keep track of segments whose size is larger than max_distance and thus
        # might be able to merge over larger distances next time.
        larger_segments = []

        for current in segments:
            current = current.get_root()

            to_merge = _find_mergeable_segment(
                    current, pixel_to_segment, max_distance, matrix.shape)
            if to_merge is not None:
                current.merge(to_merge)

            if current.size() > max_distance:
                larger_segments.append(current)

        # larger_segments might contain segments that were subsequently joined
        # together. Remove duplicates before merging again.
        segments = set(segment.get_root() for segment in larger_segments)
    return pixel_to_segment


def get_lengths(matrix: numpy.ndarray, is_single_file: bool) -> numpy.ndarray:
    """
    matrix is a 2D numpy array of uint8s. We return a 2D numpy array of uint32s,
    which are a measure of how long a chain of nonzero values from the original
    matrix is.

    If is_single_file is set, the main diagonal will be all 1's, because a file
    shouldn't count as a duplicate of itself.
    """
    pixel_to_segment = _get_pixel_to_segment(matrix, is_single_file)
    # For every pixel not involved in a segment, its score is 0 if it was not
    # set in the original, and 1 if it was (it's either a lone pixel or it's on
    # the main diagonal of a file compared to itself).
    image = (matrix != 0).astype(numpy.uint32)
    for (r, c), segment in pixel_to_segment.items():
        image[r, c] = segment.size()
    return image


def get_segments(
    matrix: numpy.ndarray, is_single_file: bool
) -> set[_SegmentUnionFind]:
    """
    matrix is a 2D numpy array of uint8s. We return set of _SegmentUnionFinds
    describing all the segments we found in the matrix.

    If is_single_file is set, the main diagonal cannot be joined into a segment,
    because a file shouldn't count as a duplicate of itself.
    """
    pixel_to_segment = _get_pixel_to_segment(matrix, is_single_file)
    # Collect all the segments and remove duplicates.
    segments = set(segment.get_root() for segment in pixel_to_segment.values())
    return segments


def _find_mergeable_segment(
    current: _SegmentUnionFind,
    pixel_to_segment: dict[_Coordinates, _SegmentUnionFind],
    max_distance: int,
    shape: tuple[int, ...],
) -> Optional[_SegmentUnionFind]:
    """
    current is a _SegmentUnionFind, and pixel_to_segment is a dict mapping pixel
    coordinates to _SegmentUnionFind objects. We return the largest
    _SegmentUnionFind below-right of current that we can merge with, or None if
    none are available. We only look at most max_distance away from the location
    diagonal from current's bottom-right corner (using the Manhattan distance).

    Two segments are mergeable if the Manhattan distance between the
    bottom-right end of one and the top-left end of the other is at most 2 more
    than each of their sizes (the purpose of the 2 being that two segments
    immediately diagonal from each other should be considered a distance 0
    apart).
    """
    nr, nc = shape

    best_candidate = None
    best_candidate_size = -1
    def update_candidate(candidate: _SegmentUnionFind) -> None:
        nonlocal best_candidate, best_candidate_size
        if candidate.size() > best_candidate_size:
            best_candidate = candidate
            best_candidate_size = candidate.size()

    r, c = current.bottom
    for i in range(max_distance):
        candidate_r = r + 1 + i
        if candidate_r >= nr:
            # We're out-of-bounds, and any row beyond this is also out of
            # bounds. Give up already.
            break

        for j in range(max_distance - i):
            candidate_c = c + 1 + j
            if candidate_c >= nc:
                # We're out-of-bounds, so skip looking further in this row, and
                # go on to the next row.
                break

            candidate = pixel_to_segment.get((candidate_r, candidate_c))
            if candidate is None:  # No segment in this location
                continue
            candidate = candidate.get_root()

            cand_end_r, cand_end_c = candidate.top
            dist = abs(r + 1 - cand_end_r) + abs(c + 1 - cand_end_c)
            # We want both segments' size to be at least as large as the
            # distance between them. To even call this function, current's size
            # is at least max_distance, so we don't need to check that again.
            if dist <= candidate.size():
                update_candidate(candidate)
    # We've now explored every possible cell at most max_distance below current.
    return best_candidate


def get_hues(matrix: numpy.ndarray, is_single_file: bool) -> numpy.ndarray:
    scores = get_lengths(matrix, is_single_file)
    # Cut everything off at the max, then divide by the max to put all values
    # between 0 and 1.
    scores = numpy.minimum(_MAX_TOKEN_CHAIN, scores.astype(numpy.float32))
    scores /= _MAX_TOKEN_CHAIN
    # Get the hues to go from blue (lowest score) up to red (highest). Red has
    # hue 0, while blue is roughly 170.
    scores = 1 - scores
    scores *= 170
    scores = scores.astype(numpy.uint8)
    return scores
