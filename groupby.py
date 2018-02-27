#!/usr/bin/env python3

import argparse
import functools
import itertools
import os

import util.FileProperties
from util.DirectorySearch import directory_search
from util.FileActions import hardlink_files, remove_files
from util.FileProperties import DuplicateFilters
from util.ShellCommand import ActionShell


def main():
    available_filters = util.FileProperties.list_filters()

    def negation(func):
        def wrapper(*args, **kwargs):
            return not func(*args, **kwargs)
        return wrapper
    conditions = {
        "is_file": os.path.isfile,
        "not_symbolic_link": negation(os.path.islink),
        "not_empty": lambda filename: os.path.getsize(filename) > 0,
    }
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', "--filters",
                        choices=available_filters.keys(),
                        help="Default: size md5",
                        action="append")
    parser.add_argument('-s', '--shell',
                        dest="filters",
                        help="Filenames represented as {}: --shell \"du {} | cut -f1\"",
                        action=ActionShell)
    parser.add_argument('--exec-group',
                        dest="duplicate_action",
                        help="Filenames represented as {}, filters as {f1}, {fn}...: --exec-group \"echo {} {f1}\"",
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
    parser.add_argument('-r', '--recursive', action='store_true')
    parser.add_argument('-t', '--threshold', type=int, default=1, help="Minimum number of files in each group")
    parser.add_argument("--max-depth", type=int)
    parser.add_argument('--empty-file', action='store_true', help="Allow comparision of empty files")
    parser.add_argument('--follow-symbolic', action='store_true', help="Allow following of symbolic links for compare")
    parser.add_argument('--interactive', action='store_true')
    parser.add_argument('directories',
                        default=[os.getcwd()],
                        metavar="directory",
                        nargs='*')
    args = parser.parse_args()

    if args.follow_symbolic is True:
        conditions.pop("not_symbolic_link")
    if args.empty_file is True:
        conditions.pop("not_empty")

    # Choose only last duplicate action
    if args.duplicate_action:
        duplicate_action = args.duplicate_action[-1]
    else:
        duplicate_action = None

    args.threshold = args.threshold if args.threshold > 1 else 1

    # Default filtering methods
    args.filters = args.filters if args.filters else ["size", "md5"]

    # Get all file paths
    # Usage of set to remove duplicate directory entries
    paths = (path for directory in set(args.directories)
             for path in directory_search(directory,
                                          recursive=args.recursive,
                                          max_depth=args.max_depth,
                                          include=args.include,
                                          exclude=args.exclude
                                          )
             )

    # Get first (blocking) filter method, group other filter methods
    filter_methods = (available_filters[filter_method]
                      if type(filter_method) is str
                      else filter_method
                      for filter_method in args.filters)
    filtered_duplicates = DuplicateFilters(filters=filter_methods, filenames=paths, conditions=conditions.values())

    def dup_action_link(duplicates):
        for duplicate_result in duplicates:
            if len(duplicate_result) >= args.threshold:
                first, *others = duplicate_result
                hardlink_files(itertools.repeat(first), others)

    def dup_action_remove(duplicates):
        for duplicate_result in duplicates:
            if len(duplicate_result) >= args.threshold:
                remove_files(duplicate_result[1:])

    if duplicate_action == "link":
        filtered_duplicates = list(filtered_duplicates)
        dup_action_link(filtered_duplicates)
    elif duplicate_action == "remove":
        dup_action_remove(filtered_duplicates)
    elif type(duplicate_action) is functools.partial:
        for index, results in enumerate(filtered_duplicates):
            if len(results) >= args.threshold:
                # Take each filters output and label f1: 1st_output, fn: n_output...
                labeled_filters = {f"f{filter_number + 1}": filter_output
                                   for filter_number, filter_output in enumerate(filtered_duplicates.filter_hashes[index])}
                for result in results:
                    # Executes the command given and returns its output if available
                    command_string = duplicate_action(result, **labeled_filters)
                    print(command_string)
    else:
        if args.interactive is True:
            filtered_duplicates = tuple(filtered_duplicates)
        for index, result in enumerate(filtered_duplicates):
            if len(result) >= args.threshold:
                print(*filtered_duplicates.filter_hashes[index], sep=' -> ')
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
