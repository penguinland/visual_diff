#!/usr/bin/env python3

import collections
import glob

import find_duplicates
import utils


def find_all_files(glob_pattern):
    """
    We take in a string describing a glob pattern, and return a dict mapping
    language names to lists of filenames in the glob whose extension matches the
    language (e.g., `{"cpp": ["example.hpp", "example.cpp"]}`).
    """
    results = collections.defaultdict(list)
    for filename in glob.iglob(glob_pattern):
        language = utils.guess_language(filename)
        results[language].append(filename)
    return results


def compare_files(filename_a, filename_b, language):
    data_a, data_b = (tokenizer.get_file_tokens(filename, language)
                      for filename in (args.filename_a, args.filename_b))
    pixel_count = len(data_a.tokens) * len(data_b.tokens)
    if pixel_count > utils.PIXELS_IN_BIG_FILE:
        print("skipping analysis of too-big image "
              f"for '{filename_a}' and '{filename_b}'")
        return
    matrix = utils.make_matrix(data_a.tokens, data_b.tokens)
    segments = find_duplicates.get_segments(matrix, (filename_a == filename_b))
    # We'll keep a tuple of (size, start_line_a, end_line_a, start_line_b,
    # end_line_b) for each large segment we find.
    large_segments = set()
    for segment in segments:
        if segment.size() < 100:
            continue
        large_segments.add((



def compare_all_files(filenames, language):
    for filename_a in filenames:
        for filename_b in filenames:
            compare_files(filename_a, filename_b, language)
