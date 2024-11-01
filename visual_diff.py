#!/usr/bin/env python3

import argparse
import code_tokenize
import numpy
import sys

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
    parser.add_argument("--gui", "-g", action="store_true",
                        help="Explore the results in a GUI")
    parser.add_argument("--output_location", "-o", default="output.png",
                        help="Location of output image (default: output.png)")
    parser.add_argument("--big_file", "-b", action="store_true",
                        help="Save the image even if the file is big")
    parser.add_argument("--language", "-l", default="python",
                        help="Language of code in files")
    return parser.parse_args(sys.argv[1:])


def get_tokens(filename, language):
    """
    We return a tuple of (tokens, lines, boundaries) where
    - tokens is a list of tokens from the file
    - lines is a list of strings containing the file text
    - boundaries is a list of ((start_row, start_col), (end_row, end_col)) tuples for each token
    """
    with open(filename) as f:
        contents = f.read()
    toks = code_tokenize.tokenize(contents, lang=language)
    toks = [t for t in toks if t.type not in ("newline", "comment")]
    lines = [line.rstrip() for line in contents.split("\n")]
    constant_types = ("string", "integer", "float", "indent", "dedent")
    token_array = numpy.array(
            [tok.type if tok.type in constant_types else tok.text
             for tok in toks])

    boundaries = []
    for i, t in enumerate(toks):
        try:
            start = t.ast_node.start_point
            end = t.ast_node.end_point
            boundaries.append(((start[0] + 1, start[1]), (end[0] + 1, end[1])))
        except AttributeError:
            if t.type == "indent":
                assert(t.new_line_before)
                next_t = toks[i+1]
                line = next_t.ast_node.start_point[0] + 1
                boundaries.append(((line, 0), (line, next_t.ast_node.start_point[1]-1)))
            elif t.type == "dedent":
                # We might be the very last token. Look backwards to the last non-dedent token to
                # figure out what line we're on.
                di = 0
                prev_t = t
                while prev_t.type == "dedent":
                    di -= 1
                    prev_t = toks[i + di]
                line = prev_t.ast_node.end_point[0] + 2
                boundaries.append(((line, 0), (line, 0)))  # Eh... good enough, though not correct
            else:
                print("UNEXPECTED TOKEN!", i, t, type(t), dir(t))
                raise

    return token_array, lines, boundaries



if __name__ == "__main__":
    args = parse_args()
    data_a = get_tokens(args.filename_a, args.language)
    data_b = get_tokens(args.filename_b or args.filename_a, args.language)
    tokens_a = data_a[0]
    tokens_b = data_b[0]

    matrix = numpy.zeros([len(tokens_a), len(tokens_b)], numpy.uint8)
    for i, value in enumerate(tokens_a):
        matrix[i, :] = (tokens_b == value)

    if args.gui:
        if can_use_gui:
            gui.launch(matrix, data_a, data_b)
        else:
            print("ERROR: Cannot load GUI. Try doing a `sudo apt-get install "
                  "python3-pil.imagetk`. If that doesn't help, open a python3 "
                  "shell, `import gui`, and see what's going wrong.")
            sys.exit(1)
    else:
        # Only import matplotlib if we're going to use it. There's some weird
        # behavior on Macs in which matplotlib works fine on its own, and PIL works
        # fine on its own, but if you import matplotlib and then try *using* PIL for
        # the GUI, we have an uncaught NSException. Consequently, we don't import
        # matplotlib at the top of the file, and instead only import it if we're
        # actually going to use it.
        from matplotlib import pyplot

        pixel_count = len(tokens_a) * len(tokens_b)
        if pixel_count > 10 * 1000 * 1000 and not args.big_file:
            print("WARNING: the image is over 10 megapixels. Saving very large "
                  "images can use so many resources that your computer "
                  "will freeze. To perform this action anyway, use the "
                  "--big_file flag.")
            sys.exit(2)

        # Otherwise, all is well.
        pyplot.imsave(args.output_location, matrix)
