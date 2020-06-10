#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from reclass.values import item
from reclass.utils.dictpath import DictPath
from reclass.errors import ResolveError


class RefItem(item.ItemWithReferences):

    type = item.ItemTypes.REFERENCE

    def assembleRefs(self, context={}):
        super(RefItem, self).assembleRefs(context)
        try:
            self._refs.append(self._flatten_contents(context))
        except ResolveError as e:
            self.allRefs = False

    def _flatten_contents(self, context, inventory=None):
        result = [str(i.render(context, inventory)) for i in self.contents]
        return "".join(result)

    def _resolve(self, ref, context):
        path = DictPath(self._settings.delimiter, ref)
        try:
            return path.get_value(context)
        except (KeyError, TypeError) as e:
            raise ResolveError(ref)

    def render(self, context, inventory):
        #strings = [str(i.render(context, inventory)) for i in self.contents]
        #return self._resolve("".join(strings), context)
        return self._resolve(self._flatten_contents(context, inventory),
                             context)

    def __str__(self):
        strings = [str(i) for i in self.contents]
        rs = self._settings.reference_sentinels
        return '{0}{1}{2}'.format(rs[0], ''.join(strings), rs[1])
