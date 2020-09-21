from __future__ import absolute_import
import collections

import yaml
from yaml.representer import SafeRepresenter
import six


class LiteralUnicode(six.text_type):
    pass


def change_style(style, representer):
    def new_representer(dumper, data):
        scalar = representer(dumper, data)
        scalar.style = style
        return scalar
    return new_representer


represent_literal_unicode = change_style('|', SafeRepresenter.represent_unicode)
yaml.add_representer(LiteralUnicode, represent_literal_unicode, Dumper=yaml.SafeDumper)
