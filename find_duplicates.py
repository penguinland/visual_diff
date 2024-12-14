import numpy


def get_lengths(matrix, is_single_file):
    """
    Matrix is a 2D numpy array of bools. We return a 2D numpy array of ints,
    where each int corresponds to one of the bools. The ints are a measure of
    how long a chain of bools is.

    This number is calculated as follows:
    - The number of a False pixel is 0.
    - The "cost" of joining two pixels into a segment is the Manhattan distance
      between the location just below-right of the first pixel and the second
      pixel. For example, two pixels immediately diagonal from each other cost
      nothing to join together, while joining two pixels a knights move apart
      has a cost of 1.
    - The final score of a True pixel is the maximum value of (the number of
      pixels in the group minus the cost of performing all the joins). For
      example, a diagonal run of 10 pixels should each have score 10, whereas
      two diagonals of 5 pixels whose endpoints are separated by a knight's
      move should have a score of 9. A single pixel by itself scores 1.
    """
    nr, nc = matrix.shape
    distance_template = numpy.arange(nr)[:, None] + numpy.arange(nc)
    # For each pixel, we need to keep track of the score it can achieve by
    # joining things further down and right from it, and the row and column of
    # the best such pixel to join it with.
    scores = numpy.zeros((nr, nc), dtype=numpy.uint32)
    next_r = numpy.zeros((nr, nc), dtype=numpy.int32) - 1
    next_c = numpy.zeros((nr, nc), dtype=numpy.int32) - 1

    # Initialize the bottommost and rightmost edges to be the initial scores:
    # they cannot grow further down or right.
    scores[-1, :] = numpy.astype(matrix[-1, :], numpy.uint32)
    scores[:, -1] = numpy.astype(matrix[:, -1], numpy.uint32)

    # Then, walk the rest of matrix from bottom-right to top-left, with each
    # pixel growing as large as it can solely by joining things further right
    # and down from itself.
    for r in range(nr - 2, -1, -1):
        for c in range(nc - 2, -1, -1):
            if matrix[r, c] == 0:  # Pixel is unset, so it should score 0.
                continue
            # Otherwise, it should be at least 1.
            scores[r, c] = 1

            if is_single_file and r == c:
                # A token compared to itself matches but shouldn't be
                # considered an interesting group.
                continue

            candidates = scores[r+1:, c+1:]
            distances = distance_template[:(nr - r - 1), :(nc - c - 1)]
            possible_scores = candidates - distances
            best_r, best_c = numpy.unravel_index(
                    numpy.argmax(possible_scores), candidates.shape)
            best_score = possible_scores[best_r, best_c]
            if best_score > 0:
                scores[r, c] += best_score
                next_r[r, c] = best_r + r + 1
                next_c[r, c] = best_c + c + 1

    # Now, do the opposite: moving top-left to bottom-right, set the scores of
    # all pixels to be as large as we could find.
    for i in range(nr):
        has_update = numpy.logical_and(numpy.greater_equal(next_r[i, :], 0),
                                       numpy.greater_equal(next_c[i, :], 0))
        rs = next_r[i,:][has_update]
        cs = next_c[i,:][has_update]
        ss = scores[i,:][has_update]
        scores[rs, cs] = numpy.maximum(scores[rs, cs], ss)

    return scores
