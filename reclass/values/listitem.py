#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .item import Item
from reclass.settings import Settings

class ListItem(Item):

    def __init__(self, item, settings):
        self.type = Item.LIST
        self._list = item
        self._settings = settings

    def contents(self):
        return self._list

    def is_container(self):
        return True

    def render(self, context, inventory):
        return self._list

    def merge_over(self, item):
        if item.type == Item.LIST:
            item._list.extend(self._list)
            return item
        raise RuntimeError('Trying to merge %s over %s' % (repr(self), repr(item)))

    def __repr__(self):
        return 'ListItem(%r)' % (self._list)
