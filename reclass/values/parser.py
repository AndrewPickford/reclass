#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

import pyparsing as pp

from compitem import CompItem
from invitem import InvItem
from refitem import RefItem
from scaitem import ScaItem

from reclass.defaults import ESCAPE_CHARACTER, REFERENCE_SENTINELS, EXPORT_SENTINELS
from reclass.errors import ParseError

_STR = 1
_REF = 2
_EXP = 3

_ESCAPE = ESCAPE_CHARACTER
_DOUBLE_ESCAPE = _ESCAPE + _ESCAPE

_REF_OPEN = REFERENCE_SENTINELS[0]
_REF_CLOSE = REFERENCE_SENTINELS[1]
_REF_CLOSE_FIRST = _REF_CLOSE[0]
_REF_ESCAPE_OPEN = _ESCAPE + _REF_OPEN
_REF_ESCAPE_CLOSE = _ESCAPE + _REF_CLOSE
_REF_DOUBLE_ESCAPE_OPEN = _DOUBLE_ESCAPE + _REF_OPEN
_REF_DOUBLE_ESCAPE_CLOSE = _DOUBLE_ESCAPE + _REF_CLOSE
_REF_EXCLUDES = _ESCAPE + _REF_OPEN + _REF_CLOSE

_EXP_OPEN = EXPORT_SENTINELS[0]
_EXP_CLOSE = EXPORT_SENTINELS[1]
_EXP_CLOSE_FIRST = _EXP_CLOSE[0]
_EXP_ESCAPE_OPEN = _ESCAPE + _EXP_OPEN
_EXP_ESCAPE_CLOSE = _ESCAPE + _EXP_CLOSE
_EXP_DOUBLE_ESCAPE_OPEN = _DOUBLE_ESCAPE + _EXP_OPEN
_EXP_DOUBLE_ESCAPE_CLOSE = _DOUBLE_ESCAPE + _EXP_CLOSE
_EXP_EXCLUDES = _ESCAPE + _EXP_OPEN + _EXP_CLOSE

_EXCLUDES = _ESCAPE + _REF_OPEN + _REF_CLOSE + _EXP_OPEN + _EXP_CLOSE

def _string(string, location, tokens):
    token = tokens[0]
    tokens[0] = (_STR, token)

def _reference(string, location, tokens):
    token = list(tokens[0])
    tokens[0] = (_REF, token)

def _export(string, location, tokens):
    token = list(tokens[0])
    tokens[0] = (_EXP, token)

