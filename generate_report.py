#!/usr/bin/env python3
import argparse
import collections
import glob

import find_duplicates
import tokenizer
import utils


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("file_glob", nargs="*",
                        help="Glob pattern of files to analyze")
    parser.add_argument("--min_length", "-ml", type=int, default=100,
                        help="Minimum number of duplicated tokens to report")
    parser.add_argument("--big_files", "-bf", action="store_true",
                        help="Don't skip images over 50 megapixels")
    return parser.parse_args()


def find_all_files(glob_patterns):
    """
    We take in a string describing a glob pattern, and return a dict mapping
    language names to lists of filenames in the glob whose extension matches the
    language (e.g., `{"cpp": ["example.hpp", "example.cpp"]}`).
    """
    results = collections.defaultdict(list)
    for glob_pattern in glob_patterns:
        for filename in glob.iglob(glob_pattern):
            try:
                language = utils.guess_language(filename)
            except ValueError:
                print(f"Skipping file '{filename}' in unknown format")
                continue
            results[language].append(filename)
    return results


def compare_files(filename_a, data_a, filename_b, data_b,
                  min_segment_size, include_large_files=False):
    """
    Returns a list of strings that should be shown in a report about
    duplication within these files.
    """
    pixel_count = len(data_a.tokens) * len(data_b.tokens)
    if pixel_count > utils.PIXELS_IN_BIG_FILE and not include_large_files:
        return ["skipping analysis of too-big image "
                f"for '{filename_a}' and '{filename_b}'"]
    matrix = utils.make_matrix(data_a.tokens, data_b.tokens)
    segments = find_duplicates.get_segments(matrix, (filename_a == filename_b))
    # We'll keep a tuple of (negative_size, start_line_a, end_line_a,
    # start_line_b, end_line_b) for each large segment we find. We store the
    # negative of the size so that, when sorted, the largest segments come
    # first.
    large_segments = set()
    for segment in segments:
        if segment.size() < min_segment_size:
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
        return []  # No major duplication!
    # Otherwise...
    results = [f"Found duplicated code between {filename_a} and {filename_b}:"]

    def sorting_key(data):
        # Sort by the starting line in file A, then starting line in file B,
        # then by length (largest to smallest).
        return (data[1], data[3], -data[0])
    large_segments = sorted(large_segments, key=sorting_key)
    for size, start_a, end_a, start_b, end_b in large_segments:
        results.append(f"    {size} tokens on lines "
                       f"{start_a}-{end_a} and lines {start_b}-{end_b}")
    return results


def compare_all_files(file_data, min_segment_size, include_large_files):
    """
    Returns a list of strings that should be shown in a report about
    duplication within these files.
    """
    results = []
    # Compare all pairs of files. After comparing A with B, don't also compare
    # B with A, but do remember to compare A with A.
    for i, (filename_a, data_a) in enumerate(file_data):
        for filename_b, data_b in file_data[i:]:
            pair_results = compare_files(
                    filename_a, data_a, filename_b, data_b, min_segment_size,
                    include_large_files)
            results.extend(pair_results)
    return results


if __name__ == "__main__":
    args = parse_args()
    languages_to_file_lists = find_all_files(args.file_glob)
    for language, file_list in languages_to_file_lists.items():
        data = []
        for filename in file_list:
            try:
                data.append((filename,
                             tokenizer.get_file_tokens(filename, language)))
            except SyntaxError:
                print(f"Cannot parse {filename}")

        for line in compare_all_files(
                data, args.min_length, args.big_files):
            print(line)
