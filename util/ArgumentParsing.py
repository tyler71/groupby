import os

from util.ActionCreateFilter import ActionAppendRegexFilter, ActionAppendShellFilter, ActionAppendFilePropertyFilter
from util.ActionCreateFunc import ActionAppendExecShell, ActionAppendMerge, remove_files, hardlink_files


def parser_logic(parser):
    parser.add_argument('-f', '--filter',
                        dest="filters",
                        help="Filenames represented as {}: --shell \"du {} | cut -f1\"",
                        action=ActionAppendFilePropertyFilter)
    parser.add_argument('-E', '--filter-regex', dest="filters", action=ActionAppendRegexFilter)
    parser.add_argument('-s', '--filter-shell', dest="filters", action=ActionAppendShellFilter)
    parser.add_argument('-x', '--exec-group',
                        dest="group_action",
                        help="Filenames represented as {}, filters as {f1}, {fn}...: --exec-group \"echo {} {f1}\"",
                        action=ActionAppendExecShell)
    parser.add_argument('-m', '--exec-merge', dest="group_action", action=ActionAppendMerge)
    parser.add_argument('--exec-remove', const=remove_files, dest="group_action", action='append_const')
    parser.add_argument('--exec-link', const=hardlink_files, dest="group_action", action='append_const')
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

