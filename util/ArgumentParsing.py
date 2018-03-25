import os
from functools import partial

from util.ActionCreateFilter import ActionSelectFilter
from util.ActionCreateFunc import ActionAppendExecShell, \
    ActionAppendMerge, \
    remove_files, \
    hardlink_files, \
    print_results


def parser_logic(parser):
    parser.add_argument('-f', '--filter',
                        dest="filters",
                        metavar="FILTER",
                        help=help_filter,
                        action=ActionSelectFilter,
                        )

    parser.add_argument('-x', '--exec-shell',
                        dest="group_action",
                        metavar='COMMAND',
                        help=help_exec_shell,
                        action=ActionAppendExecShell,
                        )

    parser.add_argument('-m', '--exec-merge',
                        dest="group_action",
                        metavar="DIRECTORY",
                        action=ActionAppendMerge,
                        help=help_exec_merge,
                        )

    parser.add_argument('--exec-remove',
                        const=remove_files,
                        dest="group_action",
                        action='append_const',
                        )

    parser.add_argument('--exec-link',
                        const=hardlink_files,
                        dest="group_action",
                        action='append_const',
                        )

    parser.add_argument("--exec-basic-formatting",
                        const=partial(print_results, basic_formatting=True),
                        dest="group_action",
                        action="append_const",
                        help='no indenting or empty newlines in standard output',
                        )

    parser.add_argument('-r', '--recursive',
                        action='store_true',
                        )

    parser.add_argument('--include',
                        action='append',
                        metavar='FILE',
                        )

    parser.add_argument('--exclude',
                        action='append',
                        metavar='FILE',
                        )

    parser.add_argument('--dir-include',
                        action='append',
                        metavar='DIRECTORY',
                        )

    parser.add_argument('--dir-exclude',
                        action='append',
                        metavar='DIRECTORY',
                        )

    parser.add_argument('--dir-hidden',
                        action='store_true',
                        )

    parser.add_argument("--max-depth",
                        type=int,
                        metavar='DEPTH',
                        )

    parser.add_argument('--empty-file',
                        action='store_true',
                        help="Allow comparision of empty files",
                        )

    parser.add_argument('--follow-symbolic',
                        action='store_true', help="allow following of symbolic links for compare",
                        )

    parser.add_argument('-g', '--group-size',
                        metavar="SIZE",
                        type=int,
                        default=1,
                        help="Minimum number of files in each group",
                        )

    parser.add_argument('-v', '--verbosity',
                        default=3,
                        action="count",
                        )

    parser.add_argument('directories',
                        metavar="directory",
                        default=[os.getcwd()],
                        nargs='*',
                        )
    return parser


help_filter = """builtin filters
modifiers with syntax filter:modifier
  partial_md5
  md5
  sha     :[1, 224, 256, 384, 512, 3_224, 3_256, 3_384, 3_512]
  modified:[MICROSECOND, SECOND, MINUTE, HOUR, DAY, MONTH, YEAR, WEEKDAY] | '%%DIRECTIVE'
  accessed:[MICROSECOND, SECOND, MINUTE, HOUR, DAY, MONTH, YEAR, WEEKDAY] | '%%DIRECTIVE'
  size    :[B, KB, MB, GB, TB, PB]
  filename:'EXPRESSION'
example: -f modified
         -f size:mb

shell filters
filenames represented as {}: 
example: -f \"du {} | cut -f1\"
         -f \"exiftool -p '\$DateTimeOriginal' {} | cut -d\: -f1\"
"""

help_exec_shell = """complete shell command on grouped files
notation:
  {}  : path and filename
  {.} : filename, extension removed
  {/} : filename, path removed
  {//}: path of filename
  {/.}: filename, extension and path removed
  {..}: extension of filename
  {fn}: filter output of filter n
example: -x "mkdir {f1}; mv {} {f1}/{/}"
         -x "mkdir {f1}; ffmpeg -i {} ogg/{/.}.ogg"
"""

help_exec_merge = """syntax DIRECTORY:MODIFIER
default = DIRECTORY:COUNT
COUNT : increment conflicting filenames
        foo.mkv -> foo_0001.mkv
IGNORE: skip conflicting filenames
ERROR : exit the program if conflicting filename found

replace conflicting filenames with CONDITION
LARGER
SMALLER
NEWER
OLDER
example: -m foo:LARGER
         -m foo:ERROR
"""
