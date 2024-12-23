import collections
import colorsys
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


def to_rgb_matrix(matrix, hues):
    def pixel_hsv_to_rgb(hsv):
        hsv_floats = hsv.astype(numpy.float64) / 255
        rgb_floats = colorsys.hsv_to_rgb(*hsv_floats)
        return numpy.array([x * 255 for x in rgb_floats], numpy.uint8)

    pixel_matrix = to_hsv_matrix(matrix, hues)
    nr, nc, _ = pixel_matrix.shape
    for r in range(nr):
        for c in range(nc):
            pixel_matrix[r, c, :] = pixel_hsv_to_rgb(pixel_matrix[r, c, :])
    return pixel_matrix
