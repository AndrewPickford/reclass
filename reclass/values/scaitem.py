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

class ScaItem(Item):

    def __init__(self, value, settings):
        self.type = Item.SCALAR
        self._value = value
        self._settings = settings

    def contents(self):
        return self._value

    def merge_over(self, item):
        if item.type == Item.SCALAR or item.type == Item.COMPOSITE:
            return self
        raise RuntimeError('Trying to merge %s over %s' % (repr(self), repr(item)))

    def render(self, context, inventory):
        return self._value

    def __repr__(self):
        return 'ScaItem({0!r})'.format(self._value)

    def __str__(self):
        return str(self._value)
