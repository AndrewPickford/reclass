from reclass.settings import Settings
from reclass.values.value import Value
from reclass.values.compitem import CompItem
from reclass.values.scaitem import ScaItem
from reclass.values.valuelist import ValueList
from reclass.values.listitem import ListItem
from reclass.values.dictitem import DictItem
import unittest

SETTINGS = Settings()

class TestListItem(unittest.TestCase):

    def test_merge_over_merge_list(self):
        listitem1 = ListItem([1], SETTINGS)
        listitem2 = ListItem([2], SETTINGS)
        expected = ListItem([1, 2], SETTINGS)

        result = listitem2.merge_over(listitem1)

        self.assertEquals(result.contents, expected.contents)

    def test_merge_other_types_not_allowed(self):
        other = type('Other', (object,), {'type': 34})
        val1 = Value(None, SETTINGS, '')
        listitem = ListItem(val1, SETTINGS)

        self.assertRaises(RuntimeError, listitem.merge_over, other)

if __name__ == '__main__':
    unittest.main()
