"""Test HADGEM2-CC fixes."""
import unittest

from esmvalcore.cmor.fix import Fix
from esmvalcore.cmor._fixes.cmip5.hadgem2_cc import AllVars, O2


class TestAllVars(unittest.TestCase):
    """Test allvars fixes."""

    def test_get(self):
        """Test fix get"""
        self.assertListEqual(
            Fix.get_fixes('CMIP5', 'HADGEM2-CC', 'tas'), [AllVars()])


class TestO2(unittest.TestCase):
    """Test o2 fixes."""

    def test_get(self):
        """Test fix get"""
        self.assertListEqual(
            Fix.get_fixes('CMIP5', 'HADGEM2-CC', 'o2'), [AllVars(), O2()])
