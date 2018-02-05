#!/usr/bin/env python3

from collections import defaultdict
import os
import argparse

from DirectorySearch import recursive_directory_search
from File_Properties import modification_date, disk_size, file_hash

existing_files = set()
file_sig = defaultdict(list)
for basedir, files in recursive_directory_search("~/Ram/tester"):
    for file in files:
        print(file)
        path = os.path.join(basedir, file)
        signature = (modification_date(path), disk_size(path))
        file_sig[signature].append(path)

for signature, duplicates in file_sig.items():
    if len(duplicates) > 1:
        dup_hashes = set()
        for item in duplicates:
            item_hash = file_hash(item)
            if item_hash in dup_hashes:
                print("Duplicate")
            else:
                dup_hashes.add(item_hash)
