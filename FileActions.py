import os


def remove_files(filenames: iter) -> list:
    removed_files = list()
    for filename in filenames:
        print(f"Removing {filename}")

        try:
            print(f"os.remove(filename)")
            removed_files.append(filename)
        except FileNotFoundError:
            print("Not Found")
    return removed_files


def hardlink_files(source_files: iter, duplicate_files: iter) -> list:
    linked_files = list()
    for source_file, filename in zip(source_files, duplicate_files):
        print(f"Linking {source_file} -> {filename}")
        try:
            print(f"os.remove({filename})")
            print(f"os.link({source_file}, {filename})")
            os.remove(filename)
            os.link(source_file, filename)
            linked_files.append((source_file, filename))
        except FileNotFoundError:
            print("Not Found")
    return linked_files
