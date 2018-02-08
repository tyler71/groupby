#!/usr/bin/env python3

import os
import argparse

from itertools import repeat

from DirectorySearch import recursive_directory_search
from FileProperties import first_filter, duplicate_filter
from FileProperties import md5_sum, sha256_sum
from FileProperties import modification_date
from FileProperties import disk_size

from FileActions import hardlink_files, remove_files


def main():
    filters = {
        "md5": md5_sum,
        "sha256": sha256_sum,
        "modified": modification_date,
        "accessed": access_date,
        "size": disk_size,
    }
    parser = argparse.ArgumentParser()
    parser.add_argument('directories',
                        default=os.getcwd(),
                        metavar="directory",
                        nargs='+')
    parser.add_argument('-f', "--filters",
                        choices=filters.keys(),
                        nargs='+')
    parser.add_argument('--remove',
                        dest="duplicate_action",
                        action="append_const",
                        const='remove',
                        help="Remove Duplicates, last flag applies of remove or link ")
    parser.add_argument('--link',
                        dest="duplicate_action",
                        action="append_const",
                        const='link',
                        help="Replaces Duplicates with Hard Links of Source, last flag applies of remove or link")
    args = parser.parse_args()

    # Choose only last duplicate action
    if args.duplicate_action:
        duplicate_action = args.duplicate_action[-1]
    else:
        duplicate_action = None

    # Default filtering methods
    if not args.filters:
        args.filters = ["disk_size", "md5"]

    # Get all file paths
    paths = (path for directory in args.directories
                  for path in recursive_directory_search(directory))

    # First filter converts all paths to grouped by filter and returns
    # lists of duplicates
    results = first_filter(filters[args.filters[0]], paths)
    if args.filters[1:]:
        for filter_type in (filters[filter_] for filter_ in args.filters[1:]):
            results = duplicate_filter(filter_type, results)

    if duplicate_action == "link":
        for result in results:
            hardlink_files(repeat(result[0]), result[1:])
    elif duplicate_action == "remove":
        for result in results:
            remove_files(result[1:])
    else:
        for result in results:
            if len(result) > 1:
                print(result[0])
                print('\n'.join((str(dup).rjust(len(dup) + 4) for dup in result[1:])), end='\n\n')

if __name__ == '__main__':
    main()
