import datetime
import hashlib
import logging
import math
import os
import re
from collections import OrderedDict
from collections import defaultdict
from functools import partial

from util.Templates import ActionAppendCreateFunc, \
    EscapedBraceExpansion
from util.Templates import invoke_shell

# This matches a newline, a space, tab, return character OR a null value: between the | and )
_whitespace = re.compile('^([\n \t\r]|)+$')

log = logging.getLogger(__name__)


class ActionSelectFilter(ActionAppendCreateFunc):
    def _process(self, template):
        self.filters = ActionAppendFilePropertyFilter.filters()
        self.aliases = EscapedBraceExpansion.aliases()
        selected_filter = self.check_filter_type(template)
        return selected_filter

    def check_filter_type(self, template):
        if ":" in template:
            filter_check = template.split(":", 1)[0]
        else:
            filter_check = template
        if filter_check in self.filters:

            return ActionAppendFilePropertyFilter._process(template)
        elif any((alias in template
                  for alias in self.aliases.keys())):
            return ActionAppendShellFilter._process(template)
        else:
            msg = "{filter} is not a valid filter"
            print(msg.format(filter=template))
            exit(1)


class OrderedDefaultListDict(OrderedDict):
    def __missing__(self, key):
        self[key] = value = []
        return value


class ActionAppendShellFilter(ActionAppendCreateFunc):
    @staticmethod
    def _process(template):
        template_format = EscapedBraceExpansion(template)
        shell_command = partial(invoke_shell, command=template_format)
        return shell_command


class ActionAppendFilePropertyFilter(ActionAppendCreateFunc):
    @classmethod
    def filters(cls):
        filters = OrderedDict(
            {
                "partial_md5": cls.partial_md5_sum,
                "md5"        : cls.md5_sum,
                "sha"        : cls.sha_sum,
                "modified"   : cls.modification_date,
                "accessed"   : cls.access_date,
                "size"       : cls.disk_size,
                "filename"   : cls.file_name,
                "file"       : cls.direct_compare,
            }
        )
        return filters

    @classmethod
    def _process(cls, template):
        if ":" in template:
            func_name, abstraction = template.split(":", 1)
            func_name = cls.filters()[func_name]
            filter_func = partial(func_name, abstraction=abstraction)
        else:
            func_name = template
            filter_func = cls.filters()[func_name]

        return filter_func

    # https://stackoverflow.com/a/14822210
    @classmethod
    def _size_round(cls, size_bytes, abstraction=None):
        aliases = cls.aliases("size_round")
        abstraction = abstraction.upper()
        size_pow = OrderedDict([("B", 0), ("KB", 1), ("MB", 2), ("GB", 3), ("TB", 4), ("PB", 5)])
        if size_bytes == 0:
            return "0{}".format(aliases[abstraction])
        try:
            power_level = size_pow[aliases[abstraction]]
        except KeyError as e:
            log.error("Modifier {} is not valid".format(e))
            # Set used to remove duplicate values
            print("Valid Keys:", *size_pow.keys(), sep='\n  ')
            exit(1)

        p = math.pow(1024, power_level)
        s = round(size_bytes / p, 0)

        # Convert to integer
        real_number = int(s)
        output = "{}{}".format(real_number, aliases[abstraction])
        return output

    @classmethod
    def _filename_round(cls, filename, abstraction=None):
        def re_match(filename, *, pattern) -> str:
            assert isinstance(pattern, re._pattern_type)
            split_filename = os.path.split(filename)[1]

            # If capture groups are used, use them,
            # otherwise return the entire matched expression
            result = pattern.search(split_filename)
            if result and result.groups():
                return ''.join(result.groups())
            elif result and result.group():
                return result.group()
            else:
                return ''

        try:
            expr = re.compile(abstraction)
        except Exception as e:
            err_msg = 'Regex "{expr}" generated this error\n{err}'
            log.error(err_msg.format(expr=expr, err=e))
            exit(1)
        regex_pattern = re_match(filename, pattern=expr)
        return regex_pattern

    @classmethod
    def _datetime_round(cls, datetime_, abstraction=None):
        aliases = cls.aliases("datetime_round")
        rounding_level = {
            'MICRO'  : lambda dt: dt.replace(microsecond=0),
            'SECOND' : lambda dt: dt.replace(microsecond=0),
            'MINUTE' : lambda dt: dt.replace(microsecond=0, second=0),
            'HOUR'   : lambda dt: dt.replace(microsecond=0, second=0, minute=0),
            'DAY'    : lambda dt: dt.replace(microsecond=0, second=0, minute=0, hour=0),
            'MONTH'  : lambda dt: dt.replace(microsecond=0, second=0, minute=0, hour=0, day=1),
            'YEAR'   : lambda dt: dt.replace(microsecond=0, second=0, minute=0, hour=0, day=1, month=1),
            'WEEKDAY': lambda dt: dt.replace(microsecond=0, second=0, minute=0, hour=0).weekday(),
        }
        try:
            abstraction = aliases[abstraction.upper()]
        except KeyError as e:
            log.error("Modifier {} is not valid".format(e))
            # Set used to remove duplicate values
            print("Valid Keys:", *sorted(set(aliases.values())), sep='\n  ')
            exit(1)
        rounded_datetime = rounding_level[abstraction](datetime_)
        return rounded_datetime

    # Used with checksum functions to reduce memory footprint
    @classmethod
    def _iter_read(cls, filename: str, chunk_size=65536) -> bytes:
        with open(filename, 'rb') as file:
            for chunk in iter(lambda: file.read(chunk_size), b''):
                yield chunk

    @classmethod
    def access_date(cls, filename: str, *, abstraction=None) -> str:
        access_time = os.path.getmtime(filename)
        access_datetime = datetime.datetime.fromtimestamp(access_time)
        if abstraction is not None:
            access_datetime = cls._datetime_round(access_datetime, abstraction)
        spaces_converted = str(access_datetime).replace(' ', '_')
        return str(spaces_converted)

    @classmethod
    def modification_date(cls, filename: str, *, abstraction=None) -> str:
        modification_time = os.path.getmtime(filename)
        modified_datetime = datetime.datetime.fromtimestamp(modification_time)
        if abstraction is not None:
            modified_datetime = cls._datetime_round(modified_datetime, abstraction)
        spaces_converted = str(modified_datetime).replace(' ', '_')
        return str(spaces_converted)

    @classmethod
    def file_name(cls, filename: str, *, abstraction=None) -> str:
        file_basename = os.path.basename(filename)
        if abstraction is not None:
            file_basename = cls._filename_round(filename, abstraction=abstraction)
        return str(file_basename)

    @classmethod
    def disk_size(cls, filename: str, *, abstraction=None) -> str:
        byte_usage = os.path.getsize(filename)
        if abstraction is not None:
            byte_usage = cls._size_round(byte_usage, abstraction=abstraction)
        return str(byte_usage)

    @classmethod
    def md5_sum(cls, filename, *, chunk_size=65536) -> str:
        checksumer = hashlib.md5()
        for chunk in cls._iter_read(filename, chunk_size):
            checksumer.update(chunk)
        file_hash = checksumer.hexdigest()
        return str(file_hash)

    @classmethod
    def sha_sum(cls, filename, *, chunk_size=65536, abstraction=None) -> str:
        sha_levels = {
            '1': hashlib.sha1,
            '224': hashlib.sha224,
            '256': hashlib.sha256,
            '384': hashlib.sha384,
            '512': hashlib.sha512,
            '3_224': hashlib.sha3_224,
            '3_256': hashlib.sha3_256,
            '3_384': hashlib.sha3_384,
            '3_512': hashlib.sha3_512,
        }
        if abstraction is not None:
            checksumer = sha_levels[abstraction]()
        else:
            checksumer = sha_levels['256']()
        for chunk in cls._iter_read(filename, chunk_size):
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

    @staticmethod
    def aliases(alias_type):
        datetime_round = {
            'NANO'       : 'MICROSECOND',
            'MICROSECOND': 'MICROSECOND',
            'MICRO'      : 'MICROSECOND',

            'S'          : 'SECOND',
            'SEC'        : 'SECOND',
            'SECOND'     : 'SECOND',

            'M'          : 'MINUTE',
            'MIN'        : 'MINUTE',
            'MINUTE'     : 'MINUTE',

            'H'          : 'HOUR',
            'HOUR'       : 'HOUR',

            'D'          : 'DAY',
            'DAY'        : 'DAY',

            'MON'        : 'MONTH',
            'MONTH'      : 'MONTH',

            'YEAR'       : 'YEAR',
            'Y'          : 'YEAR',
            'YR'         : 'YEAR',

            'WEEKDAY'    : 'WEEKDAY',
            'WD'         : 'WEEKDAY',
        }
        size_round = {
            'B': 'B',
            'BYTE': 'B',
            'BYTES': 'B',

            'KB': 'KB',
            'KILO': 'KB',
            'KILOBYTE': 'KB',
            'KILOBYTES': 'KB',

            'MB': 'MB',
            'MEGA': 'MB',
            'MEGABYTE': 'MB',
            'MEGABYTES': 'MB',

            'GB': 'GB',
            'GIGA': 'GB',
            'GIGABYTE': 'GB',
            'GIGABYTES': 'GB',

            'TB': 'TB',
            'TERA': 'TB',
            'TERABYTE': 'TB',
            'TERABYTES': 'TB',

            'PB': 'PB',
            'PETA': 'PB',
            'PETABYTE': 'PB',
            'PETABYTES': 'PB',
        }
        if alias_type == "size_round":
            return size_round
        elif alias_type == "datetime_round":
            return datetime_round


