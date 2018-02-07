import os


def recursive_directory_search(directory: str) -> tuple:
    directory = os.path.expanduser(directory)

    for directory, subdir, files in os.walk(directory):
        yield (directory, files)


if __name__ == '__main__':
    for directory, files in recursive_directory_search("tests/directory_search"):
        print(directory, files)
