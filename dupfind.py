#!/usr/bin/env python3

import os
import argparse

import itertools

from util.DirectorySearch import directory_search
from util.FileProperties import first_filter, duplicate_filter
from util.FileProperties import md5_sum, sha256_sum, partial_md5_sum
from util.FileProperties import modification_date, access_date
from util.FileProperties import disk_size, direct_compare
from util.FileProperties import file_name

from util.ShellCommand import ActionShell

from util.FileActions import hardlink_files, remove_files


def main():
    filters = {
        "partial_md5": partial_md5_sum,
        "md5": md5_sum,
        "sha256": sha256_sum,
        "modified": modification_date,
        "accessed": access_date,
        "size": disk_size,
        "filename": file_name,
        "file": direct_compare,
    }
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', "--filters",
                        choices=filters.keys(),
                        help="Default: size md5",
                        action="append")
    parser.add_argument('-s', '--shell',
                        dest="filters",
                        help="Filenames represented as {}: --shell \"du {} | cut -f1\"",
                        action=ActionShell)
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
    parser.add_argument('--include', action='append')
    parser.add_argument('--exclude', action='append')
    parser.add_argument('--recursive', '-r', action='store_true')
    parser.add_argument('--interactive', action='store_true')
    parser.add_argument('directories',
                        default=[os.getcwd()],
                        metavar="directory",
                        nargs='*')
    args = parser.parse_args()

    # Choose only last duplicate action
    if args.duplicate_action:
        duplicate_action = args.duplicate_action[-1]
    else:
        duplicate_action = None

    # Default filtering methods
    if not args.filters:
        args.filters = ["size", "md5"]

    # Get all file paths
    # Usage of set to remove duplicate directory entries
    paths = (path for directory in set(args.directories)
             for path in directory_search(directory,
                                          recursive=args.recursive,
                                          include=args.include,
                                          exclude=args.exclude
                                         )
            )

    # Get first (blocking) filter method, group other filter methods
    filter_method, *other_filter_methods = (filters[filter_method]
                                            if type(filter_method) is str
                                            else filter_method
                                            for filter_method in args.filters)
    filtered_duplicates = first_filter(filter_method, paths)
    if other_filter_methods:
        for filter_method in (filter_ for filter_ in other_filter_methods):
            filtered_duplicates = duplicate_filter(filter_method, filtered_duplicates)

    def dup_action_link(duplicates):
        for duplicate_result in duplicates:
            first, *others = duplicate_result
            hardlink_files(itertools.repeat(first), others)

    def dup_action_remove(duplicates):
        for duplicate_result in duplicates:
            remove_files(duplicate_result[1:])

    if duplicate_action == "link":
        dup_action_link(filtered_duplicates)
    elif duplicate_action == "remove":
        dup_action_remove(filtered_duplicates)
    else:
        if args.interactive is True:
            filtered_duplicates = tuple(filtered_duplicates)
        for result in filtered_duplicates:
            if len(result) > 1:
                source_file, *duplicates = result
                print(source_file)
                print('\n'.join((str(dup).rjust(len(dup) + 4) for dup in duplicates)), end='\n\n')
        if args.interactive is True:
            action_on_duplicated = None
            try:
                while action_on_duplicated not in {"1", "2", "3", "exit" "link", "remove"}:
                    action_on_duplicated = str(input("Select action: \n1) link \n2) remove\n3) exit\n"))
                if action_on_duplicated in {"3", "exit"}:
                    raise KeyboardInterrupt
            except KeyboardInterrupt:
                exit("\nExiting...")

            interactive_actions = {
                "1": dup_action_link,
                "link": dup_action_link,
                "2": dup_action_remove,
                "remove": dup_action_remove,
            }
            action_on_duplicated = action_on_duplicated.lower()
            interactive_actions[action_on_duplicated](filtered_duplicates)


if __name__ == '__main__':
    main()
