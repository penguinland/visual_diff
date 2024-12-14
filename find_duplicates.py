import numpy


def get_lengths(matrix, is_single_file):
    """
    Matrix is a 2D numpy array of bools. We return a 2D numpy array of ints,
    where each int corresponds to one of the bools. The ints are a measure of
    how long a chain of bools is.

    This number is calculated as follows:
    - The number of a False pixel is -1.
    - A pixel not joined to anything else has a score of 1.
    - Pixels can only be joined in a down-and-to-the-right fashion.
    - The "cost" of joining two pixels into a segment is the Manhattan distance
      between the location just below-right of the first pixel and the second
      pixel. For example, two pixels immediately diagonal from each other cost
      nothing to join together, while joining two pixels a knights move apart
      has a cost of 1.
    - The number of a True pixel is the maximum value of the number of pixels
      it can join with minus the cost of performing all the joins. For example,
      a diagonal run of 10 pixels should each have value 10, whereas two
      diagonals of 5 pixels each whose endpoints are separated by a knight's
      move should have a value of 9.
    """
    r, c = matrix.shape
    distance_template = numpy.arange(r)[:, None] + numpy.arange(c)
    # For each pixel, we need to keep track of the score it can achieve by
    # joining things further down and right from it, and the row and column of
    # the best such pixel to join it with.
    scores = numpy.zeros((r, c), dtype=numpy.int32) - 1
    next_r = numpy.zeros((r, c), dtype=numpy.int32) - 1
    next_c = numpy.zeros((r, c), dtype=numpy.int32) - 1

    # Initialize the bottommost and rightmost edges to be the initial scores:
    # they cannot grow further down or right.
    scores[-1, :] = 2 * numpy.astype(matrix[-1, :], numpy.int32) - 1
    scores[:, -1] = 2 * numpy.astype(matrix[:, -1], numpy.int32) - 1

    # Then, walk the rest of matrix from bottom-right to top-left, with each
    # pixel growing as large as it can solely by joining things further right
    # and down from itself.
    for i in range(r - 2, -1, -1):
        for j in range(c - 2, -1, -1):
            if matrix[i, j] == 0:  # Pixel is unset, so it should score -1.
                continue
            # Otherwise, it should be at least 1.
            scores[i, j] = 1

            if is_single_file and i == j:
                # A token compared to itself matches but shouldn't be
                # considered an interesting group.
                continue

            candidates = scores[i+1:, j+1:]
            distances = distance_template[:(r - i - 1), :(c - j - 1)]
            possible_scores = candidates - distances
            best_r, best_c = numpy.unravel_index(
                    numpy.argmax(possible_scores), candidates.shape)
            best_score = possible_scores[best_r, best_c]
            if best_score > 0:
                scores[i, j] += best_score
                next_r[i, j] = best_r + i + 1
                next_c[i, j] = best_c + j + 1

    # Now, do the opposite: moving top-left to bottom-right, set the scores of
    # all pixels to be as large as we could find.
    for i in range(r):
        for j in range(c):
            nr = next_r[i, j]
            nc = next_c[i, j]
            if nr < 0 or nc < 0:
                continue
            scores[nr, nc] = max(scores[i, j], scores[nr, nc])

    return scores
