#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import copy
import sys

from reclass.errors import ChangedConstantError, ResolveError, TypeMergeError


class ValueList(object):

    def __init__(self, value, settings):
        self._settings = settings
        self._refs = []
        self.allRefs = True
        self._values = [value]
        self._inv_refs = []
        self.has_inv_query = False
        self.ignore_failed_render = False
        self.is_complex = False
        self._update()

    @property
    def uri(self):
        return '; '.join([str(x.uri) for x in self._values])

    def append(self, value):
        self._values.append(value)
        self._update()

    def extend(self, values):
        self._values.extend(values._values)
        self._update()

    def _update(self):
        self.assembleRefs()
        self._check_for_inv_query()
        self.is_complex = False
        item_type = self._values[0].item_type()
        for v in self._values:
            if v.is_complex or v.constant or v.overwrite or v.item_type() != item_type:
                self.is_complex = True

    @property
    def has_references(self):
        return len(self._refs) > 0

    def get_inv_references(self):
        return self._inv_refs

    def get_references(self):
        return self._refs

    def _check_for_inv_query(self):
        self.has_inv_query = False
        self.ignore_failed_render = True
        for value in self._values:
            if value.has_inv_query:
                self._inv_refs.extend(value.get_inv_references())
                self.has_inv_query = True
                if value.ignore_failed_render() is False:
                    self.ignore_failed_render = False
        if self.has_inv_query is False:
            self.ignore_failed_render = False

    def assembleRefs(self, context={}):
        self._refs = []
        self.allRefs = True
        for value in self._values:
            value.assembleRefs(context)
            if value.has_references:
                self._refs.extend(value.get_references())
            if value.allRefs is False:
                self.allRefs = False

    @property
    def needs_all_envs(self):
        for value in self._values:
            if value.needs_all_envs:
                return True
        return False

    def merge(self):
        output = None
        for n, value in enumerate(self._values):
            if output is None:
                output = value
            else:
                output = value.merge_over(output)
        return output

    def render(self, context, inventory):
        from reclass.datatypes.parameters import Parameters

        output = None
        deepCopied = False
        last_error = None
        constant = False
        for n, value in enumerate(self._values):
            try:
                new = value.render(context, inventory)
            except ResolveError as e:
                # only ignore failed renders if
                # ignore_overwritten_missing_references is set and we are
                # dealing with a scalar value and it's not the last item in the
                # values list
                if (self._settings.ignore_overwritten_missing_references
                        and not isinstance(output, (dict, list))
                        and n != (len(self._values)-1)):
                    new = None
                    last_error = e
                    print("[WARNING] Reference '%s' undefined" % str(value),
                          file=sys.stderr)
                else:
                    raise e

            if constant:
                if self._settings.strict_constant_parameters:
                    raise ChangedConstantError('{0}; {1}'.format(self._values[n-1].uri, self._values[n].uri))
                else:
                    continue

            if output is None or value.overwrite:
                output = new
                deepCopied = False
            else:
                if isinstance(output, dict):
                    if isinstance(new, dict):
                        p1 = Parameters(output, self._settings, None, parse_strings=False)
                        p2 = Parameters(new, self._settings, None, parse_strings=False)
                        p1.merge(p2)
                        output = p1.as_dict()
                    elif isinstance(new, list):
                        raise TypeMergeError(self._values[n], self._values[n-1], self.uri)
                    elif self._settings.allow_scalar_over_dict or (self._settings.allow_none_override and new is None):
                        output = new
                        deepCopied = False
                    else:
                        raise TypeMergeError(self._values[n], self._values[n-1], self.uri)
                elif isinstance(output, list):
                    if isinstance(new, list):
                        if not deepCopied:
                            output = copy.deepcopy(output)
                            deepCopied = True
                        output.extend(new)
                    elif isinstance(new, dict):
                        raise TypeMergeError(self._values[n], self._values[n-1], self.uri)
                    elif self._settings.allow_scalar_over_list or (self._settings.allow_none_override and new is None):
                        output = new
                        deepCopied = False
                    else:
                        raise TypeMergeError(self._values[n], self._values[n-1], self.uri)
                else:
                    if isinstance(new, dict):
                        if self._settings.allow_dict_over_scalar:
                            output = new
                            deepCopied = False
                        else:
                            raise TypeMergeError(self._values[n], self._values[n-1], self.uri)
                    elif isinstance(new, list):
                        if self._settings.allow_list_over_scalar:
                            output_list = list()
                            output_list.append(output)
                            output_list.extend(new)
                            output = output_list
                            deepCopied = True
                        else:
                            raise TypeMergeError(self._values[n], self._values[n-1], self.uri)
                    else:
                        output = new
                        deepCopied = False

            if value.constant:
                constant = True

        if isinstance(output, (dict, list)) and last_error is not None:
            raise last_error

        return output
