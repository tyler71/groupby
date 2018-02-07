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
        "modification_date": modification_date,
        "disk_size": disk_size,
    }
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', "--directories",
                        default=os.getcwd(),
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
    parser.add_argument("--force",
                        choices=["properties", "checksum"])
    args = parser.parse_args()

    if args.duplicate_action:
        duplicate_action = args.duplicate_action[-1]
    else:
        duplicate_action = None
    if not args.filters:
        args.filters = ["disk_size", "md5"]

    paths = (path for directory in args.directories
                  for path in recursive_directory_search(directory))

    results = first_filter(filters[args.filters[0]], paths)
    if args.filters[1:]:
        for filter_type in (filters[filter] for filter in args.filters[1:]):
            results = duplicate_filter(filter_type, results)

    if duplicate_action == "link":
        for result in results:
            hardlink_files(repeat(result[0]), result[1:])
    elif duplicate_action == "remove":
        for result in results:
            remove_files(result[1:])
    else:
        for result in results:
            print(result[0])
            print('\n'.join((str(dup).rjust(len(dup) + 4) for dup in result[1:])), end='\n\n')


if __name__ == '__main__':
    main()
