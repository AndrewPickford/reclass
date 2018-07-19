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
import functools

STR = 1
REF = 2
INV = 3

_OBJ = 'OBJ'
_LOGICAL = 'LOGICAL'
_OPTION = 'OPTION'
_IF = 'IF'

TEST = 'TEST'
LIST_TEST = 'LIST_TEST'

VALUE = 'VALUE'
AND = 'AND'
OR = 'OR'

EQUAL = '=='
NOT_EQUAL = '!='

IGNORE_ERRORS = '+IgnoreErrors'
ALL_ENVS = '+AllEnvs'


def _tag_with(tag, transform=lambda x:x):
    def inner(tag, string, location, tokens):
        token = transform(tokens[0])
        tokens[0] = (tag, token)
    return functools.partial(inner, tag)

def get_expression_parser():

    s_end = pp.StringEnd()
    sign = pp.Optional(pp.Literal('-'))
    number = pp.Word(pp.nums)
    dpoint = pp.Literal('.')
    ignore_errors = pp.CaselessLiteral(IGNORE_ERRORS)
    all_envs = pp.CaselessLiteral(ALL_ENVS)
    eq, neq = pp.Literal(EQUAL), pp.Literal(NOT_EQUAL)
    eand, eor = pp.CaselessLiteral(AND), pp.CaselessLiteral(OR)

    option = (ignore_errors | all_envs).setParseAction(_tag_with(_OPTION))
    options = pp.Group(pp.ZeroOrMore(option))
    operator_test = (eq | neq).setParseAction(_tag_with(TEST))
    operator_logical = (eand | eor).setParseAction(_tag_with(_LOGICAL))
    begin_if = pp.CaselessLiteral(_IF).setParseAction(_tag_with(_IF))
    obj = pp.Word(pp.printables).setParseAction(_tag_with(_OBJ))

    integer = pp.Combine(sign + number + pp.WordEnd()).setParseAction(
            _tag_with(_OBJ, int))
    real = pp.Combine(sign +
                      ((number + dpoint + number) |
                       (dpoint + number) |
                       (number + dpoint))
                     ).setParseAction(_tag_with(_OBJ, float))
    expritem = integer | real | obj
    single_test = expritem + operator_test + expritem
    additional_test = operator_logical + single_test

    expr_var = pp.Group(obj + s_end).setParseAction(_tag_with(VALUE))
    expr_test = pp.Group(obj + begin_if + single_test +
                         pp.ZeroOrMore(additional_test) +
                         s_end).setParseAction(_tag_with(TEST))
    expr_list_test = pp.Group(begin_if + single_test +
                              pp.ZeroOrMore(additional_test) +
                              s_end).setParseAction(_tag_with(LIST_TEST))
    expr = expr_test | expr_var | expr_list_test
    line = options + expr + s_end
    return line

