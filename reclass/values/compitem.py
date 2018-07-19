#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from reclass.settings import Settings
from reclass.values import item


class CompItem(item.ItemWithReferences):

    type = item.ItemTypes.COMPOSITE

    def merge_over(self, other):
        if (other.type == item.ItemTypes.SCALAR or
                other.type == item.ItemTypes.COMPOSITE):
            return self
        raise RuntimeError('Failed to merge %s over %s' % (self, other))

    def render(self, context, inventory):
        # Preserve type if only one item
        if len(self.contents) == 1:
            return self.contents[0].render(context, inventory)
        # Multiple items
        strings = [str(i.render(context, inventory)) for i in self.contents]
        return "".join(strings)

    def __str__(self):
        return ''.join([str(i) for i in self.contents])
