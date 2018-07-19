#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from reclass.values import item


class ListItem(item.ContainerItem):

    type = item.ItemTypes.LIST

    def merge_over(self, other):
        if other.type == item.ItemTypes.LIST:
            other.contents.extend(self.contents)
            return other
        raise RuntimeError('Failed to merge %s over %s'  % (self, other))
