import shlex
import re
import os

from functools import partial

from util.Templates import ActionAppendCreateFunc


class FilterRegex(ActionAppendCreateFunc):
    def _process(self, template):
        template = re.compile(template)
        regex_pattern = partial(self._re_match, pattern=template)
        return regex_pattern

    def _re_match(self, filename, *, pattern) -> str:
        split_file = os.path.split(filename)[1]
        quoted_dir = shlex.quote(split_file)

        result = pattern.search(quoted_dir)
        return result.group() if result else ""
