import argparse
import codecs
import logging
import os
import shlex
import string
import subprocess
import sys

log = logging.getLogger(__name__)


# This inherits the action="append" of argparse
# It takes a argument of template which should be a string
# and passes it to _process which should return a function will be called
# with a filename.
class ActionAppendCreateFunc(argparse._AppendAction):
    # Internal logic for AppendAction
    def __call__(self, parser, namespace, values, option_string=None):
        # Trigger when nargs a list
        if isinstance(values, (list, tuple)):
            values_list = list()
            for template in values:
                template = codecs.escape_decode(bytes(template, "utf-8"))[0].decode("utf-8")
                callable_ = self._process(template)
                values_list.append(callable_)
            values = values_list
        else:
            template = values
            # All subclasses should return a callable when called with _process
            # Whatever that is
            template = codecs.escape_decode(bytes(template, "utf-8"))[0].decode("utf-8")
            callable_ = self._process(template)
            values = callable_
        super().__call__(parser, namespace, values, option_string)

    def _process(self, template):
        # should take a template
        # and return a function allowing it to be called with a string
        raise (ValueError, "Expected to be extended in subclass")


# This overrides the .format string, to allow for greater control of how .format works
# Additional formats can be specified with a new letter of spec
class BraceExpansion(string.Formatter):
    '''
        Based on parallel notation including
        {}  : filename
        {.} : filename with extension removed
        {/} : basename of filename
        {//}: dirname of file
        {/.}: dirname of file with extension removed
    '''

    def __init__(self, template):
        self.template = template
        self.aliases = {
            "{}": "{0:z}",
            "{.}": "{0:a}",
            "{/}": "{0:b}",
            "{//}": "{0:c}",
            "{/.}": "{0:e}",
            "{..}": "{0:f}",
        }

        for key, alias in self.aliases.items():
            self.template = self.template.replace(key, alias)

    def __call__(self, *args, **kwargs):
        return self.format(self.template, *args, **kwargs)

    def format_field(self, value, spec):
        # {} notation: normal output
        if spec.endswith("z"):
            value = value
            spec = spec[:-1] + 's'
        # {.} notation: extension removed
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


class EscapedBraceExpansion(BraceExpansion):
    def __init__(self, template):
        super().__init__(template)

    def format_field(self, value, spec):
        value = super().format_field(value, spec)
        value = shlex.quote(value)
        return value


def invoke_shell(*args, command, **labled_filters) -> str:
    shell_escaped_labeled_filters = {key: shlex.quote(value)
                                     for key, value in labled_filters.items()}
    try:
        output = subprocess.check_output(command(*args, **shell_escaped_labeled_filters), shell=True)
    except subprocess.CalledProcessError as e:
        msg = 'Command: "{cmd}" generated a code [{code}]\n' \
              'Output: {output}'
        log.error(msg.format(cmd=sanitize_string(e.cmd),
                             code=e.returncode,
                             output=sanitize_string(e.output)))
        exit(1)
    except KeyError as e:
        log.error("Filter {}, not found".format(e))
        exit(1)
    return output


def sanitize_string(msg):
    encode_type = sys.getfilesystemencoding()
    if isinstance(msg, str):
        msg = msg.encode(encode_type, errors='replace')
        msg = msg.decode(encode_type)
    elif isinstance(msg, bytes):
        msg = msg.decode(encode_type, errors='replace')
    return msg


def negation(func):
    def wrapper(*args, **kwargs):
        return not func(*args, **kwargs)
    return wrapper
