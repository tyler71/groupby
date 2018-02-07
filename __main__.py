#!/usr/bin/env python3

import os
import argparse
import pprint

import itertools


from FileProperties import file_properties, duplicates_hashed
from FileActions import remove_files, hardlink_files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', "--directories",
                        default=os.getcwd(),
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
        duplicate_action = list()

    if args.force:
        if args.force == "properties":
            # Group files by modification date and size
            results = file_properties(args.directories)
        elif args.force == "checksum":
            signatures = file_properties(args.directories)
            # Compare checksums of each list of files
            results = duplicates_hashed(signatures.values())
            results += duplicates_hashed(signatures.keys())
    else:
        signatures = file_properties(args.directories)
        print(signatures)
        print(list(signatures.values()) + list(signatures.keys()))
        results = duplicates_hashed(itertools.chain(signatures.values(), [signatures.keys()]))




    if len(duplicate_action) == 0:
        for key, value in results.items():
            print(key)
            print('\n'.join((str(dup).rjust(len(dup) + 4) for dup in value)), end='\n\n')
    elif duplicate_action == "remove":
        result = remove_files(hashed.values())
    elif duplicate_action == "link":
        for source_file, duplicates in hashed.items():
            repeating_source_file = itertools.repeat(source_file)
            result = hardlink_files(repeating_source_file, duplicates)


if __name__ == '__main__':
    main()
