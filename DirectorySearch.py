import os
import pathlib
import glob


def directory_search(directory: str, recursive=True, include=None, exclude=None) -> tuple:
    directory = os.path.expanduser(directory)


    for directory, subdir, files in os.walk(directory):
        if exclude or include:
            if exclude:
                excluded_filenames = {file for glob_match in exclude
                                      for file in files
                                      if pathlib.PurePath(file).match(glob_match)}
            else:
                excluded_filenames = set()
            if include:
                included_filenames = {file for glob_match in include
                                      for file in files
                                      if pathlib.PurePath(file).match(glob_match)}
            else:
                included_filenames = set()
            for file in files:
                if file in included_filenames:
                    yield os.path.join(directory, file)
                elif file not in excluded_filenames and len(excluded_filenames) > 0:
                    yield os.path.join(directory, file)
        else:
            for file in files:
                yield os.path.join(directory, file)

        # Break after 1st iteration to prevent recursiveness
        if recursive is False:
            break


if __name__ == '__main__':
    for directory, files in directory_search("tests/directory_search"):
        print(directory, files)
