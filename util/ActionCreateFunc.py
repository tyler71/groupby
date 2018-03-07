import os
import shlex
import subprocess
import re
import shutil
from functools import partial

from util.Templates import ActionAppendCreateFunc
from util.Templates import StringExpansionFunc

from util.ActionCreateFilter import disk_size, modification_date


class ActionSelect(ActionAppendCreateFunc, StringExpansionFunc):
    def _process(self, template):
        self.builtins = {
            "link": ActionAppendLink,
            "remove": ActionAppendRemove,
            "merge": ActionAppendMerge,
        }
        selected_class_func = self.check_group_exec_type(template)

        return selected_class_func(template)

    def check_group_exec_type(self, template):
        def valid_regex(regex):
            try:
                re.compile(regex)
                return True
            except re.error:
                return False

        if template in self.builtins:
            return self.builtins[template]
        elif any((alias in template
                  for alias in self.aliases)):
            return ActionAppendExecShell


class ActionAppendExecShell(ActionAppendCreateFunc):
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


class ActionAppendRemove(ActionAppendCreateFunc):
    def _process(self, template):
        return self.remove_files

    def remove_files(self, filtered_group: iter, **kwargs) -> list:
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


class ActionAppendLink(ActionAppendCreateFunc):
    def _process(self, template):
        return self.hardlink_files

    def hardlink_files(self, filtered_group: iter, **kwargs) -> list:
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
            elif len(mergedir_flag) == 3:
                merge_dir, overwrite_flag, condition = mergedir_flag
        else:
            merge_dir = mergedir_flag
            condition = None
            overwrite_flag = None

        if os.path.exists(merge_dir):
            print(IsADirectoryError)
            exit()
        else:
            os.makedirs(merge_dir)

        if overwrite_flag is not None and overwrite_flag.upper() == 'CONDITION':
            assert condition is not None

        if overwrite_flag.upper() in overwrite_flags:
            overwrite_method = overwrite_flags[overwrite_flag.upper()]
        else:
            overwrite_method = self._count

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

        moved_files = list()

        for file in filter_group:
            filename = os.path.split(file)[1]
            filename_split = filename.split('.')
            if os.path.exists(os.path.join(filter_dir, filename)):
                count = '0001'
                dest_dir = filter_dir
                dest_file = os.path.join(filename_split[0] + "_{}.".format(count) + filename_split[1])
                dest_dir_file = os.path.join(dest_dir, dest_file)
                while os.path.exists(dest_dir_file):
                    print(dest_dir_file)
                    count = incr_count(count)
                    dest_file = os.path.join(filename_split[0] + "_{}.".format(count) + filename_split[1])
                shutil.copy(file, dest_dir_file)
                moved_files.append(dest_dir_file)
            else:
                dest_dir_file = os.path.join(filter_dir, filename)
                shutil.copy(file, dest_dir_file)
                moved_files.append(dest_dir_file + '\n')

        return moved_files


    def _ignore(self, filter_dir, filter_group):
        moved_files = list()

        for file in filter_group:
            filename = os.path.split(file)[1]
            if os.path.exists(os.path.join(filter_dir, filename)):
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
                    shutil.copy(file, dest_dir_file)
            else:
                dest_dir_file = os.path.join(filter_dir, filename)
                shutil.copy(file, dest_dir_file)
                moved_files.append(dest_dir_file + '\n')

        return moved_files
        pass
