import subprocess
from functools import partial
import argparse
import shlex
import string
import os

from pathlib import Path
from argparse import _ensure_value, _copy


class ActionShell(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        items = _copy.copy(_ensure_value(namespace, self.dest, []))
        if isinstance(values, (list, tuple)):
            for template in values:
                template = template.replace("{}", "{0}")
                template_format = format_template(template)
                shell_command = partial(invoke_shell, command=template_format)
                items.append(shell_command)
        else:
            template = values
            template_format = TemplateFunc(template)
            shell_command = partial(invoke_shell, command=template_format)
            items.append(shell_command)

        setattr(namespace, self.dest, items)

    def _process(self, template):
        template_format = Template(template)
        shell_command = partial(invoke_shell, command=template_format)
        return shell_command


def format_template(template):
    def wrapper(*args, **kwargs):
        template_func = template.format(*args, **kwargs)
        return template_func
    return wrapper


def invoke_shell(*args, command, **kwargs) -> str:
    args = (shlex.quote(arg) for arg in args)
    try:
        output = subprocess.check_output(command(*args, **kwargs), shell=True).decode('utf8')
    except subprocess.CalledProcessError as e:
        print("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        return ''
    return output


class TemplateFunc(string.Formatter):
    def __init__(self, template):
        self.template = template

        for key, alias in self.aliases.items():
            self.template = self.template.replace(key, alias)

    aliases = {
        "{}": "{0:s}",
        "{.}": "{0:a}",
        "{/}": "{0:b}",
        "{//}": "{0:c}",
        "{/.}": "{0:e}",
        "{..}": "{0:f}",
    }

    def __call__(self, *args, **kwargs):
        return self.format(self.template, *args, **kwargs)

    def format_field(self, value, spec):
        '''
            Based on parallel notation including
            {}  : filename
            {.} : filename with extension removed
            {/} : basename of filename
            {//}: dirname of file
            {/.}: dirname of file with extension removed
        '''

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


