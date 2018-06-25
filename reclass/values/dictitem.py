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

class DictItem(Item):

    def __init__(self, item, settings):
        self.type = Item.DICTIONARY
        self._dict = item
        self._settings = settings

    def contents(self):
        return self._dict

    def is_container(self):
        return True

    def render(self, context, inventory):
        return self._dict

    def __repr__(self):
        return 'DictItem(%r)' % self._dict
