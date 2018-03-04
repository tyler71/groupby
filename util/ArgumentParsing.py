import os
import re
import shlex
import subprocess

from functools import partial

from util.FileProperties import list_filters
from util.Templates import ActionTemplate, TemplateFunc


def parser_logic(parser):
    available_filters = list_filters()
    parser.add_argument('-f', "--filters",
                        choices=available_filters.keys(),
                        help="Default: size md5",
                        action="append")
    parser.add_argument('-E', '--regex', dest="filters", action=FilterRegex)
    parser.add_argument('-s', '--shell',
                        dest="filters",
                        help="Filenames represented as {}: --shell \"du {} | cut -f1\"",
                        action=ActionShell)
    parser.add_argument('-x', '--exec-group',
                        dest="group_action",
                        help="Filenames represented as {}, filters as {f1}, {fn}...: --exec-group \"echo {} {f1}\"",
                        action=ActionShell)
    parser.add_argument('--remove',
                        dest="group_action",
                        action="append_const",
                        const='remove',
                        help="Remove Duplicates, last flag applies of remove or link ")
    parser.add_argument('--link',
                        dest="group_action",
                        action="append_const",
                        const='link',
                        help="Replaces Duplicates with Hard Links of Source, last flag applies of remove or link")
    parser.add_argument('--include', action='append')
    parser.add_argument('--exclude', action='append')
    parser.add_argument('--dir-include', action='append')
    parser.add_argument('--dir-exclude', action='append')
    parser.add_argument('--dir-hidden', action='store_true')
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


class ActionShell(ActionTemplate):
    def _process(self, template):
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
        template_format = TemplateFunc(template, aliases=aliases)
        shell_command = partial(self._invoke_shell, command=template_format)
        return shell_command

    def _invoke_shell(self, *args, command, **kwargs) -> str:
        args = (shlex.quote(arg) for arg in args)
        try:
            output = subprocess.check_output(command(*args, **kwargs), shell=True).decode('utf8')
        except subprocess.CalledProcessError as e:
            print("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
            return ''
        except KeyError as e:
            print("Filter", e, "not found")
            exit(1)
        return output


class FilterRegex(ActionTemplate):
    def _process(self, template):
        template = re.compile(template)
        regex_pattern = partial(self._re_match, pattern=template)
        return regex_pattern

    def _re_match(self, filename, *, pattern) -> str:
        split_file = os.path.split(filename)[1]
        quoted_dir = shlex.quote(split_file)

        result = pattern.search(quoted_dir)
        return result.group() if result else ""




