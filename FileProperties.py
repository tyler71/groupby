import datetime
import os
import hashlib

def modification_date(filename: str) -> datetime.datetime:
    modification_time = os.path.getmtime(filename)
    parsed_date = datetime.datetime.fromtimestamp(modification_time)
    return parsed_date


def disk_size(filename: str) -> int:
    byte_usage = os.path.getsize(filename)
    return byte_usage


def file_hash(filename: str) -> str:
    def iter_read(filename: str, chunk_size=65536) -> bytes:
        with open(filename, 'rb') as file:
            for chunk in iter(lambda: file.read(chunk_size), b''):
                yield chunk

    sha256 = hashlib.sha256()
    for chunk in iter_read(filename):
        sha256.update(chunk)
    file_hash = sha256.hexdigest()

    return file_hash


if __name__ == '__main__':
    print(file_hash("tests/file_properties/hash"))
    print(disk_size("tests/file_properties/5120_byte"))
    print(modification_date("tests/file_properties/5120_byte"))