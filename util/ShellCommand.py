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
            template = template.replace("{}", "{0}")
            template_format = format_template(template)
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

class TemplateFunc(string.Formatter):
    def __init__(self, template):
        self.template = template
        self.template = template.replace("{}", "{0}")
        self.template = template.replace("{.}", "{:a}")
        self.template = template.replace("{/}", "{:b}")
        self.template = template.replace("{//}", "{:c}")
        self.template = template.replace("{/.}", "{:e}")
        self.template = template.replace("{..}", "{:f}")

    def __call__(self, *args, **kwargs):
        pass

    def format_field(self, value, spec):
        # {.} notation: Remove file extension
        if spec.endswith("a"):
            split_ext = os.path.splitext(value)
            value_no_ext = split_ext[0]
            value = value_no_ext
        # {/} notation: basename of list()file
        if spec.endswith("b"):
            split_filename = os.path.split(value)[1]
            value = split_filename
        # {//} notation: directory of filename)
        if spec.endswith("c"):
            split_dir = os.path.split(value)[0]
            value = split_dir
        # {/.} notation: basename of file, with extentest removed
        if spec == "e":
            no_dir =  os.path.split(value)[1]
            split_ext = os.path.splitext(no_dir)[0]
            value = split_ext
        # {..} notation: test extension of file
        if spec.endswith("f"):
            ext = os.path.splitext(value)[1]
            value = ext
        return value, spec


def invoke_shell(*args, command, **kwargs) -> str:
    args = [shlex.quote(arg) for arg in args]
    try:
        output = subprocess.check_output(command(*args, **kwargs), shell=True).decode('utf8')
    except subprocess.CalledProcessError as e:
        print("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        return ''
    return output.strip()
