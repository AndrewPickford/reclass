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
from .item import Item

class CompItem(Item):

    def __init__(self, items, settings):
        self.type = Item.COMPOSITE
        self._items = items
        self._settings = settings
        self.assembleRefs()

    # TODO: possibility of confusion. Looks like 'assemble' should be either
    # 'gather' or 'extract'.
    def assembleRefs(self, context={}):
        self._refs = []
        self._allRefs = True
        for item in self._items:
            if item.has_references:
                item.assembleRefs(context)
                self._refs.extend(item.get_references())
                if item.allRefs is False:
                    self._allRefs = False

    @property
    def contents(self):
        return self._items

    @property
    def allRefs(self):
        return self._allRefs

    @property
    def has_references(self):
        return len(self._refs) > 0

    def get_references(self):
        return self._refs

    def merge_over(self, item):
        if item.type == Item.SCALAR or item.type == Item.COMPOSITE:
            return self
        raise RuntimeError('Trying to merge %s over %s' % (repr(self), repr(item)))

    def render(self, context, inventory):
        # Preserve type if only one item
        if len(self._items) == 1:
            return self._items[0].render(context, inventory)
        # Multiple items
        strings = [ str(i.render(context, inventory)) for i in self._items ]
        return "".join(strings)

    def __repr__(self):
        return 'CompItem(%r)' % self._items

    def __str__(self):
        return ''.join([ str(i) for i in self._items ])
