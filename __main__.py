#!/usr/bin/env python3

import os
import argparse
import pprint

from FileProperties import file_signatures, duplicates_hashed
from FileActions import remove_files, hardlink_files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', "--directories",
                        default=os.getcwd(),
                        nargs='+')
    parser.add_argument('--remove',
                        dest="duplicate_action",
                        action="append_const",
                        const='r',
                        help="Remove Duplicates, last flag applies of remove or link ")
    parser.add_argument('--link',
                        dest="duplicate_action",
                        action="append_const",
                        const='l',
                        help="Replaces Duplicates with Hard Links of Source, last flag applies of remove or link")
    args = parser.parse_args()
    if args.duplicate_action:
        duplicate_action = args.duplicate_action[-1]
    else:
        duplicate_action = list()

    signatures = file_signatures(args.directories)
    hashed = duplicates_hashed(signatures.values())

    if len(duplicate_action) == 0:
        for key, value in hashed.items():
            print(key)
            print('\n'.join((" " * 4 + dup for dup in value)), end='\n\n')
    elif duplicate_action == "r":
        print(hashed.values())
        #remove_files(hashed.values())
    elif duplicate_action == "l":
        for source_file, duplicates in hashed.items():
            print(f"Linking {source_file} to {duplicates}")


if __name__ == '__main__':
    main()
