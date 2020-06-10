from reclass.settings import Settings
from reclass.values.value import Value
from reclass.values.compitem import CompItem
from reclass.values.scaitem import ScaItem
from reclass.values.valuelist import ValueList
from reclass.values.listitem import ListItem
from reclass.values.dictitem import DictItem
import unittest

SETTINGS = Settings()

class TestScaItem(unittest.TestCase):

    def test_merge_over_merge_scalar(self):
        scalar1 = ScaItem([1], SETTINGS)
        scalar2 = ScaItem([2], SETTINGS)

        result = scalar2.merge_over(scalar1)

        self.assertEquals(result.contents, scalar2.contents)

    def test_merge_over_merge_composite(self):
        scalar1 = CompItem(Value(1, SETTINGS, ''), SETTINGS)
        scalar2 = ScaItem([2], SETTINGS)

        result = scalar2.merge_over(scalar1)

        self.assertEquals(result.contents, scalar2.contents)

    def test_merge_other_types_not_allowed(self):
        other = type('Other', (object,), {'type': 34})
        val1 = Value(None, SETTINGS, '')
        scalar = ScaItem(val1, SETTINGS)

        self.assertRaises(RuntimeError, scalar.merge_over, other)

if __name__ == '__main__':
    unittest.main()
