import os
import hashlib
import re

from collections import OrderedDict

class OrderedDefaultListDict(OrderedDict):
    def __missing__(self, key):
        self[key] = value = []
        return value

# This matches a newline, a space, tab, return character OR a null value: between the | and )
_whitespace = re.compile('^([\n \t\r]|)+$')


# Used with checksum functions
def _iter_read(filename: str, chunk_size=65536) -> bytes:
    with open(filename, 'rb') as file:
        for chunk in iter(lambda: file.read(chunk_size), b''):
            yield chunk


def access_date(filename: str) -> str:
    access_time = os.path.getmtime(filename)
    return str(access_time)


def modification_date(filename: str) -> str:
    modification_time = os.path.getmtime(filename)
    return str(modification_time)


def file_name(filename: str) -> str:
    file_basename = os.path.basename(filename)
    return str(file_basename)


def disk_size(filename: str) -> str:
    byte_usage = os.path.getsize(filename)
    return str(byte_usage)


def md5_sum(filename, chunk_size=65536) -> str:
    checksumer = hashlib.md5()
    for chunk in _iter_read(filename, chunk_size):
        checksumer.update(chunk)
    file_hash = checksumer.hexdigest()
    return str(file_hash)


def sha256_sum(filename, chunk_size=65536) -> str:
    checksumer = hashlib.sha256()
    for chunk in _iter_read(filename, chunk_size):
        checksumer.update(chunk)
    file_hash = checksumer.hexdigest()
    return str(file_hash)


def partial_md5_sum(filename, chunk_size=65536, chunks_read=200) -> str:
    checksumer = hashlib.md5()
    with open(filename, 'rb') as file:
        for null in range(0, chunks_read):
            chunk = file.read(chunk_size)
            if chunk == b'':
                break
            checksumer.update(chunk)
    return checksumer.hexdigest()


def direct_compare(filename) -> bytes:
    with open(filename, 'rb') as file:
        data = file.read()
    return data


class DuplicateFilters:
    def __init__(self, *, filters, filenames):
        self.filters = filters
        self.filenames = filenames
        self.filter_hashes = list()

    def __iter__(self):
        return self.process()

    def process(self):
        first_filter, *additional_filters = self.filters
        results = self._first_filter(first_filter, self.filenames)
        for additional_filter in additional_filters:
            results = self._additional_filters(additional_filter, results)
        for duplicate_list in results:
            yield duplicate_list

    def _first_filter(self, func, paths):
        grouped_duplicates = OrderedDefaultListDict()
        for path in paths:
            if os.path.isfile(path):
                item_hash = func(path)
                if len(item_hash) < 10 and _whitespace.match(str(item_hash)):
                    # Just a newline means no output
                    continue
                grouped_duplicates[item_hash].append(path)
        for key, duplicate in grouped_duplicates.items():
            if len(duplicate) > 1:
                # key is appended enclosed in a list to group it, allowing other filters to also append to that
                # specific group
                self.filter_hashes.append([key])
                yield duplicate

    def _additional_filters(self, func, duplicates, index_offset=0, insert_group=False):
        unmatched_duplicates = OrderedDefaultListDict()
        for index, duplicate_list in enumerate(duplicates):
            index += index_offset
            filtered_duplicates = list()
            if len(duplicate_list) > 1:
                first, *others = duplicate_list
                filtered_duplicates.append(first)
                source_hash = func(first)

                # For each additional filter, append the source hash to the filter_hashes, allowing
                # a user to use the results as part of a command
                if insert_group:
                    self.filter_hashes.insert(index, list())
                    self.filter_hashes[index].append(source_hash)
                else:
                    self.filter_hashes[index].append(source_hash)

                for item in others:
                    item_hash = func(item)

                    # If matching _whitespace, continue since it shouldn't be considered a valid
                    # output, however will only check for values less then 10 (for performance)
                    if len(item_hash) < 10 and _whitespace.match(str(item_hash)):
                        continue

                    # If this item matches the source, include it in the list to be returned.
                    if item_hash == source_hash:
                        filtered_duplicates.append(item)
                    else:
                        unmatched_duplicates[item_hash].append(item)

            # Calls itself on all unmatched groups
            if unmatched_duplicates:
                print('-' * 10)
                index_offset = index + 1
                yield from self._additional_filters(func, duplicates, index_offset=index_offset, insert_group=True)

            yield filtered_duplicates


if __name__ == '__main__':
    print(md5_sum("tests/file_properties/hash"))
    print(partial_md5_sum("tests/file_properties/hash"))
    print(sha256_sum("tests/file_properties/hash"))

    print(disk_size("tests/file_properties/5120_byte"))
    print(modification_date("tests/file_properties/5120_byte"))
