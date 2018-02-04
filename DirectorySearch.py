import os

from collections import defaultdict


def recursive_directory_search(directory: str) -> dict:
    directory = os.path.expanduser(directory)
    for result in os.listdir(directory):
        path = os.path.join(directory, result)
        if os.path.isfile(path):
            yield (directory, result)
        else:
            yield from recursive_directory_search(path)


if __name__ == '__main__':
    directory_files = defaultdict(list)
    for directory, file in recursive_directory_search("testing/recursive_files"):
        directory_files[directory].append(file)

    print(directory_files)
