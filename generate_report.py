#!/usr/bin/env python3
import argparse
import collections
import glob
from typing import Iterator

import find_duplicates
import tokenizer
import utils


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("file_glob", nargs="*",
                        help="Glob pattern of files to analyze")
    parser.add_argument("--min_length", "-ml", type=int, default=300,
                        help="Minimum number of duplicated tokens to report")
    parser.add_argument("--big_files", "-bf", action="store_true",
                        help="Don't skip images over 50 megapixels")
    return parser.parse_args()


def find_all_files(glob_patterns: str) -> dict[str, list[str]]:
    """
    We return a dict mapping language names to lists of filenames in the glob
    whose extension matches the language (e.g., `{"cpp": ["example.hpp",
    "example.cpp"]}`).
    """
    results = collections.defaultdict(list)
    for glob_pattern in glob_patterns:
        for filename in glob.iglob(glob_pattern, recursive=True):
            try:
                language = utils.guess_language(filename)
            except ValueError:
                print(f"Skipping file '{filename}' in unknown format")
                continue
            results[language].append(filename)
    return results


def compare_files(
    data_a: tokenizer.FileInfo,
    data_b: tokenizer.FileInfo,
    min_segment_size: int,
    include_big_files: bool=False,
) -> Iterator[str]:
    """
    Returns a list of strings that should be shown in a report about
    duplication within these files.
    """
    filename_a = data_a.filename
    filename_b = data_b.filename

    pixel_count = len(data_a.tokens) * len(data_b.tokens)
    if pixel_count > utils.PIXELS_IN_BIG_FILE and not include_big_files:
        yield ("skipping analysis of too-big image "
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
        return  # No major duplication!
    # Otherwise...
    yield f"Found duplicated code between {filename_a} and {filename_b}:"

    def sorting_key(
        data: tuple[int, int, int, int, int]
    ) -> tuple[int, int, int]:
        # Sort by the starting line in file A, then starting line in file B,
        # then by length (largest to smallest).
        return (data[1], data[3], -data[0])
    sorted_large_segments = sorted(large_segments, key=sorting_key)
    for size, start_a, end_a, start_b, end_b in sorted_large_segments:
        yield (f"    {size} tokens on lines "
               f"{start_a}-{end_a} and lines {start_b}-{end_b}")


def compare_all_files(
    file_data: list[tokenizer.FileInfo],
    min_segment_size: int,
    include_big_files: bool=False,
) -> Iterator[str]:
    """
    Returns a list of strings that should be shown in a report about
    duplication within these files.
    """
    # Compare all pairs of files. After comparing A with B, don't also compare
    # B with A, but do remember to compare A with A.
    for i, data_a in enumerate(file_data):
        for data_b in file_data[i:]:
            yield from compare_files(
                    data_a, data_b, min_segment_size, include_big_files)


def process_all_files_in_language(
    language: str,
    file_list: list[str],
    min_length: int,
    include_big_files: bool,
) -> None:
    """
    Given a language and a list of files containing code in that language,
    tokenize each file and look for duplicated code between them all. Print out
    anything you find.
    """
    data = []
    for filename in file_list:
        try:
            data.append(tokenizer.get_file_tokens(filename, language))
        except SyntaxError:
            print(f"Cannot parse {filename}")

    for line in compare_all_files(data, min_length, include_big_files):
        print(line)


if __name__ == "__main__":
    args = parse_args()
    languages_to_file_lists = find_all_files(args.file_glob)
    for language, file_list in languages_to_file_lists.items():
        process_all_files_in_language(
                language, file_list, args.min_length, args.big_files)
