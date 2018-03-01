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
        template = template.replace("{}", "{0}")
        template = template.replace("{.}", "{:no_ext}")
        template = template.replace("{/}", "{:basename}")
        template = template.replace("{//}", "{:dir_path}")
        template = template.replace("{/.}", "{:no_dir_ext}")
        template = template.replace("{..}", "{:only_ext}")
        template_format = Template(template)
        shell_command = partial(invoke_shell, command=template_format)
        return shell_command


class TemplateFunc(string.Formatter):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        pass

    def format_field(self, value, spec):
        # {.} notation: Remove file extension
        if spec.endswith("no_ext"):
            split_ext = os.path.splitext(value)
            value_no_ext = split_ext[0]
            value = value_no_ext
        # {/} notation: basename of list()file
        if spec.endswith("basename"):
            split_filename = os.path.split(value)[1]
            value = split_filename
        # {//} notation: directory of filename)
        if spec.endswith("dirname"):
            split_dir = os.path.split(value)[0]
            value = split_dir
        # {/.} notation: basename of file, with extentest removed
        if spec == "no_ext_dir":
            no_dir =  os.path.split(value)[1]
            split_ext = os.path.splitext(no_dir)[0]
            value = split_ext
        # {..} notation: test extension of file
        if spec.endswith("only_ext"):
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
