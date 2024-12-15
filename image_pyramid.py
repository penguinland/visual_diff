import numpy


class ImagePyramid:
    _ZOOMED_IN_LEVELS = 3  # Number of times you can zoom in beyond 100%
    _MAX_TOKEN_CHAIN = 100

    def __init__(self, matrix, sidelength, scores=None):
        self._pyramid = []  # A list of `matrix` at different zoom levels
        self._pyramid.append(matrix)
        self._sidelength = sidelength

        if scores is None:
            self._score_pyramid = None
        else:
            normalized_scores = (
                numpy.astype(scores, numpy.float32) / self._MAX_TOKEN_CHAIN)
            normalized_scores = numpy.maximum(1, normalized_scores)
            self._score_pyramid = []
            self._score_pyramid.append(normalized_scores)

        # Zoom out and make the matrix smaller and smaller
        while max(matrix.shape) >= sidelength:
            # Combine 2x2 squares of pixels to make the next level.
            nr, nc = [(value // 2) * 2 for value in matrix.shape]
            quads = [matrix[row:nr:2, col:nc:2]
                     for row in [0, 1] for col in [0, 1]]
            # TODO: Is there a standard way of resizing a binary image that
            # keeps lines crisp while removing salt-and-pepper noise?

            # We want the following outcomes when combining a 2x2 square into a
            # single pixel:
            #   - If none of the 4 pixels is set, we should not be set.
            #   - If 1 of the 4 pixels is set, we're set a quarter of the time.
            #   - If 2 of the 4 pixels are set, we're set half the time.
            #   - It's impossible to have 3 of the 4 pixels set.
            #   - If all 4 pixels are set, this one should be set, too.
            # To discuss the times when half the pixels are set:
            #   - If the two that are set are on the main diagonal, we should be
            #     set. It's good to make diagonals easy to see.
            #   - If the two that are set are off the main diagonal, we should
            #     not be set.
            #   - If the two that are set are adjacent to each other, we should
            #     be set half the time.
            # To discuss times when 1 pixel is set:
            #   - If the 1 pixel is off the diagonal, it might be part of a
            #     large diagonal line shifted 1 pixel off of our diagonal. Half
            #     of these should be set.
            #   - If the 1 pixel is on the diagonal, we should not be set (so
            #     that we're set a quarter of the time overall).
            # To satisfy all these conditions, we should be set either if both
            # pixels on the diagonal are set or if 1 pixel off the diagonal is
            # set.
            matrix = ((quads[0] & quads[3]) |
                      (quads[1] & numpy.logical_not(quads[2])))
            self._pyramid.append(matrix)

            if scores is not None:
                # Do the same thing with the scores, except use the max value.
                score_quads = [normalized_scores[row:nr:2, col:nc:2]
                               for row in [0, 1] for col in [0, 1]]
                normalized_scores = numpy.maximum(
                    numpy.maximum(score_quads[0], score_quads[1]),
                    numpy.maximum(score_quads[2], score_quads[3]))
                self._score_pyramid.append(normalized_scores)

        # self._zoom_level is the index into self._pyramid to get the current
        # image.
        self._zoom_level = 0  # Start at 100%
        self._max_zoom_level = len(self._pyramid) - 1

    def get_submatrix(self, top_left_x, top_left_y):
        """
        Given the top left corner of a window, we return a matrix containing
        the relevant sub-image, and the indices of the top-left corner.

        The image returned is at the current zoom level, 3 times taller and
        wider than the displayed window, so that the center of the window is
        the center of the image.
        """
        zoom_level = self._zoom_level
        scale = max(0, -zoom_level)
        current_data = self._pyramid[max(0, zoom_level)]
        nr, nc = current_data.shape
        nr <<= scale
        nc <<= scale

        min_x = max(0,  top_left_x -     self._sidelength)
        min_y = max(0,  top_left_y -     self._sidelength)
        max_x = min(nc, top_left_x + 2 * self._sidelength)
        max_y = min(nr, top_left_y + 2 * self._sidelength)

        if zoom_level >= 0:
            # No need to do anything special: just return the relevant data
            submatrix = current_data[min_y:max_y, min_x:max_x]
            image = numpy.zeros(
                [submatrix.shape[0], submatrix.shape[1], 3], numpy.uint8)
            image[:, :, 2] = submatrix * 255
            return image, min_x, min_y

        # Otherwise, we're zoomed in more than 100%. Grab the data we want,
        # then duplicate it a bunch.

        # First, scale all the coordinates to the actual data size.
        min_x >>= scale
        min_y >>= scale
        max_x >>= scale
        max_y >>= scale
        # Avoid roundoff errors: make the truncated edges 1 pixel wider before
        # expanding, and if it's a few pixels larger than expected, no one
        # will notice.
        max_x += 1
        max_y += 1

        submatrix = current_data[min_y:max_y, min_x:max_x]

        # Now, duplicate the data until it's grown to the right size.
        for _ in range(-zoom_level):
            new_submatrix = numpy.zeros([2 * x for x in submatrix.shape])
            for r in [0, 1]:
                for c in [0, 1]:
                    new_submatrix[r::2, c::2] = submatrix
            submatrix = new_submatrix

        image = numpy.zeros(
            [submatrix.shape[0], submatrix.shape[1], 3], numpy.uint8)
        image[:, :, 2] = submatrix * 255
        return image, min_x << scale, min_y << scale

    def zoom(self, amount):
        """
        Returns whether we successfully changed zoom levels.
        """
        orig_zoom_level = self._zoom_level
        # Note that tkinter doesn't spawn extra threads, so this doesn't have
        # race conditions.
        self._zoom_level += amount
        self._zoom_level = min(self._zoom_level, self._max_zoom_level)
        self._zoom_level = max(self._zoom_level, -self._ZOOMED_IN_LEVELS)
        return (self._zoom_level != orig_zoom_level)

    def get_zoom_level(self):
        return self._zoom_level
