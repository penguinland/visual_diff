import code_tokenize
import collections
import numpy


# The tokens is a list of tokens contained in a file.
# The lines is a list of strings containing the file contents.
# The boundaries is a list of ((start_row, start_col), (end_row, end_col))
#     tuples for each token.
FileInfo = collections.namedtuple("FileInfo", ["tokens", "lines", "boundaries"])


def get_tokens(file_contents, language):
    """
    We return a FileInfo object containing details of the given
    file_contents.
    """
    toks = code_tokenize.tokenize(file_contents, lang=language)
    toks = [t for t in toks if t.type not in ("newline", "comment")]
    lines = list(file_contents.split("\n"))
    constant_types = ("string", "integer", "float", "indent", "dedent")
    token_array = numpy.array(
        [tok.type if tok.type in constant_types else tok.text for tok in toks])
    boundaries = _get_boundaries(toks)
    return FileInfo(token_array, lines, boundaries)


def _get_boundaries(toks):
    boundaries = []
    most_recent_line = 1  # Used when parsing dedents
    for i, t in enumerate(toks):
        try:
            # Most tokens contain their start and end values. However, the
            # tokenizer we use starts counting lines at 0, and we need to
            # start counting at 1. So, add 1 to all line indices.
            start = t.ast_node.start_point
            end = t.ast_node.end_point
            most_recent_line = end[0] + 1
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
                # If there are other non-dedent tokens after us, we can use
                # their starting column as our ending column.
                next_i = i
                while next_i < len(toks) and toks[next_i].type == "dedent":
                    next_i += 1
                if next_i == len(toks):  # No following tokens: we hit EOF.
                    # No following tokens: we hit EOF. We probably can't display
                    # this token.
                    line = most_recent_line
                    end_column = 0
                else:  # We found a non-dedent token: we stop where it starts
                    line, end_column = toks[next_i].ast_node.start_point
                # Remember we number our lines starting at 1, not 0.
                boundaries.append(((line + 1, 0), (line + 1, end_column)))
            else:
                print("UNEXPECTED TOKEN!", i, t, type(t), dir(t))
                raise
    return boundaries