def get_ref_parser(escape_character, reference_sentinels, export_sentinels):
    _ESCAPE = escape_character
    _DOUBLE_ESCAPE = _ESCAPE + _ESCAPE

    _REF_OPEN = reference_sentinels[0]
    _REF_CLOSE = reference_sentinels[1]
    _REF_CLOSE_FIRST = _REF_CLOSE[0]
    _REF_ESCAPE_OPEN = _ESCAPE + _REF_OPEN
    _REF_ESCAPE_CLOSE = _ESCAPE + _REF_CLOSE
    _REF_DOUBLE_ESCAPE_OPEN = _DOUBLE_ESCAPE + _REF_OPEN
    _REF_DOUBLE_ESCAPE_CLOSE = _DOUBLE_ESCAPE + _REF_CLOSE
    _REF_EXCLUDES = _ESCAPE + _REF_OPEN + _REF_CLOSE

    _INV_OPEN = export_sentinels[0]
    _INV_CLOSE = export_sentinels[1]
    _INV_CLOSE_FIRST = _INV_CLOSE[0]
    _INV_ESCAPE_OPEN = _ESCAPE + _INV_OPEN
    _INV_ESCAPE_CLOSE = _ESCAPE + _INV_CLOSE
    _INV_DOUBLE_ESCAPE_OPEN = _DOUBLE_ESCAPE + _INV_OPEN
    _INV_DOUBLE_ESCAPE_CLOSE = _DOUBLE_ESCAPE + _INV_CLOSE
    _INV_EXCLUDES = _ESCAPE + _INV_OPEN + _INV_CLOSE

    _EXCLUDES = _ESCAPE + _REF_OPEN + _REF_CLOSE + _INV_OPEN + _INV_CLOSE

    double_escape = pp.Combine(pp.Literal(_DOUBLE_ESCAPE) +
        pp.MatchFirst([pp.FollowedBy(_REF_OPEN),
                       pp.FollowedBy(_REF_CLOSE),
                       pp.FollowedBy(_INV_OPEN),
                       pp.FollowedBy(_INV_CLOSE)])).setParseAction(
                               pp.replaceWith(_ESCAPE))

    ref_open = pp.Literal(_REF_OPEN).suppress()
    ref_close = pp.Literal(_REF_CLOSE).suppress()
    ref_not_open = ~pp.Literal(_REF_OPEN) + ~pp.Literal(_REF_ESCAPE_OPEN) + ~pp.Literal(_REF_DOUBLE_ESCAPE_OPEN)
    ref_not_close = ~pp.Literal(_REF_CLOSE) + ~pp.Literal(_REF_ESCAPE_CLOSE) + ~pp.Literal(_REF_DOUBLE_ESCAPE_CLOSE)
    ref_escape_open = pp.Literal(_REF_ESCAPE_OPEN).setParseAction(pp.replaceWith(_REF_OPEN))
    ref_escape_close = pp.Literal(_REF_ESCAPE_CLOSE).setParseAction(pp.replaceWith(_REF_CLOSE))
    ref_text = pp.CharsNotIn(_REF_EXCLUDES) | pp.CharsNotIn(_REF_CLOSE_FIRST, exact=1)
    ref_content = pp.Combine(pp.OneOrMore(ref_not_open + ref_not_close + ref_text))
    ref_string = pp.MatchFirst([double_escape, ref_escape_open, ref_escape_close, ref_content]).setParseAction(_tag_with(STR))
    ref_item = pp.Forward()
    ref_items = pp.OneOrMore(ref_item)
    reference = (ref_open + pp.Group(ref_items) + ref_close).setParseAction(_tag_with(REF))
    ref_item << (reference | ref_string)

    inv_open = pp.Literal(_INV_OPEN).suppress()
    inv_close = pp.Literal(_INV_CLOSE).suppress()
    inv_not_open = ~pp.Literal(_INV_OPEN) + ~pp.Literal(_INV_ESCAPE_OPEN) + ~pp.Literal(_INV_DOUBLE_ESCAPE_OPEN)
    inv_not_close = ~pp.Literal(_INV_CLOSE) + ~pp.Literal(_INV_ESCAPE_CLOSE) + ~pp.Literal(_INV_DOUBLE_ESCAPE_CLOSE)
    inv_escape_open = pp.Literal(_INV_ESCAPE_OPEN).setParseAction(pp.replaceWith(_INV_OPEN))
    inv_escape_close = pp.Literal(_INV_ESCAPE_CLOSE).setParseAction(pp.replaceWith(_INV_CLOSE))
    inv_text = pp.CharsNotIn(_INV_CLOSE_FIRST)
    inv_content = pp.Combine(pp.OneOrMore(inv_not_close + inv_text))
    inv_string = pp.MatchFirst([double_escape, inv_escape_open, inv_escape_close, inv_content]).setParseAction(_tag_with(STR))
    inv_items = pp.OneOrMore(inv_string)
    export = (inv_open + pp.Group(inv_items) + inv_close).setParseAction(_tag_with(INV))

    text = pp.CharsNotIn(_EXCLUDES) | pp.CharsNotIn('', exact=1)
    content = pp.Combine(pp.OneOrMore(ref_not_open + inv_not_open + text))
    string = pp.MatchFirst([double_escape, ref_escape_open, inv_escape_open, content]).setParseAction(_tag_with(STR))

    item = reference | export | string
    line = pp.OneOrMore(item) + pp.StringEnd()
    return line

def get_simple_ref_parser(escape_character, reference_sentinels, export_sentinels):
    _ESCAPE = escape_character
    _REF_OPEN = reference_sentinels[0]
    _REF_CLOSE = reference_sentinels[1]
    _INV_OPEN = export_sentinels[0]
    _INV_CLOSE = export_sentinels[1]
    _EXCLUDES = _ESCAPE + _REF_OPEN + _REF_CLOSE + _INV_OPEN + _INV_CLOSE

    string = pp.CharsNotIn(_EXCLUDES).setParseAction(_tag_with(STR))
    ref_open = pp.Literal(_REF_OPEN).suppress()
    ref_close = pp.Literal(_REF_CLOSE).suppress()
    reference = (ref_open + pp.Group(string) + ref_close).setParseAction(_tag_with(REF))
    line = pp.StringStart() + pp.Optional(string) + reference + pp.Optional(string) + pp.StringEnd()
    return line
