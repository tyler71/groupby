import os

from util.Templates import ActionTemplate


def remove_files(filenames: iter) -> list:
    removed_files = list()
    for filename in filenames:
        print("Removing {file}".format(file=filename))
        try:
            os.remove(filename)
            removed_files.append(filename)
        except FileNotFoundError:
            print("Not Found")
    return removed_files


def hardlink_files(source_files: iter, group_files: iter) -> list:
    linked_files = list()
    for source_file, filename in zip(source_files, group_files):
        print("Linking {source_file} -> {filename}".format(source_file=source_file, filename=filename))
        try:
            os.remove(filename)
            os.link(source_file, filename)
            linked_files.append((source_file, filename))
        except FileNotFoundError:
            print("Not Found")
    return linked_files

class ActionMerge(ActionTemplate):
    def _process(self, template):
        if ":" in template:
            template = template.split(":")
        else:
            merge_dir = template
        if len(template) == 2:
            merge_dir, overwrite_flag = template
        elif len(template) == 3:
            merge_dir, overwrite_flag, condition = template

        if not os.path.exists(merge_dir):
            os.makedirs(merge_dir)
        if os.path.exists(merge_dir) and len(os.listdir(merge_dir)) == 0:
            pass

