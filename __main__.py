#!/usr/bin/env python3

from collections import defaultdict
import os
import argparse
import pprint

from DirectorySearch import recursive_directory_search
from FileProperties import modification_date, disk_size, file_hash

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', "--directory",
                        default=os.getcwd(),
                        nargs='+')
    args = parser.parse_args()

    existing_files = set()
    file_sig = defaultdict(list)
    for directory in args.directory:
        for basedir, files in recursive_directory_search(directory):
            for file in files:
                path = os.path.join(basedir, file)
                if os.path.isfile(path):
                    signature = (modification_date(path), disk_size(path))
                    file_sig[signature].append(path)

    hashed_duplicates = defaultdict(list)
    for duplicates in file_sig.values():
        if len(duplicates) > 1:
            dup_hashes = set()
            dup_generator = (duplicate for duplicate in duplicates)

            source_file = next(dup_generator)
            dup_hashes.add(file_hash(source_file))
            for item in dup_generator:
                item_hash = file_hash(item)
                if item_hash in dup_hashes:
                    hashed_duplicates[source_file].append(item)
    pprint.pprint(hashed_duplicates)


if __name__ == '__main__':
    main()
