import datetime
import logging
import os
import shlex
import shutil
import subprocess
from functools import partial

from util.Templates import ActionAppendCreateFunc
from util.Templates import StringExpansionFunc

log = logging.getLogger(__name__)

# class ActionSelectGroupFunc(ActionAppendCreateFunc, StringExpansionFunc):
#     def _process(self, template, value=None):
#         self.builtins = {
#             "link": ActionAppendLink,
#             "remove": ActionAppendRemove,
#             "merge": ActionAppendMerge,
#         }
#         selected_class_func = self.check_group_exec_type(template)
#         templated_func = selected_class_func()
#
#         return templated_func(template)
#
#     def check_group_exec_type(self, template):
#         def valid_regex(regex):
#             try:
#                 re.compile(regex)
#                 return True
#             except re.error:
#                 return False
#
#         if template in self.builtins:
#             return self.builtins[template]
#         elif any((alias in template
#                   for alias in self.aliases)):
#             return ActionAppendExecShell
#         elif "merge:" in template:
#             return ActionAppendMerge
#         else:
#             "No valid group exec detected"
#             exit(1)


class ActionAppendExecShell(ActionAppendCreateFunc, StringExpansionFunc):
    def _process(self, template):
        template_format = StringExpansionFunc(template)
        shell_command = partial(self._group_invoke_shell, command=template_format)
        return shell_command

    def _group_invoke_shell(self, filtered_group, command, **kwargs):
        command_outputs = list()
        for file in filtered_group:
            output = self._invoke_shell(file, command=command, **kwargs)
            command_outputs.append(output)
        return command_outputs

    def _invoke_shell(self, *args, command, **kwargs) -> str:
        args = (shlex.quote(arg) for arg in args)
        try:
            output = subprocess.check_output(command(*args, **kwargs), shell=True).decode('utf8')
        except subprocess.CalledProcessError as e:
            print("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
            return ''
        except KeyError as e:
            print("Filter", e, "not found")
            exit(1)
        return output


def remove_files(filtered_group: iter, **kwargs) -> list:
    removed_files = list()
    for filename in filtered_group:
        try:
            pass
            removed_files.append("Removing {file}\n".format(file=filename))
            # os.remove(filename)
            # removed_files.append(filename)
        except FileNotFoundError:
            print("Not Found")
    return removed_files


def hardlink_files(filtered_group: iter, **kwargs) -> list:
    linked_files = list()
    source_file = filtered_group[0]

    for filename in filtered_group:
        try:
            pass
            linked_files.append("Linking {source_file} -> {filename}\n".format(source_file=source_file, filename=filename))
            # os.remove(filename)
            # os.link(source_file, filename)
        except FileNotFoundError:
            print("Not Found")
    return linked_files


class ActionAppendMerge(ActionAppendCreateFunc):
    def _process(self, template):
        mergedir_flag = template
        overwrite_flags = {
            "COUNT": self._count,
            "IGNORE": self._ignore,
            "ERROR": self._error,
            "CONDITION": self._condition,
        }
        if ":" in mergedir_flag:
            mergedir_flag = mergedir_flag.split(":")
            if len(mergedir_flag) == 2:
                merge_dir, overwrite_flag = mergedir_flag
                condition = None
            if len(mergedir_flag) == 3:
                merge_dir, overwrite_flag, condition = mergedir_flag
        else:
            merge_dir = mergedir_flag
            condition = None
            overwrite_flag = None

        if overwrite_flag is not None and overwrite_flag.upper() == 'CONDITION':
            assert condition is not None

        if overwrite_flag is not None:
            try:
                overwrite_method = overwrite_flags[overwrite_flag.upper()]
            except KeyError as e:
                print('{} is not a valid key'.format(e))
                exit(1)
        else:
            overwrite_method = self._count

        if os.path.exists(merge_dir):
            raise IsADirectoryError("{} already exists".format(merge_dir))
        else:
            os.makedirs(merge_dir)

        callable_ = partial(self._abstract_call,
                            condition=condition,
                            merge_dir=merge_dir,
                            overwrite_method=overwrite_method)
        return callable_

    def _abstract_call(self, filtered_group, *, condition, merge_dir, overwrite_method, **kwargs):

        self.condition = condition
        filter_dir = os.path.join(merge_dir, *kwargs.values())
        os.makedirs(filter_dir)
        output = overwrite_method(filter_dir, filter_group=filtered_group)
        return output

    def _count(self, filter_dir, filter_group):
        # This keeps the left padding of 0's
        def incr_count(count):
            return str(int(count) + 1).zfill(len(count))

        def create_file_path(dir, filename, count=None, fileext=None):
            if count is not None:
                filename = '_'.join([filename, count])
            if fileext is not None:
                filename = ''.join([filename + fileext])
            dest_dir_file = os.path.join(dir, filename)
            return dest_dir_file

        for file in filter_group:
            filename = os.path.split(file)[1]
            filename_split = filename.split('.')

            dest_dir_file = os.path.join(filter_dir, filename)
            if os.path.exists(dest_dir_file):
                count = '0000'
                dest_dir = filter_dir
                dest_dir_file = create_file_path(dest_dir, filename)
                while os.path.exists(dest_dir_file):
                    count = incr_count(count)
                    dest_file = os.path.join(filename_split[0] + "_{}.".format(count) + filename_split[1])
                    dest_dir_file = os.path.join(dest_dir, dest_file)
                shutil.copy(file, dest_dir_file)
                yield dest_dir_file + '\n'
            else:
                dest_dir_file = os.path.join(filter_dir, filename)
                shutil.copy(file, dest_dir_file)
                yield dest_dir_file + '\n'

    def _ignore(self, filter_dir, filter_group):
        moved_files = list()

        for file in filter_group:
            filename = os.path.split(file)[1]
            dest_file = os.path.join(filter_dir, filename)
            if os.path.exists(dest_file):
                log.info("{} Exists, Ignoring {}".format(dest_file, file))
                continue
            else:
                dest_dir_file = os.path.join(filter_dir, filename)
                shutil.copy(file, dest_dir_file)
                moved_files.append(dest_dir_file + '\n')

        return moved_files

    def _error(self, filter_dir, filter_group):
        moved_files = list()

        for file in filter_group:
            filename = os.path.split(file)[1]
            if os.path.exists(os.path.join(filter_dir, filename)):
                raise FileExistsError
            else:
                dest_dir_file = os.path.join(filter_dir, filename)
                shutil.copy(file, dest_dir_file)
                moved_files.append(dest_dir_file + '\n')

        return moved_files

    def _condition(self, filter_dir, filter_group):
        def modification_date(filename: str) -> str:
            modification_time = os.path.getmtime(filename)
            modified_datetime = datetime.datetime.fromtimestamp(modification_time)
            return str(modified_datetime)

        def disk_size(filename: str) -> str:
            byte_usage = os.path.getsize(filename)
            return str(byte_usage)

        conditions = {
            'LARGER': lambda file1, file2: disk_size(file1) > disk_size(file2),
            'SMALLER' : lambda file1, file2: disk_size(file1) < disk_size(file2),
            'NEWER'  : lambda file1, file2: modification_date(file1) < modification_date(file2),
            'OLDER'  : lambda file1, file2: modification_date(file1) > modification_date(file2),
        }
        condition = conditions[self.condition.upper()]
        moved_files = list()

        for file in filter_group:
            filename = os.path.split(file)[1]
            dest_dir_file = os.path.join(filter_dir, filename)
            if os.path.exists(dest_dir_file):
                if condition(file, dest_dir_file):
                    log.info("{} overwriting {}".format(file, dest_dir_file))
                    shutil.copy(file, dest_dir_file)
            else:
                dest_dir_file = os.path.join(filter_dir, filename)
                shutil.copy(file, dest_dir_file)
                moved_files.append(dest_dir_file + '\n')

        return moved_files
