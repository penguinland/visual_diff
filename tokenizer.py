#!/usr/bin/env python3

import code_tokenize
import numpy

import utils


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
