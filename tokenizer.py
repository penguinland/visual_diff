import code_tokenize
import numpy
import numpy.typing
from typing import NamedTuple, Optional

from code_tokenize.tokens import ASTToken

import utils


# Syntactic sugar: a Boundary contains the start and end of a token, where
# each position is described by its line number and the column within the line.
# The first line of the file is line 1, but the first column of the line is
# column 0. The end is the first location *after* the end of the token (which
# might be 1 character past the end of the current line, if this is the last
# token on the line).
# Example: This file:
#     print("hi")
#     print("bye")
# Likely has these boundaries:
#     ((1,  0), (1,  5))  print
#     ((1,  5), (1,  6))  (
#     ((1,  6), (1, 10))  "hi"
#     ((1, 10), (1, 11))  )
#     ((2,  0), (2,  5))  print
#     ((2,  5), (2,  6))  (
#     ((2,  6), (2, 11))  "bye"
#     ((2, 11), (2, 12))  )
Boundary = tuple[tuple[int, int], tuple[int, int]]


class FileInfo(NamedTuple):
    tokens: numpy.typing.NDArray[numpy.str_]
    lines: list[str]
    boundaries: list[Boundary]
    filename: str


def get_file_tokens(filename: str, language: Optional[str]=None) -> FileInfo:
    if language is None:
        language = utils.guess_language(filename)
    with open(filename) as f:
        return get_tokens(f.read(), language, filename)


def get_tokens(file_contents: str, language: str, filename: str) -> FileInfo:
    try:
        toks = code_tokenize.tokenize(file_contents, lang=language)
    except ValueError:
        # Empty files (such as `__init__.py`) break the code_tokenize
        # implementation, so return early.
        return FileInfo(numpy.array([]), [], [], filename)

    toks = [t for t in toks if t.type not in ("newline", "comment")]
    lines = list(file_contents.split("\n"))
    constant_types = ("string", "integer", "float", "indent", "dedent")
    token_array = numpy.array(
        [tok.type if tok.type in constant_types else tok.text for tok in toks])
    boundaries = _get_boundaries(toks)
    return FileInfo(token_array, lines, boundaries, filename)


def _find_boundary(
    i: int,
    tok: ASTToken,
    toks: list[ASTToken],
    most_recent_line: int
) -> Boundary:
    """
    toks is a list of all tokens in a file. tok is the token at index i in this
    list. We return the Boundary in the file at which this token starts and
    ends.
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


def _get_boundaries(toks: list[ASTToken]) -> list[Boundary]:
    most_recent_line = 0  # Used when parsing dedents in Python
    boundaries = []
    for i, tok in enumerate(toks):
        start, end = _find_boundary(i, tok, toks, most_recent_line)
        # The tokenizer we use starts counting lines at 0, and we need to start
        # counting at 1. So, add 1 to all line indices.
        boundaries.append(((start[0] + 1, start[1]), (end[0] + 1, end[1])))
        most_recent_line = end[0]
    return boundaries
