#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .parser import Parser
from .dictitem import DictItem
from .listitem import ListItem
from .scaitem import ScaItem
from reclass.errors import InterpolationError

from six import string_types

class Value(object):

    _parser = Parser()

    def __init__(self, value, settings, uri, parse_string=True):
        self._settings = settings
        self.uri = uri
        self.overwrite = False
        self.constant = False
        if isinstance(value, string_types):
            if parse_string:
                try:
                    self._item = self._parser.parse(value, self._settings)
                except InterpolationError as e:
                    e.uri = self.uri
                    raise
            else:
                self._item = ScaItem(value, self._settings)
        elif isinstance(value, list):
            self._item = ListItem(value, self._settings)
        elif isinstance(value, dict):
            self._item = DictItem(value, self._settings)
        else:
            self._item = ScaItem(value, self._settings)

    def item_type(self):
        return self._item.type

    def item_type_str(self):
        return self._item.type_str()

    def is_container(self):
        return self._item.is_container()

    @property
    def allRefs(self):
        return self._item.allRefs

    @property
    def has_references(self):
        return self._item.has_references

    @property
    def has_inv_query(self):
        return self._item.has_inv_query

    @property
    def needs_all_envs(self):
        if self._item.has_inv_query:
            return self._item.needs_all_envs
        return False

    def ignore_failed_render(self):
        return self._item.ignore_failed_render

    @property
    def is_complex(self):
        return self._item.is_complex

    def get_references(self):
        return self._item.get_references()

    def get_inv_references(self):
        return self._item.get_inv_references()

    def assembleRefs(self, context):
        if self._item.has_references:
            self._item.assembleRefs(context)

    def render(self, context, inventory):
        try:
            return self._item.render(context, inventory)
        except InterpolationError as e:
            e.uri = self.uri
            raise

    @property
    def contents(self):
        return self._item.contents

    def merge_over(self, value):
        self._item = self._item.merge_over(value._item)
        return self

    def __repr__(self):
        return 'Value(%r)' % self._item

    def __str__(self):
        return str(self._item)
