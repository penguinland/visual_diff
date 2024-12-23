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

    hsv_matrix = to_hsv_matrix(matrix, hues)
    rgb_matrix = numpy.zeros(hsv_matrix.shape, numpy.uint8)
    nr, nc, _ = hsv_matrix.shape
    for r in range(nr):
        for c in range(nc):
            rgb_matrix[r, c, :] = pixel_hsv_to_rgb(hsv_matrix[r, c, :])

    return rgb_matrix

matrix = numpy.array([[1, 1], [1, 0]], dtype=numpy.uint8)
hues = numpy.array([[0, 170], [45, 170]], dtype=numpy.uint32)
rgb = to_rgb_matrix(matrix, hues)
bw = to_rgb_matrix(matrix, None)

print(matrix)
print(hues)
print(rgb)
print(bw)
print(rgb[1, 0, :])
