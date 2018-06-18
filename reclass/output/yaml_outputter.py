#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
# Copyright © 2007–14 martin f. krafft <madduck@madduck.net>
# Released under the terms of the Artistic Licence 2.0
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from reclass.output import OutputterBase
import yaml

_SafeDumper = yaml.CSafeDumper if yaml.__with_libyaml__ else yaml.SafeDumper


class Outputter(OutputterBase):

    def dump(self, data, pretty_print=False, no_refs=False):
        if (no_refs):
            return yaml.dump(data, default_flow_style=not pretty_print, Dumper=ExplicitDumper)
        else:
            return yaml.dump(data, default_flow_style=not pretty_print, Dumper=_SafeDumper)


class ExplicitDumper(_SafeDumper):
    """
    A dumper that will never emit aliases.
    """

    def ignore_aliases(self, data):
        return True
