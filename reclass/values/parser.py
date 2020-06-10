#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pyparsing as pp

from .compitem import CompItem
from .invitem import InvItem
from .refitem import RefItem
from .scaitem import ScaItem

from reclass.errors import ParseError
from reclass.values.parser_funcs import tags
import reclass.values.parser_funcs as parsers

import collections
import six


class Parser(object):

    def __init__(self):
        self._ref_parser = None
        self._simple_parser = None
        self._old_settings = None

    @property
    def ref_parser(self):
        if self._ref_parser is None or self._settings != self._old_settings:
            self._ref_parser = parsers.get_ref_parser(self._settings)
            self._old_settings = self._settings
        return self._ref_parser

    @property
    def simple_ref_parser(self):
        if self._simple_parser is None or self._settings != self._old_settings:
            self._simple_parser = parsers.get_simple_ref_parser(self._settings)
            self._old_settings = self._settings
        return self._simple_parser

    def parse(self, value, settings):
        def full_parse():
            try:
                return self.ref_parser.parseString(value)
            except pp.ParseException as e:
                raise ParseError(e.msg, e.line, e.col, e.lineno)

        self._settings = settings
        sentinel_count = (value.count(settings.reference_sentinels[0]) +
                          value.count(settings.export_sentinels[0]))
        if sentinel_count == 0:
            # speed up: only use pyparsing if there are sentinels in the value
            return ScaItem(value, self._settings)
        elif sentinel_count == 1:  # speed up: try a simple reference
            try:
                tokens = self.simple_ref_parser.parseString(value)
            except pp.ParseException:
                tokens = full_parse()  # fall back on the full parser
        else:
            tokens = full_parse()  # use the full parser

        tokens = parsers.listify(tokens)
        items = self._create_items(tokens)
        if len(items) == 1:
            return items[0]
        return CompItem(items, self._settings)

    _item_builders = {tags.STR: (lambda s, v: ScaItem(v, s._settings)),
                      tags.REF: (lambda s, v: s._create_ref(v)),
                      tags.INV: (lambda s, v: s._create_inv(v)) }

    def _create_items(self, tokens):
        return [self._item_builders[t](self, v) for t, v in tokens ]

    def _create_ref(self, tokens):
        items = [ self._item_builders[t](self, v) for t, v in tokens ]
        return RefItem(items, self._settings)

    def _create_inv(self, tokens):
        items = [ScaItem(v, self._settings) for t, v in tokens]
        if len(items) == 1:
            return InvItem(items[0], self._settings)
        return InvItem(CompItem(items), self._settings)
