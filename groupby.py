#!/usr/bin/env python3

import argparse
import logging
import os
import sys
from collections import OrderedDict

from util.ActionCreateFilter import DuplicateFilters, ActionAppendFilePropertyFilter
from util.ArgumentParsing import parser_logic
from util.DirectorySearch import directory_search
from util.Logging import log_levels


def main():


    assert_statement = "Requires Python{mjr}.{mnr} or greater".format(
        mjr=sys.version_info.major,
        mnr=sys.version_info.minor)
    assert sys.version_info >= (3, 4), assert_statement

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
    parser = parser_logic(parser)
    args = parser.parse_args()

    if args.verbosity:
        logging.basicConfig(level=log_levels.get(args.verbosity, 3),
                            stream=sys.stderr,
                            format='[%(levelname)s] %(message)s')
    else:
        logging.disable(logging.CRITICAL)
    log = logging.getLogger(__name__)

    if args.follow_symbolic is True:
        conditions.pop("not_symbolic_link")
    if args.empty_file is True:
        conditions.pop("not_empty")


    # Choose only last group action
    if args.group_action:
        group_action = args.group_action[-1]
    else:
        group_action = None

    args.threshold = args.threshold if args.threshold > 1 else 1

    # Default filtering method
    if not args.filters:
        args.filters = [ActionAppendFilePropertyFilter.disk_size,
                        ActionAppendFilePropertyFilter.md5_sum]

    # Get all file paths
    # Usage of set to remove group directory entries
    paths = (path for directory in set(args.directories)
             for path in directory_search(directory,
                                          recursive=args.recursive,
                                          dir_hidden=args.dir_hidden,
                                          max_depth=args.max_depth,
                                          include=args.include,
                                          exclude=args.exclude,
                                          dir_include=args.dir_include,
                                          dir_exclude=args.dir_exclude,
                                          )
             )

    filtered_groups = DuplicateFilters(filters=args.filters, filenames=paths, conditions=conditions.values())

    # Smart action selected with 2 possible options
    # * Builtins
    # * Shell Action
    # Custom action supplied by -x, --exec-group
    # Uses references to tracked filters in filter_hashes as {f1} {fn}
    # Uses parallel brace expansion, {}, {.}, {/}, {//}, {/.}
    # Also includes expansion of {..}, just includes filename extension
    if group_action:
        for index, results in enumerate(filtered_groups):
            if len(results) >= args.threshold:
                # Take each filters output and label f1: 1st_output, fn: n_output...
                # Strip filter_output because of embedded newline
                labeled_filters = OrderedDict()
                for filter_number, filter_output in enumerate(filtered_groups.filter_hashes[index]):
                    labeled_filters["f{fn}".format(fn=filter_number + 1)] = filter_output.strip()
                command_string = group_action(results, **labeled_filters)
                for output in command_string:
                    print(output, end='')
            print('')
    else:
        # Print all groups.
        for index, result in enumerate(filtered_groups):
            if len(result) >= args.threshold:
                if args.basic_formatting:
                    logging.info(' -> '.join(filtered_groups.filter_hashes[index]))
                    print('\n'.join((str(grp)) for grp in result), end='\n')
                else:
                    source_file, *groups = result
                    log.info(' -> '.join(filtered_groups.filter_hashes[index]))
                    print(source_file)
                    if groups:
                        print('\n'.join((str(grp).rjust(len(grp) + 4) for grp in groups)), end='\n\n')
                    else:
                        print('')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("")
        exit(1)
