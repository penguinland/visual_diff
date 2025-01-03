#!/usr/bin/env python3

import collections
import glob

import find_duplicates
import tokenizer
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
                      for filename in (filename_a, filename_b))
    pixel_count = len(data_a.tokens) * len(data_b.tokens)
    if pixel_count > utils.PIXELS_IN_BIG_FILE:
        print("skipping analysis of too-big image "
              f"for '{filename_a}' and '{filename_b}'")
        return
    matrix = utils.make_matrix(data_a.tokens, data_b.tokens)
    segments = find_duplicates.get_segments(matrix, (filename_a == filename_b))
    # We'll keep a tuple of (negative_size, start_line_a, end_line_a,
    # start_line_b, end_line_b) for each large segment we find. We store the
    # negative of the size so that, when sorted, the largest segments come
    # first.
    large_segments = set()
    for segment in segments:
        if segment.size() < 100:
            continue
        # When comparing a file to itself, don't consider the segment from X to
        # Y as distinct from the segment from Y to X.
        if filename_a == filename_b and segment.top[0] > segment.top[1]:
                continue
        large_segments.add((segment.size(),
                            data_a.boundaries[segment.top[0]][0][0],
                            data_a.boundaries[segment.bottom[0]][1][0],
                            data_b.boundaries[segment.top[1]][0][0],
                            data_b.boundaries[segment.bottom[1]][1][0],
                            ))

    if not large_segments:
        return  # No major duplication!
    # Otherwise...
    print(f"Found duplicated code between {filename_a} and {filename_b}:")
    def sorting_key(data):
        # Sort by the starting line in file A, then starting line in file B,
        # then by length (largest to smallest).
        return (data[1], data[3], -data[0])
    large_segments = sorted(large_segments, key=sorting_key)
    for size, start_a, end_a, start_b, end_b in large_segments:
        print(f"    {size} tokens on lines "
              f"{start_a}-{end_a} and lines {start_b}-{end_b}")


compare_files("examples/pointsprite.py", "examples/pointsprite.py", "python")


def compare_all_files(filenames, language):
    # Compare all pairs of files. After comparing A with B, don't also compare
    # B with A, but do remember to compare A with A.
    for i, filename_a in enumerate(filenames):
        for filename_b in filenames[i:]:
            compare_files(filename_a, filename_b, language)

compare_all_files(["examples/gpsnmea.go", "examples/gpsrtk.go"], "go")
