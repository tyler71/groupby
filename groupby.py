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
from util.Templates import unicode_check
from util.Templates import negation
from util.ActionCreateFunc import print_results


def main():
    assert_statement = "Requires Python{mjr}.{mnr} or greater".format(
        mjr=sys.version_info.major,
        mnr=sys.version_info.minor)
    assert sys.version_info >= (3, 4), assert_statement

    parser = argparse.ArgumentParser()
    parser = parser_logic(parser)
    args = parser.parse_args()

    if args.verbosity:
        logging.basicConfig(level=log_levels.get(args.verbosity, 3),
                            stream=sys.stderr,
                            format='[%(levelname)s] %(message)s')
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
        args.filters = [ActionAppendFilePropertyFilter.disk_size,
                        ActionAppendFilePropertyFilter.md5_sum]

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
        if len(results) >= args.threshold:
            # Take each filters output and label f1: 1st_output, fn: n_output...
            # Strip filter_output because of embedded newline
            labeled_filters = OrderedDict()
            for filter_number, filter_output in enumerate(filtered_groups.filter_hashes[index]):
                labeled_filters["f{fn}".format(fn=filter_number + 1)] = unicode_check(filter_output).strip()
            command_string = group_action(results, **labeled_filters)
            for output in command_string:
                print(output, end='')
        print('')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("")
        exit(1)
