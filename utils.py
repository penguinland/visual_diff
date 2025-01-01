import numpy


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


def make_matrix(tokens_a, tokens_b):
    matrix = numpy.zeros([len(tokens_a), len(tokens_b)], dtype=numpy.uint8)
    for i, value in enumerate(tokens_a):
        matrix[i, :] = (tokens_b == value)
    return matrix


def guess_language(filename):
    file_type = filename.split(".")[-1]
    known_types = {  # Sorted by language (sorted by value, not key!)
        "c":      "c",
        "h":      "cpp",  # Might be C or C++, err on the side of caution
        "cc":     "cpp",
        "hh":     "cpp",
        "cpp":    "cpp",
        "hpp":    "cpp",
        "go":     "go",
        "js":     "javascript",
        "py":     "python",
        "svelte": "svelte",
        "ts":     "typescript",
        }
    expected_language = known_types.get(file_type)
    if expected_language is not None:
        return expected_language
    raise ValueError(f"Cannot infer language for unknown file extension "
                     f"'.{file_type}'. Set language explicitly")
