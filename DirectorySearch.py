import os


def recursive_directory_search(directory: str) -> tuple:
    directory = os.path.expanduser(directory)

    for directory, subdir, files in os.walk(directory):
        for file in files:
            yield os.path.join(directory, file)


if __name__ == '__main__':
    for directory, files in recursive_directory_search("tests/directory_search"):
        print(directory, files)
