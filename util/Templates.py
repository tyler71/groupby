import argparse
import datetime
import hashlib
import os
import string
from collections import OrderedDict


# This inherits the action="append" of argparse
# It takes a argument of template which should be a string
# and passes it to _process which should return a function will be called
# with a filename.
class ActionAppendCreateFunc(argparse._AppendAction):
    # Internal logic for AppendAction
    def __call__(self, parser, namespace, values, option_string=None):
        _copy = argparse._copy
        _ensure_value = argparse._ensure_value

        items = _copy.copy(_ensure_value(namespace, self.dest, []))

    # / Internal Logic
        # Trigger when nargs a list
        if isinstance(values, (list, tuple)):
            for template in values:
                callable_ = self._process(template)
                items.append(callable_)
        else:
            template = values
            # All subclasses should return a callable when called with _process
            # Whatever that is
            callable_ = self._process(template)
            items.append(callable_)

        setattr(namespace, self.dest, items)

    def _process(self, template):
        # should take a template
        # and return a function allowing it to be called with a string
        raise (ValueError, "Expected to be extended in subclass")


# This overrides the .format string, to allow for greater control of how .format works
# Additional formats can be specified with a new letter of spec
class StringExpansionFunc(string.Formatter):
    '''
        Based on parallel notation including
        {}  : filename
        {.} : filename with extension removed
        {/} : basename of filename
        {//}: dirname of file
        {/.}: dirname of file with extension removed
    '''

    aliases = {
        "{}": "{0:s}",
        "{.}": "{0:a}",
        "{/}": "{0:b}",
        "{//}": "{0:c}",
        "{/.}": "{0:e}",
        "{..}": "{0:f}",
    }

    def __init__(self, template):
        self.template = template
        self.aliases = StringExpansionFunc.aliases

        for key, alias in self.aliases.items():
            self.template = self.template.replace(key, alias)

    def __call__(self, *args, **kwargs):
        return self.format(self.template, *args, **kwargs)

    def format_field(self, value, spec):

        if spec.endswith("a"):
            split_ext = os.path.splitext(value)
            value_no_ext = split_ext[0]
            value = value_no_ext
            spec = spec[:-1] + 's'
        # {/} notation: basename of list()file
        if spec.endswith("b"):
            split_filename = os.path.split(value)[1]
            value = split_filename
            spec = spec[:-1] + 's'
        # {//} notation: directory of filename)
        if spec.endswith("c"):
            split_dir = os.path.split(value)[0]
            value = split_dir
            spec = spec[:-1] + 's'
        # {/.} notation: basename of file, with ext removed
        if spec.endswith("e"):
            no_dir = os.path.split(value)[1]
            split_ext = os.path.splitext(no_dir)[0]
            value = split_ext
            spec = spec[:-1] + 's'
        # {..} expanded notation: extension of file
        if spec.endswith("f"):
            ext = os.path.splitext(value)[1]
            value = ext
            spec = spec[:-1] + 's'
        return super().format_field(value, spec)


class FileProperties:

    def __init__(self):
        self.filters = OrderedDict(
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

    def __call__(self, func_name):
        return self.filters[func_name]

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


    @staticmethod
    def md5_sum(filename, chunk_size=65536) -> str:
        checksumer = hashlib.md5()
        for chunk in FileProperties._iter_read(filename, chunk_size):
            checksumer.update(chunk)
        file_hash = checksumer.hexdigest()
        return str(file_hash)

    @staticmethod
    def sha256_sum(filename, chunk_size=65536) -> str:
        checksumer = hashlib.sha256()
        for chunk in FileProperties._iter_read(filename, chunk_size):
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
