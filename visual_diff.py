#!/usr/bin/env python3

import argparse
import code_tokenize
import numpy
import PIL.Image
import sys

import find_duplicates
import utils

try:
    # To get the GUI to work, you'll need to be able to install the TK bindings
    # for PIL (in Ubuntu, it's the python3-pil.imagetk package). We put this in
    # a try block so that the non-GUI functionality will still work even if you
    # can't install this.
    import gui
    can_use_gui = True
except ImportError:
    can_use_gui = False


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename_a", help="File to analyze")
    parser.add_argument("filename_b", nargs="?", help="Second file to analyze")
    parser.add_argument("--output_location", "-o",
                        help="Save an image to this location and exit")
    parser.add_argument("--big_file", "-b", action="store_true",
                        help="Save the image even if the file is big")
    parser.add_argument("--language", "-l", default=None,
                        help="Language of code in files")
    parser.add_argument("--map_width", "-mw", type=int, default=600,
                        help="map width/height, in pixels")
    parser.add_argument("--text_width", "-tw", type=int,
                        help="Expected maximum line width, in characters")
    parser.add_argument("--color", "-c", action="store_true",
                        help="Color based on the amount of duplication")
    return parser.parse_args(sys.argv[1:])


def get_tokens(file_contents, language):
    """
    We return a utils.FileInfo object containing details of the given
    file_contents.
    """
    toks = code_tokenize.tokenize(file_contents, lang=language)
    toks = [t for t in toks if t.type not in ("newline", "comment")]
    lines = list(file_contents.split("\n"))
    constant_types = ("string", "integer", "float", "indent", "dedent")
    token_array = numpy.array(
        [tok.type if tok.type in constant_types else tok.text for tok in toks])

    boundaries = []
    for i, t in enumerate(toks):
        try:
            # Most tokens contain their start and end values. However, the
            # tokenizer we use starts counting lines at 0, and we need to
            # start counting at 1. So, add 1 to all line indices.
            start = t.ast_node.start_point
            end = t.ast_node.end_point
            boundaries.append(((start[0] + 1, start[1]), (end[0] + 1, end[1])))
        except AttributeError:
            if t.type == "indent":
                # When we add indentation, it's on the same line as the next
                # token. Pretend it starts at the beginning of the line and
                # ends just before the start of the next token.
                assert(t.new_line_before)
                next_t = toks[i+1]
                line = next_t.ast_node.start_point[0] + 1
                boundaries.append(
                    ((line, 0), (line, next_t.ast_node.start_point[1])))
            elif t.type == "dedent":
                # We might be the very last token. Look backwards to the last
                # non-dedent token: we're on the line after that. If there are
                # non-dedent tokens after us, we can find our end column by
                # looking at that token's start column, but if we're the end of
                # the file, just make our width 0.
                di = 0
                prev_t = t
                while prev_t.type == "dedent":
                    di -= 1
                    prev_t = toks[i + di]
                # Grab the line of the last non-dedent token, then add 1 to get
                # our line. The parser starts counting at line 0, but we start
                # at line 1, so add another 1 to match.
                line = prev_t.ast_node.end_point[0] + 2
                # If there are other non-dedent tokens after us, we can use
                # their starting column as our ending column.
                next_i = i
                while next_i < len(toks) and toks[next_i].type == "dedent":
                    next_i += 1
                if next_i == len(toks):  # No following tokens: we hit EOF
                    end_column = 0
                else:  # We found a non-dedent token: we stop where it starts
                    end_column = toks[next_i].ast_node.start_point[1]
                boundaries.append(((line, 0), (line, end_column)))
            else:
                print("UNEXPECTED TOKEN!", i, t, type(t), dir(t))
                raise

    return utils.FileInfo(token_array, lines, boundaries)


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


def get_text_width(args):
    if args.text_width is not None:
        return args.text_width
    if args.language == "python" or args.filename_a.split(".")[-1] == "py":
        return 80
    return 100


def make_matrix(tokens_a, tokens_b):
    matrix = numpy.zeros([len(tokens_a), len(tokens_b)], dtype=numpy.uint8)
    for i, value in enumerate(tokens_a):
        matrix[i, :] = (tokens_b == value)
    return matrix


if __name__ == "__main__":
    args = parse_args()
    language = args.language
    if language is None:
        language = guess_language(args.filename_a)

    with open(args.filename_a) as f_a:
        data_a = get_tokens(f_a.read(), language)
    # TODO: it might be cool to allow comparisons across languages.
    with open(args.filename_b or args.filename_a) as f_b:
        data_b = get_tokens(f_b.read(), language)
    print(f"Comparing a file with {len(data_a.tokens)} tokens to "
          f"one that has {len(data_b.tokens)}: final image has "
          f"{len(data_a.tokens) * len(data_b.tokens)} pixels.")
    matrix = make_matrix(data_a.tokens, data_b.tokens)

    if args.color:
        hues = find_duplicates.get_hues(matrix, args.filename_b is None)
    else:
        hues = None

    if args.output_location is None:
        if can_use_gui:
            text_width = get_text_width(args)
            gui.launch(matrix, hues, data_a, data_b, args.map_width, text_width)
        else:
            print("ERROR: Cannot load GUI. Try doing a `sudo apt-get install "
                  "python3-pil.imagetk`. If that doesn't help, open a python3 "
                  "shell, `import gui`, and see what's going wrong.")
            sys.exit(1)
    else:
        pixel_count = len(data_a.tokens) * len(data_b.tokens)
        if pixel_count > 10 * 1000 * 1000 and not args.big_file:
            print("WARNING: the image is over 10 megapixels. Saving very large "
                  "images can use so many resources that your computer "
                  "will freeze. To perform this action anyway, use the "
                  "--big_file flag.")
            sys.exit(2)

        # Otherwise, all is well.
        image = utils.to_hsv_matrix(matrix, hues)
        pil_image = PIL.Image.fromarray(image, mode="HSV")
        pil_image.convert(mode="RGB").save(args.output_location)
