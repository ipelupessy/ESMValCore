"""Test fixes for FIO-ESM."""
import unittest

from cf_units import Unit
from iris.cube import Cube

from esmvalcore.cmor.fix import Fix
from esmvalcore.cmor._fixes.cmip5.fio_esm import Ch4, Co2


class TestCh4(unittest.TestCase):
    """Test ch4 fixes."""

    def setUp(self):
        """Prepare tests."""
        self.cube = Cube([1.0], var_name='ch4', units='J')
        self.fix = Ch4()

    def test_get(self):
        """Test fix get"""
        self.assertListEqual(
            Fix.get_fixes('CMIP5', 'FIO-ESM', 'ch4'), [Ch4()])

    def test_fix_data(self):
        """Test data fix."""
        cube = self.fix.fix_data(self.cube)
        self.assertEqual(cube.data[0], 29. / 16. * 1.e9)
        self.assertEqual(cube.units, Unit('J'))


class TestCo2(unittest.TestCase):
    """Test co2 fixes."""

    def setUp(self):
        """Prepare tests."""
        self.cube = Cube([1.0], var_name='co2', units='J')
        self.fix = Co2()

    def test_get(self):
        """Test fix get"""
        self.assertListEqual(
            Fix.get_fixes('CMIP5', 'FIO-ESM', 'co2'), [Co2()])

    def test_fix_data(self):
        """Test data fix."""
        cube = self.fix.fix_data(self.cube)
        self.assertEqual(cube.data[0], 29. / 44. * 1.e6)
        self.assertEqual(cube.units, Unit('J'))
