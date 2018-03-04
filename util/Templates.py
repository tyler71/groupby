import argparse
import string

class ActionTemplate(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        _copy = argparse._copy
        _ensure_value = argparse._ensure_value

        items = _copy.copy(_ensure_value(namespace, self.dest, []))
        if isinstance(values, (list, tuple)):
            for template in values:
                template = self.format_template(template)
                callable_ = self._process(template)
                items.append(callable_)
        else:
            template = values
            callable_ = self._process(template)
            items.append(callable_)

        setattr(namespace, self.dest, items)

    def _format_template(self, template):
        def wrapper(*args, **kwargs):
            template_func = template.format(*args, **kwargs)
            return template_func
        return wrapper

    def _process(self, template):
        # should take a template
        # and return a function allowing it to be called with a string
        raise (ValueError, "Expected to be extended in subclass")


class TemplateFunc(string.Formatter):
    def __init__(self, template, aliases):
        self.template = template
        self.aliases = aliases

        for key, alias in self.aliases.items():
            self.template = self.template.replace(key, alias)

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
