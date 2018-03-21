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
                        help="Filenames represented as {}: --shell \"du {} | cut -f1\"",
                        action=ActionSelectFilter,
                        # action=ActionAppendFilePropertyFilter,
                        )

    parser.add_argument('-x', '--exec-shell',
                        dest="group_action",
                        metavar='COMMAND',
                        help="Filenames represented as {}, filters as {f1}, {fn}...: --exec-group \"echo {} {f1}\"",
                        action=ActionAppendExecShell,
                        )

    parser.add_argument('-m', '--exec-merge',
                        dest="group_action",
                        metavar="DIRECTORY",
                        action=ActionAppendMerge,
                        help='Includes 4 options including {merge_options}'.format(
                            merge_options=' '.join(ActionAppendMerge.overwrite_flags().keys()))
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
                        help='No indenting or empty newlines in standard output',
                        )

    parser.add_argument('-r', '--recursive',
                        action='store_true',
                        )

    parser.add_argument('--include',
                        action='append',
                        )

    parser.add_argument('--exclude',
                        action='append',
                        )

    parser.add_argument('--dir-include',
                        action='append',
                        )

    parser.add_argument('--dir-exclude',
                        action='append',
                        )

    parser.add_argument('--dir-hidden',
                        action='store_true',
                        )

    parser.add_argument("--max-depth",
                        type=int,
                        )

    parser.add_argument('--empty-file',
                        action='store_true',
                        help="Allow comparision of empty files",
                        )

    parser.add_argument('--follow-symbolic',
                        action='store_true', help="Allow following of symbolic links for compare",
                        )

    parser.add_argument('-g', '--group-size', metavar="SIZE", type=int, default=1,
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

