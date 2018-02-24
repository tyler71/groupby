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
                template_func = lambda filename: template.format(filename)
                #shell_command = partial(invoke_shell, command=template_func)
                items.append(template)
        else:
            template = values
            template_func = lambda filename: template.format(filename)
            #shell_command = partial(invoke_shell, command=template_func)
            items.append(template)

        setattr(namespace, self.dest, items)


def invoke_shell(filename: str, *, command,) -> str:
    quoted_filename = shlex.quote(filename)
    try:
        output = subprocess.check_output(command(quoted_filename), shell=True).decode('utf8')
        print(output)
    except subprocess.CalledProcessError as e:
        print("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        return b''
    return output.strip()