def _get_parser():
    double_escape = pp.Combine(pp.Literal(_DOUBLE_ESCAPE) + pp.MatchFirst([pp.FollowedBy(_REF_OPEN), pp.FollowedBy(_REF_CLOSE)])).setParseAction(pp.replaceWith(_ESCAPE))

    ref_open = pp.Literal(_REF_OPEN).suppress()
    ref_close = pp.Literal(_REF_CLOSE).suppress()
    ref_not_open = ~pp.Literal(_REF_OPEN) + ~pp.Literal(_REF_ESCAPE_OPEN) + ~pp.Literal(_REF_DOUBLE_ESCAPE_OPEN)
    ref_not_close = ~pp.Literal(_REF_CLOSE) + ~pp.Literal(_REF_ESCAPE_CLOSE) + ~pp.Literal(_REF_DOUBLE_ESCAPE_CLOSE)
    ref_escape_open = pp.Literal(_REF_ESCAPE_OPEN).setParseAction(pp.replaceWith(_REF_OPEN))
    ref_escape_close = pp.Literal(_REF_ESCAPE_CLOSE).setParseAction(pp.replaceWith(_REF_CLOSE))
    ref_text = pp.CharsNotIn(_REF_EXCLUDES) | pp.CharsNotIn(_REF_CLOSE_FIRST, exact=1)
    ref_content = pp.Combine(pp.OneOrMore(ref_not_open + ref_not_close + ref_text))
    ref_string = pp.MatchFirst([double_escape, ref_escape_open, ref_escape_close, ref_content]).setParseAction(_string)
    ref_item = pp.Forward()
    ref_items = pp.OneOrMore(ref_item)
    reference = (ref_open + pp.Group(ref_items) + ref_close).setParseAction(_reference)
    ref_item << (reference | ref_string)

    exp_open = pp.Literal(_EXP_OPEN).suppress()
    exp_close = pp.Literal(_EXP_CLOSE).suppress()
    exp_not_open = ~pp.Literal(_EXP_OPEN) + ~pp.Literal(_EXP_ESCAPE_OPEN) + ~pp.Literal(_EXP_DOUBLE_ESCAPE_OPEN)
    exp_not_close = ~pp.Literal(_EXP_CLOSE) + ~pp.Literal(_EXP_ESCAPE_CLOSE) + ~pp.Literal(_EXP_DOUBLE_ESCAPE_CLOSE)
    exp_escape_open = pp.Literal(_EXP_ESCAPE_OPEN).setParseAction(pp.replaceWith(_EXP_OPEN))
    exp_escape_close = pp.Literal(_EXP_ESCAPE_CLOSE).setParseAction(pp.replaceWith(_EXP_CLOSE))
    exp_text = pp.CharsNotIn(_EXP_CLOSE_FIRST)
    exp_content = pp.Combine(pp.OneOrMore(exp_not_close + exp_text))
    exp_string = pp.MatchFirst([double_escape, exp_escape_open, exp_escape_close, exp_content]).setParseAction(_string)
    exp_items = pp.OneOrMore(exp_string)
    export = (exp_open + pp.Group(exp_items) + exp_close).setParseAction(_export)

    text = pp.CharsNotIn(_EXCLUDES) | pp.CharsNotIn('', exact=1)
    content = pp.Combine(pp.OneOrMore(ref_not_open + exp_not_open + text))
    string = pp.MatchFirst([double_escape, ref_escape_open, exp_escape_open, content]).setParseAction(_string)

    item = reference | export | string
    line = pp.OneOrMore(item) + pp.StringEnd()
    return line

def _get_simple_ref_parser():
    string = pp.CharsNotIn(_EXCLUDES).setParseAction(_string)
    ref_open = pp.Literal(_REF_OPEN).suppress()
    ref_close = pp.Literal(_REF_CLOSE).suppress()
    reference = (ref_open + pp.Group(string) + ref_close).setParseAction(_reference)
    line = pp.StringStart() + pp.Optional(string) + reference + pp.Optional(string) + pp.StringEnd()
    return line


class Parser(object):

    _parser = _get_parser()
    _simple_ref_parser = _get_simple_ref_parser()

    def parse(self, value, delimiter):
        self._delimiter = delimiter
        dollars = value.count('$')
        if dollars == 0:
            # speed up: only use pyparsing if there is a $ in the string
            return ScaItem(value)
        elif dollars == 1:
            # speed up: try a simple reference
            try:
                tokens = self._simple_ref_parser.leaveWhitespace().parseString(value).asList()
            except pp.ParseException as e:
                # fall back on the full parser
                try:
                    tokens = self._parser.leaveWhitespace().parseString(value).asList()
                except pp.ParseException as e:
                    raise ParseError(e.msg, e.line, e.col, e.lineno)
        else:
            # use the full parser
            try:
                tokens = self._parser.leaveWhitespace().parseString(value).asList()
            except pp.ParseException as e:
                raise ParseError(e.msg, e.line, e.col, e.lineno)

        items = self._create_items(tokens)
        if len(items) == 1:
            return items[0]
        else:
            return CompItem(items)

    _create_dict = { _STR: (lambda s, v: ScaItem(v)),
                     _REF: (lambda s, v: s._create_ref(v)),
                     _EXP: (lambda s, v: s._create_inv(v)) }

    def _create_items(self, tokens):
        return [ self._create_dict[t](self, v) for t, v in tokens ]

    def _create_ref(self, tokens):
        items = [ self._create_dict[t](self, v) for t, v in tokens ]
        return RefItem(items, self._delimiter)

    def _create_inv(self, tokens):
        items = [ ScaItem(v) for t, v in tokens ]
        if len(items) == 1:
            return InvItem(items[0], self._delimiter)
        else:
            return InvItem(CompItem(items), self._delimiter)