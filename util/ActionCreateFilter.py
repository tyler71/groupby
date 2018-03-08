import os
import re
import shlex
import subprocess
from collections import OrderedDict
from functools import partial

from util.Templates import ActionAppendCreateFunc, StringExpansionFunc

# This matches a newline, a space, tab, return character OR a null value: between the | and )
_whitespace = re.compile('^([\n \t\r]|)+$')


class OrderedDefaultListDict(OrderedDict):
    def __missing__(self, key):
        self[key] = value = []
        return value


class ActionAppendShellFilter(ActionAppendCreateFunc):
    def _process(self, template):
        template_format = StringExpansionFunc(template)
        shell_command = partial(self._invoke_shell, command=template_format)
        return shell_command

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


class ActionAppendRegexFilter(ActionAppendCreateFunc):
    def _process(self, template):
        template = re.compile(template)
        regex_pattern = partial(self._re_match, pattern=template)
        return regex_pattern

    def _re_match(self, filename, *, pattern) -> str:
        split_file = os.path.split(filename)[1]
        quoted_dir = shlex.quote(split_file)

        result = pattern.search(quoted_dir)
        return result.group() if result else ""


class ActionAppendFilePropertyFilter(ActionAppendCreateFunc):
    def _process(self, template):
        filters = OrderedDict(
            {
                "partial_md5": self.partial_md5_sum,
                "md5": self.md5_sum,
                "sha256": self.sha256_sum,
                "modified": self.modification_date,
                "accessed": self.access_date,
                "size": self.disk_size,
                "filename": self.file_name,
                "file": self.direct_compare,
            }
        )
        func_name = template
        return filters[func_name]

    # Used with checksum functions
    def _iter_read(filename: str, chunk_size=65536) -> bytes:
        with open(filename, 'rb') as file:
            for chunk in iter(lambda: file.read(chunk_size), b''):
                yield chunk

    @staticmethod
    def access_date(filename: str) -> str:
        access_time = os.path.getmtime(filename)
        access_datetime = datetime.datetime.fromtimestamp(access_time)
        return str(access_datetime)

    @staticmethod
    def modification_date(filename: str) -> str:
        modification_time = os.path.getmtime(filename)
        modified_datetime = datetime.datetime.fromtimestamp(modification_time)
        return str(modified_datetime)
    @staticmethod
    def file_name(filename: str) -> str:
        file_basename = os.path.basename(filename)
        return str(file_basename)

    @staticmethod
    def disk_size(filename: str, *args) -> str:
        byte_usage = os.path.getsize(filename)
        return str(byte_usage)

    def md5_sum(filename, chunk_size=65536) -> str:
        checksumer = hashlib.md5()
        for chunk in ActionAppendFilePropertyFilter._iter_read(filename, chunk_size):
            checksumer.update(chunk)
        file_hash = checksumer.hexdigest()
        return str(file_hash)

    @staticmethod
    def sha256_sum(filename, chunk_size=65536) -> str:
        checksumer = hashlib.sha256()
        for chunk in ActionAppendFilePropertyFilter._iter_read(filename, chunk_size):
            checksumer.update(chunk)
        file_hash = checksumer.hexdigest()
        return str(file_hash)

    @staticmethod
    def partial_md5_sum(filename, chunk_size=65536, chunks_read=200) -> str:
        checksumer = hashlib.md5()
        with open(filename, 'rb') as file:
            for null in range(0, chunks_read):
                chunk = file.read(chunk_size)
                if chunk == b'':
                    break
                checksumer.update(chunk)
        return checksumer.hexdigest()

    @staticmethod
    def direct_compare(filename) -> bytes:
        with open(filename, 'rb') as file:
            data = file.read()
        return data


class DuplicateFilters:
    def __init__(self, *, filters, filenames, conditions=None):
        self.filters = filters
        self.filenames = filenames
        self.filter_hashes = list()
        if conditions is None:
            self.conditions = list()
        else:
            self.conditions = conditions

    def __iter__(self):
        return self.process()

    def process(self):
        initial_filter, *other_filters = self.filters
        results = self._first_filter(initial_filter, self.filenames, conditions=self.conditions)
        for additional_filter in other_filters:
            results = self._additional_filters(additional_filter, results)
        for group_list in results:
            yield group_list

    def _first_filter(self, func, paths, conditions):
        grouped_groups = OrderedDefaultListDict()
        for path in paths:
            if all(condition(path) for condition in conditions):
                item_hash = func(path).strip()
                if len(item_hash) < 10 and _whitespace.match(str(item_hash)):
                    # Just a newline means no output
                    continue
                grouped_groups[item_hash].append(path)
        for key, group in grouped_groups.items():
            if len(group) > 0:
                # key is appended enclosed in a list to group it, allowing other filters to also append to that
                # specific group
                self.filter_hashes.append([key])
                yield group

    def _additional_filters(self, func, groups):
        index = 0
        for group_list in groups:
            unmatched_groups = OrderedDefaultListDict()
            filtered_groups = list()
            if len(group_list) > 0:
                first, *others = group_list
                filtered_groups.append(first)
                source_hash = func(first).strip()

                # For each additional filter, append the source hash to the filter_hashes, allowing
                # a user to use the results as part of a command
                self.filter_hashes[index].append(source_hash)

                for item in others:
                    item_hash = func(item).strip()

                    # If matching _whitespace, continue since it shouldn't be considered a valid
                    # output, however will only check for values less then 10 (for performance)
                    if len(item_hash) < 10 and _whitespace.match(str(item_hash)):
                        continue

                    # If this item matches the source, include it in the list to be returned.
                    if item_hash == source_hash:
                        filtered_groups.append(item)
                    else:
                        unmatched_groups[item_hash].append(item)

            yield filtered_groups
            # Calls itself on all unmatched groups
            if unmatched_groups:
                previous_filter_track = self.filter_hashes[index][0:-1]
                for item_hash, unmatched_group in unmatched_groups.items():
                    # key is appended enclosed in a list to group it, allowing other filters to also append to that
                    # specific group
                    index += 1
                    self.filter_hashes.insert(index, previous_filter_track + [item_hash])
                    yield unmatched_group

            index += 1


if __name__ == '__main__':
    print(md5_sum("tests/file_properties/hash"))
    print(partial_md5_sum("tests/file_properties/hash"))
    print(sha256_sum("tests/file_properties/hash"))

    print(disk_size("tests/file_properties/5120_byte"))
    print(modification_date("tests/file_properties/5120_byte"))
