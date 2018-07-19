#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from reclass.settings import Settings
from reclass.values import item


class ScaItem(item.Item):

    type = item.ItemTypes.SCALAR

    def __init__(self, value, settings):
        super(ScaItem, self).__init__(value, settings)

    def merge_over(self, other):
        if other.type in [item.ItemTypes.SCALAR, item.ItemTypes.COMPOSITE]:
            return self
        raise RuntimeError('Failed to merge %s over %s' % (self, other))

    def render(self, context, inventory):
        return self.contents

    def __str__(self):
        return str(self.contents)
