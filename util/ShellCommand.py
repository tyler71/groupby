import subprocess
from functools import partial
import argparse
import shlex

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


def format_template(template):
    def wrapper(*args, **kwargs):
        template_func = template.format(*args, **kwargs)
        return template_func
    return wrapper


def invoke_shell(*args, command, **kwargs) -> str:
    args = [shlex.quote(arg) for arg in args]
    try:
        output = subprocess.check_output(command(*args, **kwargs), shell=True).decode('utf8')
    except subprocess.CalledProcessError as e:
        print("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        return ''
    return output.strip()
