#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
# Copyright © 2007–14 martin f. krafft <madduck@madduck.net>
# Released under the terms of the Artistic Licence 2.0
#

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

#try:
#    from types import StringTypes
#except ImportError:
#    StringTypes = (str, )

import copy
import sys
import types

from six import iteritems, next

from collections import namedtuple
from reclass.utils.dictpath import DictPath
from reclass.utils.parameterdict import ParameterDict
from reclass.utils.parameterlist import ParameterList
from reclass.values.value import Value
from reclass.values.valuelist import ValueList
from reclass.errors import InfiniteRecursionError, ResolveError, ResolveErrorList, InterpolationError, BadReferencesError


class Parameters(object):
    '''
    A class to hold nested dictionaries with the following specialities:

      1. "merging" a dictionary (the "new" dictionary) into the current
         Parameters causes a recursive walk of the new dict, during which

         - scalars (incl. tuples) are replaced with the value from the new
           dictionary;
         - lists are extended, not replaced;
         - dictionaries are updated (using dict.update), not replaced;

      2. "interpolating" a dictionary means that values within the dictionary
         can reference other values in the same dictionary. Those references
         are collected during merging and then resolved during interpolation,
         which avoids having to walk the dictionary twice. If a referenced
         value contains references itself, those are resolved first, in
         topological order. Therefore, deep references work. Cyclical
         references cause an error.

    To support these specialities, this class only exposes very limited
    functionality and does not try to be a really mapping object.
    '''

    def __init__(self, mapping, settings, uri, parse_strings=True):
        self._settings = settings
        self._uri = uri
        self._base = ParameterDict(uri=self._uri)
        self._unrendered = None
        self._escapes_handled = {}
        self._inv_queries = []
        self._resolve_errors = ResolveErrorList()
        self._needs_all_envs = False
        self._parse_strings = parse_strings
        if mapping is not None:
            # initialise by merging
            self.merge(mapping)

    def __len__(self):
        return len(self._base)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._base)

    def __eq__(self, other):
        return isinstance(other, type(self)) \
                and self._base == other._base \
                and self._settings == other._settings

    def __ne__(self, other):
        return not self.__eq__(other)

    def has_inv_query(self):
        return len(self._inv_queries) > 0

    def get_inv_queries(self):
        return self._inv_queries

    def needs_all_envs(self):
        return self._needs_all_envs

    def resolve_errors(self):
        return self._resolve_errors

    def as_dict(self):
        return self._base.copy()

    def _wrap_value(self, value):
        if isinstance(value, (Value, ValueList)):
            return value
        elif isinstance(value, dict):
            return self._wrap_dict(value)
        elif isinstance(value, list):
            return self._wrap_list(value)
        else:
            try:
                return Value(value, self._settings, self._uri, parse_string=self._parse_strings)
            except InterpolationError as e:
                e.context = DictPath(self._settings.delimiter)
                raise

    def _wrap_list(self, source):
        l = ParameterList(uri=self._uri)
        for (k, v) in enumerate(source):
            try:
                l.append(self._wrap_value(v))
            except InterpolationError as e:
                e.context.add_ancestor(str(k))
                raise
        return l

    def _wrap_dict(self, source):
        d = ParameterDict(uri=self._uri)
        for (k, v) in iteritems(source):
            try:
                d[k] = self._wrap_value(v)
            except InterpolationError as e:
                e.context.add_ancestor(str(k))
                raise
        return d

    def _update_value(self, cur, new):
        if isinstance(cur, Value):
            values = ValueList(cur, self._settings)
        elif isinstance(cur, ValueList):
            values = cur
        else:
            if isinstance(cur, (ParameterDict, ParameterList)):
                uri = cur.uri
            else:
                uri = self._uri
            values = ValueList(Value(cur, self._settings, uri), self._settings)

        if isinstance(new, Value):
            values.append(new)
        elif isinstance(new, ValueList):
            values.extend(new)
        else:
            if isinstance(new, (ParameterDict, ParameterList)):
                uri = new.uri
            else:
                uri = self._uri
            values.append(Value(new, self._settings, uri, parse_string=self._parse_strings))

        return values

    def _merge_dict(self, cur, new):
        """Merge a dictionary with another dictionary.

        Iterate over keys in new. If this is not an initialization merge and
        the key begins with PARAMETER_DICT_KEY_OVERRIDE_PREFIX, override the
        value of the key in cur. Otherwise deeply merge the contents of the key
        in cur with the contents of the key in _merge_recurse over the item.

        Args:
            cur (dict): Current dictionary
            new (dict): Dictionary to be merged
            initmerge (bool): True if called as part of entity init

        Returns:
            dict: a merged dictionary

        """

        for (key, value) in iteritems(new):
            if key[0] in self._settings.dict_key_prefixes:
                newkey = key[1:]
                if not isinstance(value, Value):
                    value = Value(value, self._settings, self._uri, parse_string=self._parse_strings)
                if key[0] == self._settings.dict_key_override_prefix:
                    value.overwrite = True
                elif key[0] == self._settings.dict_key_constant_prefix:
                    value.constant = True
                value = self._merge_recurse(cur.get(newkey), value)
                key = newkey
            else:
                value = self._merge_recurse(cur.get(key), value)
            cur[key] = value
        cur.uri = new.uri
        return cur

    def _merge_recurse(self, cur, new):
        """Merge a parameter with another parameter.

        Iterate over keys in new. Call _merge_dict, _update_value
        depending on type.

        Args:
            cur: Current parameter
            new: Parameter to be merged

        Returns:
            merged parameter (Value or ValueList)

        """

        if isinstance(new, dict):
            if cur is None:
                cur = ParameterDict(uri=self._uri)
            if isinstance(cur, dict):
                return self._merge_dict(cur, new)
            else:
                return self._update_value(cur, new)
        else:
            if cur is None:
                return new
            else:
                return self._update_value(cur, new)

    def merge(self, other):
        """Merge function (public edition).

        Call _merge_recurse on self with either another Parameter object or a
        dict (for initialization). Set initmerge if it's a dict.

        Args:
            other (dict or Parameter): Thing to merge with self._base

        Returns:
            None: Nothing

        """

        self._unrendered = None
        if isinstance(other, dict):
            wrapped = self._wrap_dict(other)
        elif isinstance(other, self.__class__):
            wrapped = other._wrap_dict(other._base)
        else:
            raise TypeError('Cannot merge %s objects into %s' % (type(other),
                            self.__class__.__name__))
        self._base = self._merge_recurse(self._base, wrapped)

    def _render_simple_container(self, container, key, value, path):
            if isinstance(value, ValueList):
                if value.is_complex():
                    p = path.new_subpath(key)
                    self._unrendered[p] = True
                    container[key] = value
                    if value.has_inv_query():
                        self._inv_queries.append((p, value))
                        if value.needs_all_envs():
                            self._needs_all_envs = True
                    return
                else:
                    value = value.merge()
            if isinstance(value, Value) and value.is_container():
                value = value.contents()
            if isinstance(value, dict):
                container[key] = self._render_simple_dict(value, path.new_subpath(key))
            elif isinstance(value, list):
                container[key] = self._render_simple_list(value, path.new_subpath(key))
            elif isinstance(value, Value):
                if value.is_complex():
                    p = path.new_subpath(key)
                    self._unrendered[p] = True
                    container[key] = value
                    if value.has_inv_query():
                        self._inv_queries.append((p, value))
                        if value.needs_all_envs():
                            self._needs_all_envs = True
                else:
                    container[key] = value.render(None, None)
            else:
                container[key] = value

    def _render_simple_dict(self, dictionary, path):
        new_dict = {}
        for (key, value) in iteritems(dictionary):
            self._render_simple_container(new_dict, key, value, path)
        return new_dict

    def _render_simple_list(self, item_list, path):
        new_list = [ None ] * len(item_list)
        for n, value in enumerate(item_list):
            self._render_simple_container(new_list, n, value, path)
        return new_list

    def interpolate(self, inventory=None):
        self._initialise_interpolate()
        while len(self._unrendered) > 0:
            # we could use a view here, but this is simple enough:
            # _interpolate_inner removes references from the refs hash after
            # processing them, so we cannot just iterate the dict
            path, v = next(iteritems(self._unrendered))
            self._interpolate_inner(path, inventory)
        if self._resolve_errors.have_errors():
            raise self._resolve_errors

    def initialise_interpolation(self):
        self._unrendered = None
        self._initialise_interpolate()

    def _initialise_interpolate(self):
        if self._unrendered is None:
            self._unrendered = {}
            self._inv_queries = []
            self._needs_all_envs = False
            self._resolve_errors = ResolveErrorList()
            self._base = self._render_simple_dict(self._base, DictPath(self._settings.delimiter))

    def _interpolate_inner(self, path, inventory):
        value = path.get_value(self._base)
        if not isinstance(value, (Value, ValueList)):
            # references to lists and dicts are only deepcopied when merged
            # together so it's possible a value with references in a referenced
            # list or dict has already been visited by _interpolate_inner
            del self._unrendered[path]
            return
        self._unrendered[path] = False
        self._interpolate_references(path, value, inventory)
        new = self._interpolate_render_value(path, value, inventory)
        path.set_value(self._base, new)
        del self._unrendered[path]

    def _interpolate_render_value(self, path, value, inventory):
        try:
            new = value.render(self._base, inventory)
        except ResolveError as e:
            e.context = path
            if self._settings.group_errors:
                self._resolve_errors.add(e)
                new = None
            else:
                raise
        except InterpolationError as e:
            e.context = path
            raise

        if isinstance(new, dict):
            new = self._render_simple_dict(new, path)
        elif isinstance(new, list):
            new = self._render_simple_list(new, path)
        return new

    def _interpolate_references(self, path, value, inventory):
        all_refs = False
        while not all_refs:
            for ref in value.get_references():
                path_from_ref = DictPath(self._settings.delimiter, ref)

                if path_from_ref in self._unrendered:
                    if self._unrendered[path_from_ref] is False:
                        # every call to _interpolate_inner replaces the value of
                        # self._unrendered[path] with False
                        # Therefore, if we encounter False instead of True,
                        # it means that we have already processed it and are now
                        # faced with a cyclical reference.
                        raise InfiniteRecursionError(path, ref, value.uri)
                    else:
                        self._interpolate_inner(path_from_ref, inventory)
                else:
                    # ensure ancestor keys are already dereferenced
                    ancestor = DictPath(self._settings.delimiter)
                    for k in path_from_ref.key_parts():
                        ancestor = ancestor.new_subpath(k)
                        if ancestor in self._unrendered:
                            self._interpolate_inner(ancestor, inventory)
            if value.allRefs():
                all_refs = True
            else:
                # not all references in the value could be calculated previously so
                # try recalculating references with current context and recursively
                # call _interpolate_inner if the number of references has increased
                # Otherwise raise an error
                old = len(value.get_references())
                value.assembleRefs(self._base)
                if old == len(value.get_references()):
                    raise BadReferencesError(value.get_references(), str(path), value.uri)
