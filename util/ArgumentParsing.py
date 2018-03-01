import argparse
import os
import shlex
import string
import subprocess

from functools import partial

from util.FileProperties import list_filters


def parser_logic(parser):
    available_filters = list_filters()
    parser.add_argument('-f', "--filters",
                        choices=available_filters.keys(),
                        help="Default: size md5",
                        action="append")
    parser.add_argument('-s', '--shell',
                        dest="filters",
                        help="Filenames represented as {}: --shell \"du {} | cut -f1\"",
                        action=ActionShell)
    parser.add_argument('-x', '--exec-group',
                        dest="duplicate_action",
                        help="Filenames represented as {}, filters as {f1}, {fn}...: --exec-group \"echo {} {f1}\"",
                        action=ActionShell)
    parser.add_argument('--remove',
                        dest="duplicate_action",
                        action="append_const",
                        const='remove',
                        help="Remove Duplicates, last flag applies of remove or link ")
    parser.add_argument('--link',
                        dest="duplicate_action",
                        action="append_const",
                        const='link',
                        help="Replaces Duplicates with Hard Links of Source, last flag applies of remove or link")
    parser.add_argument('--include', action='append')
    parser.add_argument('--exclude', action='append')
    parser.add_argument('--dir-include', action='append')
    parser.add_argument('--dir-exclude', action='append')
    parser.add_argument('-r', '--recursive', action='store_true')
    parser.add_argument('-t', '--threshold', type=int, default=1, help="Minimum number of files in each group")
    parser.add_argument("--basic-formatting", action="store_true")
    parser.add_argument("--max-depth", type=int)
    parser.add_argument('--empty-file', action='store_true', help="Allow comparision of empty files")
    parser.add_argument('--follow-symbolic', action='store_true', help="Allow following of symbolic links for compare")
    parser.add_argument('--interactive', action='store_true')
    parser.add_argument('-v', '--verbosity', default=3, action="count")
    parser.add_argument('directories',
                        default=[os.getcwd()],
                        metavar="directory",
                        nargs='*')
    return parser



class ActionShell(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        _copy = argparse._copy
        _ensure_value = argparse._ensure_value

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


