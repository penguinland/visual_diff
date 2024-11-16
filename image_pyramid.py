import numpy
import PIL.Image
import PIL.ImageTk


class ImagePyramid:
    _ZOOMED_IN_LEVELS = 3  # Number of times you can zoom in beyond 100%
    _MIN_MAP_SIZE = 250  # Pixel length at which to stop zooming out

    def __init__(self, matrix):
        self._pyramid = []  # A list of self._matrix at different zoom levels

        # Start by zooming into the matrix so that each pixel of the original
        # takes up multiple pixels on the screen.
        zoomed_in_matrix = matrix
        for _ in range(self._ZOOMED_IN_LEVELS):
            next_level = numpy.zeros([2 * x for x in zoomed_in_matrix.shape])
            for r in [0, 1]:
                for c in [0, 1]:
                    next_level[r::2, c::2] = zoomed_in_matrix
            self._pyramid.append(next_level)
            zoomed_in_matrix = next_level
        self._pyramid.reverse()  # The most zoomed-in part comes at the base
        self._pyramid.append(matrix)

        # Now, zoom out and make the matrix smaller and smaller
        while max(matrix.shape) > 2 * self._MIN_MAP_SIZE:
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

        # self._zoom_level is the index into self._pyramid to get the current
        # image.
        self._zoom_level = self._ZOOMED_IN_LEVELS  # Start at 100%
        self._max_zoom_level = len(self._pyramid) - 1

    def get_image(self, top_left_x, top_left_y, height, width):
        """
        We return a sub-image, and the indices of the top-left corner.

        The image returned is at the current zoom level, 3 times taller and wider
        than the displayed window. If no data would be included, we return None.
        """
        current_data = self._pyramid[self._zoom_level]
        nr, nc = current_data.shape

        min_x = max(0,  top_left_x -     width)
        min_y = max(0,  top_left_y -     height)
        max_x = min(nc, top_left_x + 2 * width)
        max_y = min(nr, top_left_y + 2 * height)

        submatrix = current_data[min_y:max_y, min_x:max_x]
        if len(submatrix) == 0:
            # We're so far away from the actual data that none of it will fit
            # on or even near the screen. Rather than attempting and failing to
            # display this data, just don't show it in the first place.
            return None, min_x, min_y

        image = PIL.Image.fromarray(submatrix * 255)
        return PIL.ImageTk.PhotoImage(image), min_x, min_y

    def zoom(self, amount):
        """
        Returns whether we successfully changed zoom levels.
        """
        orig_zoom_level = self._zoom_level
        # Note that tkinter doesn't spawn extra threads, so this doesn't have
        # race conditions.
        self._zoom_level += amount
        self._zoom_level = min(self._zoom_level, self._max_zoom_level)
        self._zoom_level = max(self._zoom_level, 0)
        return (self._zoom_level != orig_zoom_level)

    def get_zoom_level(self):
        return self._zoom_level - self._ZOOMED_IN_LEVELS
