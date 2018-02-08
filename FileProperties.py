import datetime
import os
import hashlib

from collections import defaultdict


# Used with checksum functions
def _iter_read(filename: str, chunk_size=65536) -> bytes:
    with open(filename, 'rb') as file:
        for chunk in iter(lambda: file.read(chunk_size), b''):
            yield chunk


def access_date(filename: str) -> datetime.datetime:
    access_date = os.path.getmtime(filename)
    parsed_date = datetime.datetime.fromtimestamp(access_date)
    return parsed_date


def modification_date(filename: str) -> datetime.datetime:
    modification_time = os.path.getmtime(filename)
    parsed_date = datetime.datetime.fromtimestamp(modification_time)
    return parsed_date


def disk_size(filename: str) -> int:
    byte_usage = os.path.getsize(filename)
    return byte_usage


def md5_sum(filename, chunk_size=65536):
    checksumer = hashlib.md5()
    for chunk in _iter_read(filename, chunk_size):
        checksumer.update(chunk)
    file_hash = checksumer.hexdigest()
    return file_hash


def sha256_sum(filename, chunk_size=65536):
    checksumer = hashlib.sha256()
    for chunk in _iter_read(filename, chunk_size):
        checksumer.update(chunk)
    file_hash = checksumer.hexdigest()
    return file_hash


def first_filter(func, paths: iter):
    grouped_duplicates = defaultdict(list)
    for path in paths:
        if os.path.isfile(path):
            signature = func(path)
            grouped_duplicates[signature].append(path)
    for duplicate in grouped_duplicates.values():
        yield duplicate


def duplicate_filter(func, duplicates: iter):
    '''
    Takes list of duplicates, compares their checksum and returns a source value,
    and duplicates identified with it as a dictionary
    :func object Takes function and applies to iterable of duplicates
    :duplicates List of duplicates
    :return: dictionary
    '''
    for duplicate in duplicates:
        filtered_duplicates = list()
        if len(duplicate) > 1:
            dup_hashes = set()
            first, *others = duplicate
            dup_hashes.add(func(first))
            for item in others:
                item_hash = func(item)
                if item_hash in dup_hashes:
                    filtered_duplicates.append(item)
            filtered_duplicates.append(others)
        yield duplicate


if __name__ == '__main__':
    print(file_hash("tests/file_properties/hash"))
    print(disk_size("tests/file_properties/5120_byte"))
    print(modification_date("tests/file_properties/5120_byte"))
    sigs = file_properties(["tests/directory_search"])
    print(sigs.items())
    print(duplicates_hashed(sigs.values()))
