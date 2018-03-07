import os

from util.ActionCreateFilter import ActionSelectFilter
from util.ActionCreateFunc import ActionSelectGroupFunc


def parser_logic(parser):
    parser.add_argument('-f', '--filters',
                        dest="filters",
                        help="Filenames represented as {}: --shell \"du {} | cut -f1\"",
                        action=ActionSelectFilter)
    parser.add_argument('-x', '--exec-group',
                        dest="group_action",
                        help="Filenames represented as {}, filters as {f1}, {fn}...: --exec-group \"echo {} {f1}\"",
                        action=ActionSelectGroupFunc)
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

