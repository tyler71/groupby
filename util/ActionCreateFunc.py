import os
import shlex
import subprocess
from functools import partial

from util.Templates import ActionAppendCreateFunc
from util.Templates import StringExpansionFunc


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
        flag = template
        self.overwrite_flags = {
            "COUNT": self._count,
            "IGNORE": self._ignore,
            "ERROR": self._error,
            "CONDITION": self._condition,
        }
        if ":" in flag:
            flag = flag.split(":")
            if len(flag) == 2:
                merge_dir, overwrite_flag = flag
            elif len(flag) == 3:
                merge_dir, overwrite_flag, condition = flag
        else:
            merge_dir = flag
            condition = None
            overwrite_flag = None

        callable_ = partial(self._abstract_call,
                            condition=condition,
                            merge_dir=merge_dir,
                            overwrite_flag=overwrite_flag)
        return callable_

    def _abstract_call(self, filtered_group, *, condition, merge_dir, overwrite_flag, **kwargs):
        overwrite = self.overwrite_flags.get(overwrite_flag, self._count)
        if overwrite_flag is not None and overwrite_flag.upper() == 'CONDITION':
            assert condition is not None

        self.filter_dir = os.path.join(merge_dir, *kwargs.values())
        if not os.path.exists(merge_dir):
            os.makedirs(merge_dir)
        if len(os.listdir(merge_dir)) == 0:
            os.makedirs(self.filter_dir)
            output = overwrite(condition, self.filter_dir, filter_group=filtered_group)
            return output

    def _count(self, filter_group, filter_dir):
        # This keeps the left padding of 0's
        def incr_count(count):
            return str(int(count) + 1).zfill(len(count))

        moved_files = list()

        for file in filter_group:
            filename = os.path.splitext(file)[1]
            filename_split = filename.split('.')
            if os.path.exists(self.filter_dir + filename):
                count = '0000'
                while os.path.exists(os.path.join(self.filter_dir, filename_split[0], count, filename[1])):
                    count = incr_count(count)
                moved_files.append(os.path.join(self.filter_dir, filename_split[0], count, filename[1]))
            else:
                moved_files.append(self.filter_dir + filename)

        return moved_files


    def _ignore(self, filter_group):
        pass

    def _error(self, filter_group):
        pass

    def _condition(self, filter_group, *, condition):
        pass
