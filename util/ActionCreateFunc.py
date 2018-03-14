import datetime
import logging
import os
import shutil
from functools import partial

from util.Templates import ActionAppendCreateFunc
from util.Templates import EscapedBraceExpansion
from util.Templates import invoke_shell
from util.Templates import sanitize_string

log = logging.getLogger(__name__)


def print_results(filtered_group, *, basic_formatting=False, **labeled_filters):
    log.info(' -> '.join(sanitize_string(filter_output) for filter_output in labeled_filters.values()))
    if basic_formatting is True:
        output = (sanitize_string(grp)
                  for grp in filtered_group)
    else:
        output = list()
        first_filename, *group = filtered_group
        output.append(sanitize_string(first_filename) + '\n')
        if len(group) > 0:
            for filename in group:
                padding = len(sanitize_string(filename)) + 4
                output.append(sanitize_string(filename).rjust(padding) + '\n')
    return output


class ActionAppendExecShell(ActionAppendCreateFunc):
    def _process(self, template):
        template_format = EscapedBraceExpansion(template)

        shell_command = partial(self._group_invoke_shell, command=template_format)
        return shell_command

    def _group_invoke_shell(self, filtered_group, command, **kwargs):
        command_outputs = list()
        for file in filtered_group:
            output = invoke_shell(file, command=command, **kwargs)
            command_outputs.append(output)
        return command_outputs


def remove_files(filtered_group: iter, **kwargs) -> list:
    removed_files = list()
    for filename in filtered_group:
        try:
            pass
            removed_files.append("Removing {file}\n".format(file=filename))
            # os.remove(filename)
            # removed_files.append(filename)
        except FileNotFoundError:
            log.warning("Not Found")
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
            log.warning("Not Found")
    return linked_files


class ActionAppendMerge(ActionAppendCreateFunc):
    def _process(self, template):
        mergedir_flag = template
        overwrite_flags = {
            "COUNT": self._count,
            "IGNORE": self._ignore,
            "ERROR": self._error,

            "LARGER": partial(self._condition, condition='LARGER'),
            "SMALLER": partial(self._condition, condition='SMALLER'),
            "NEWER": partial(self._condition, condition='NEWER'),
            "OLDER": partial(self._condition, condition='OLDER'),
        }

        if ":" in mergedir_flag:
            mergedir_flag = mergedir_flag.split(":")
            if len(mergedir_flag) == 2:
                merge_dir, overwrite_flag = mergedir_flag
        else:
            merge_dir = mergedir_flag
            overwrite_flag = None

        if overwrite_flag is not None:
            try:
                overwrite_method = overwrite_flags[overwrite_flag.upper()]
            except KeyError as e:
                log.error('{} is not a valid key'.format(e))
                exit(1)
        else:
            overwrite_method = self._count

        if os.path.exists(merge_dir):
            raise IsADirectoryError("{} already exists".format(merge_dir))
        else:
            os.makedirs(merge_dir)

        callable_ = partial(self._abstract_call,
                            merge_dir=merge_dir,
                            overwrite_method=overwrite_method)
        return callable_

    def _abstract_call(self, filtered_group, *, merge_dir, overwrite_method, **kwargs):
        filter_dir = os.path.join(merge_dir, *kwargs.values())
        os.makedirs(filter_dir)
        output = overwrite_method(filter_dir, filter_group=filtered_group)
        return output

    def _count(self, filter_dir, filter_group):
        # This keeps the left padding of 0's
        def incr_count(count):
            return str(int(count) + 1).zfill(len(count))

        def create_file_path(dir_, filename, count=None, fileext=None):
            if count is not None:
                filename = '_'.join([filename, count])
            if fileext is not None:
                filename = ''.join([filename + fileext])
            dest_dir_file = os.path.join(dir_, filename)
            return dest_dir_file

        for file in filter_group:
            filename = os.path.split(file)[1]
            filename_split = os.path.splitext(filename)

            dest_dir_file = os.path.join(filter_dir, filename)
            if os.path.exists(dest_dir_file):
                count = '0000'
                dest_dir = filter_dir
                dest_dir_file = create_file_path(dest_dir, filename)
                while os.path.exists(dest_dir_file):
                    count = incr_count(count)
                    if filename_split[1] == '':
                        dest_file = os.path.join(filename_split[0] + "_{}".format(count))
                    else:
                        dest_file = os.path.join(filename_split[0] + "_{}".format(count) + filename_split[1])
                    dest_dir_file = os.path.join(dest_dir, dest_file)
                log.info('Incrementing {} to {}'.format(sanitize_string(filename),
                                                        dest_file))
                shutil.copy(file, dest_dir_file)
                yield sanitize_string(dest_dir_file) + '\n'
            else:
                dest_dir_file = os.path.join(filter_dir, filename)
                shutil.copy(file, dest_dir_file)
                yield sanitize_string(dest_dir_file) + '\n'

    def _ignore(self, filter_dir, filter_group):

        for file in filter_group:
            filename = os.path.split(file)[1]
            dest_file = os.path.join(filter_dir, filename)
            if os.path.exists(dest_file):
                msg = "{} Exists, Ignoring {}".format(
                    sanitize_string(dest_file),
                    sanitize_string(file))
                log.info(msg)
                continue
            else:
                dest_dir_file = os.path.join(filter_dir, filename)
                shutil.copy(file, dest_dir_file)
                yield sanitize_string(dest_dir_file) + '\n'

    def _error(self, filter_dir, filter_group):
        for file in filter_group:
            filename = os.path.split(file)[1]
            dest_dir_file = os.path.join(filter_dir, filename)
            if os.path.exists(dest_dir_file):
                log.error('{} already exists, exiting'.format(sanitize_string(dest_dir_file)))
                exit(1)
            else:
                dest_dir_file = os.path.join(filter_dir, filename)
                shutil.copy(file, dest_dir_file)
                yield sanitize_string(dest_dir_file) + '\n'

    def _condition(self, filter_dir, filter_group, *, condition=None):
        assert condition is not None

        def modification_date(filename: str) -> str:
            modification_time = os.path.getmtime(filename)
            modified_datetime = datetime.datetime.fromtimestamp(modification_time)
            return str(modified_datetime)

        def disk_size(filename: str) -> str:
            byte_usage = os.path.getsize(filename)
            return str(byte_usage)

        conditions = {
            'LARGER' : lambda file1, file2: disk_size(file1) > disk_size(file2),
            'SMALLER': lambda file1, file2: disk_size(file1) < disk_size(file2),
            'NEWER'  : lambda file1, file2: modification_date(file1) < modification_date(file2),
            'OLDER'  : lambda file1, file2: modification_date(file1) > modification_date(file2),
        }
        condition = conditions[condition.upper()]

        for file in filter_group:
            filename = os.path.split(file)[1]
            dest_dir_file = os.path.join(filter_dir, filename)
            if os.path.exists(dest_dir_file):
                if condition(file, dest_dir_file):
                    log.info("{} overwriting {}".format(sanitize_string(file),
                                                        sanitize_string(dest_dir_file)))
                    shutil.copy(file, dest_dir_file)
                    yield sanitize_string(dest_dir_file) + '\n'
            else:
                dest_dir_file = os.path.join(filter_dir, filename)
                shutil.copy(file, dest_dir_file)
                yield sanitize_string(dest_dir_file) + '\n'


