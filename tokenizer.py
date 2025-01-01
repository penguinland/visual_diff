import code_tokenize
import collections
import numpy

import utils


# The tokens is a list of tokens contained in a file.
# The lines is a list of strings containing the file contents.
# The boundaries is a list of ((start_row, start_col), (end_row, end_col))
#     tuples for each token.
FileInfo = collections.namedtuple("FileInfo", ["tokens", "lines", "boundaries"])


def get_file_tokens(filename, language=None):
    if language is None:
        language = utils.guess_language(filename)
    with open(filename) as f:
        return get_tokens(f.read(), language)


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


def _find_boundary(i, tok, toks, most_recent_line):
    """
    toks is a list of all tokens in a file. tok is the token at index i in this
    list. We return a ((start_r, start_c), (end_r, end_c)) tuple of the row and
    column at which this token starts and ends.
    """
    try:
        node = tok.ast_node
        return node.start_point, node.end_point
    except AttributeError:  # Token doesn't have a start_point or end_point
        match tok.type:
            case "indent":
                # When we add indentation, it's on the same line as the next
                # token. Pretend it starts at the beginning of the line and
                # ends just before the start of the next token.
                assert(tok.new_line_before)
                end = toks[i + 1].ast_node.start_point
                return (end[0], 0), end
            case "dedent":
                # If there are other non-dedent tokens after us, we can use
                # their starting column as our ending column.
                next_i = i
                try:
                    while toks[next_i].type == "dedent":
                        next_i += 1
                except IndexError:  # No following tokens: we hit EOF.
                    return (most_recent_line, 0), (most_recent_line, 0)
                # Otherwise, we found a non-dedent token: stop where it starts
                end = toks[next_i].ast_node.start_point
                return (end[0], 0), end
            case _:
                print("UNEXPECTED TOKEN!", i, tok, type(tok), dir(tok))
                raise


def _get_boundaries(toks):
    most_recent_line = 0  # Used when parsing dedents in Python
    boundaries = []
    for i, tok in enumerate(toks):
        start, end = _find_boundary(i, tok, toks, most_recent_line)
        # The tokenizer we use starts counting lines at 0, and we need to start
        # counting at 1. So, add 1 to all line indices.
        boundaries.append(((start[0] + 1, start[1]), (end[0] + 1, end[1])))
        most_recent_line = end[0]
    return boundaries
