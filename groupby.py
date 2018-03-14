#!/usr/bin/env python3

import argparse
import logging
import os
import sys
from collections import OrderedDict

from util.ActionCreateFilter import DuplicateFilters, ActionAppendFilePropertyFilter
from util.ActionCreateFunc import print_results
from util.ArgumentParsing import parser_logic
from util.DirectorySearch import directory_search
from util.Logging import log_levels
from util.Templates import negation
from util.Templates import sanitize_string


def main():

    parser = argparse.ArgumentParser()
    parser = parser_logic(parser)
    args = parser.parse_args()

    if args.verbosity:
        logging.basicConfig(level=log_levels.get(args.verbosity, 3),
                            stream=sys.stderr,
                            format='[%(levelname)s] %(message)s',
                            )
    else:
        logging.disable(logging.CRITICAL)

    # Usage of set to remove directories specified multiple times
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

    # Default filtering method
    if not args.filters:
        size = ActionAppendFilePropertyFilter.disk_size
        md5  = ActionAppendFilePropertyFilter.md5_sum
        args.filters = [size, md5]

    conditions = {
        "is_file": os.path.isfile,
        "not_symbolic_link": negation(os.path.islink),
        "not_empty": lambda filename: os.path.getsize(filename) > 0,
    }
    # Directory condition modifying
    if args.follow_symbolic is True:
        conditions.pop("not_symbolic_link")
    if args.empty_file is True:
        conditions.pop("not_empty")

    filtered_groups = DuplicateFilters(filters=args.filters, filenames=paths, conditions=conditions.values())

    # With no action defined, just print the results
    if args.group_action:
        group_action = args.group_action[-1]
    else:
        group_action = print_results
    for index, results in enumerate(filtered_groups):
        if len(results) >= args.group_size:
            # Take each filters output and label f1: 1st_output, fn: n_output...
            # Strip filter_output because of embedded newline
            labeled_filters = OrderedDict()
            for filter_number, filter_output in enumerate(filtered_groups.filter_hashes[index]):
                labeled_filters["f{fn}".format(fn=filter_number + 1)] = sanitize_string(filter_output).strip()
            command_string = group_action(results, **labeled_filters)
            for output in command_string:
                print(sanitize_string(output), end='')
        else:
            # Removes extra blank newlines
            continue
        print('')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("")
        exit(0)
