import subprocess
from functools import partial
import argparse
import shlex

from argparse import _ensure_value, _copy


class ActionShell(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        items = _copy.copy(_ensure_value(namespace, self.dest, []))
        if isinstance(values, list):
            for template in values:
                shell_command = convert_to_shell(invoke_shell, template)
                items.append(shell_command)
        else:
            template = values
            shell_command = convert_to_shell(invoke_shell, template)
            items.append(shell_command)

        setattr(namespace, self.dest, items)

def convert_to_shell(func, template):
    def wrapper(*args, **kwargs):
        template_func = template.format(*args, **kwargs)
        shell_command = partial(func, command=template_func)
        return shell_command
    return wrapper


def invoke_shell(filename: str, *, command,) -> str:
    quoted_filename = shlex.quote(filename)
    try:
        output = subprocess.check_output(command(quoted_filename), shell=True).decode('utf8')
    except subprocess.CalledProcessError as e:
        print("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        return b''
    return output.strip()
