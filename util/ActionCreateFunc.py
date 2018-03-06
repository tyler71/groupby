import os
import subprocess
import shlex

from functools import partial

from util.Templates import ActionAppendCreateFunc
from util.Templates import StringExpansionFunc


# Used as both a filter and a group exec
class ActionAppendShell(ActionAppendCreateFunc):
    def _process(self, template):
        template_format = StringExpansionFunc(template)
        shell_command = partial(self._invoke_shell, command=template_format)
        return shell_command

    def _invoke_shell(self, *args, command, **kwargs) -> str:
        print(args)
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

    def remove_files(self, groupfiles: iter) -> list:
        removed_files = list()
        for group in groupfiles:
            for filename in group:
                print("Removing {file}".format(file=filename))
                try:
                    pass
                    # os.remove(filename)
                    # removed_files.append(filename)
                except FileNotFoundError:
                    print("Not Found")
        return removed_files


class ActionAppendLink(ActionAppendCreateFunc):
    def _process(self, template):
        return self.hardlink_files

    def hardlink_files(self, group_files: iter) -> list:
        linked_files = list()
        for group in group_files:
            source_file = group[0]

            for filename in group:
                print("Linking {source_file} -> {filename}".format(source_file=source_file, filename=filename))
                try:
                    pass
                    # os.remove(filename)
                    # os.link(source_file, filename)
                    linked_files.append((source_file, filename))
                except FileNotFoundError:
                    print("Not Found")
        return linked_files


class ActionAppendMerge(ActionAppendCreateFunc):
    def _process(self, template):
        self.overwrite_flags = {
            "COUNT": self._count,
            "IGNORE": self._ignore,
            "ERROR": self._error,
            "CONDITION": self._condition,
        }
        if ":" in template:
            self.template = template.split(":")
        else:
            self.merge_dir = template
        if len(template) == 2:
            self.merge_dir, self.overwrite_flag = template
        elif len(template) == 3:
            self.merge_dir, self.overwrite_flag, self.condition = template

        return self._abstract_call

    def _abstract_call(self, condition=None, *, merge_dir, overwrite_flag, filter_group, hashes):
        overwrite = self.overwrite_flags[overwrite_flag]
        if overwrite_flag.upper() == 'CONDITION':
            assert condition is not None

        self.filter_dir = os.path.join(merge_dir, *hashes)
        if not os.path.exists(merge_dir):
            os.makedirs(merge_dir)
        if len(os.listdir(merge_dir)) == 0:
            os.makedirs(self.filter_dir)
        overwrite(condition, filter_group=filter_group)

    def _count(self, filter_group):
        # This keeps the left padding of 0's
        def incr_count(count):
            return str(int(count) + 1).zfill(len(count))

        for file in filter_group:
            filename = os.path.splitext(file)[1]
            filename_split = filename.split('.')
            if os.path.exists(self.filter_dir + filename):
                count = '0000'
                while os.path.exists(os.path.join(self.filter_dir, filename_split[0], count, filename[1])):
                    count = incr_count(count)
                print(os.path.join(self.filter_dir, filename_split[0], count, filename[1]))

    def _ignore(self, filter_group):
        pass

    def _error(self, filter_group):
        pass

    def _condition(self, filter_group, *, condition):
        pass