class DuplicateFilters:
    def __init__(self, *, filters, filenames, conditions=None):
        self.filters = filters
        self.filenames = filenames
        self.filter_hashes = defaultdict(list)
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
                self.filter_hashes[path].append(item_hash)
                grouped_groups[item_hash].append(path)
        for key, group in grouped_groups.items():
            if len(group) > 0:
                # key is appended enclosed in a list to group it, allowing other filters to also append to that
                # specific group
                yield group

    def _additional_filters(self, func, groups):
        for group_list in groups:
            unmatched_groups = OrderedDefaultListDict()
            filtered_groups = list()
            if len(group_list) > 0:
                first, *others = group_list
                filtered_groups.append(first)
                source_hash = func(first).strip()
                self.filter_hashes[first].append(source_hash)

                for item in others:
                    item_hash = func(item).strip()

                    # If matching _whitespace, continue since it shouldn't be considered a valid
                    # output, however will only check for values less then 10 (for performance)
                    if len(item_hash) < 10 and _whitespace.match(str(item_hash)):
                        continue

                    self.filter_hashes[item].append(item_hash)
                    # If this item matches the source, include it in the list to be returned.
                    if item_hash == source_hash:
                        filtered_groups.append(item)
                    else:
                        unmatched_groups[item_hash].append(item)

            yield filtered_groups
            # Calls itself on all unmatched groups
            if unmatched_groups:
                for unmatched_group in unmatched_groups.values():
                    log.debug("Subgroup")
                    yield unmatched_group


if __name__ == '__main__':
    pass
