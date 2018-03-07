import os

from util.ActionCreateFilter import ActionAppendRegexFilter, ActionAppendShellFilter
from util.ActionCreateFilter import list_filters
from util.ActionCreateFunc import ActionAppendExecShell, \
    ActionAppendMerge, \
    ActionAppendLink, \
    ActionAppendRemove, \
    ActionSelect


def parser_logic(parser):
    available_filters = list_filters()
    parser.add_argument('-f', "--filters",
                        choices=available_filters.keys(),
                        help="Default: size md5",
                        action="append")
    parser.add_argument('-E', '--regex', dest="filters", action=ActionAppendRegexFilter)
    parser.add_argument('-s', '--shell',
                        dest="filters",
                        help="Filenames represented as {}: --shell \"du {} | cut -f1\"",
                        action=ActionAppendShellFilter)
    parser.add_argument('-z',
                        dest="group_action",
                        help="Filenames represented as {}, filters as {f1}, {fn}...: --exec-group \"echo {} {f1}\"",
                        action=ActionSelect)
    parser.add_argument('-x', '--exec-group',
                        dest="group_action",
                        help="Filenames represented as {}, filters as {f1}, {fn}...: --exec-group \"echo {} {f1}\"",
                        action=ActionAppendExecShell)
    parser.add_argument('--remove',
                        dest="group_action",
                        action=ActionAppendRemove,
                        help="Remove Duplicates, last flag applies of remove or link ",
                        nargs='?',  # Not used; needed for compatibility
                        const="remove")  # Not used
    parser.add_argument('--merge',
                        dest="group_action",
                        action=ActionAppendMerge)
    parser.add_argument('--link',
                        dest="group_action",
                        action=ActionAppendLink,
                        help="Replaces Duplicates with Hard Links of Source, last flag applies of remove or link",
                        const="link",  # Not used
                        nargs='?')  # Not used; needed for compatibility
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

