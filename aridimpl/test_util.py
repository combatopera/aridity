# Copyright 2017 Andrzej Cichocki

# This file is part of aridity.
#
# aridity is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# aridity is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with aridity.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from .util import OrderedSet

class TestUtil(unittest.TestCase):

    def test_orderedset(self):
        s = OrderedSet()
        self.assertEqual(False, bool(s))
        s.add(2)
        self.assertEqual(True, bool(s))
        s.add(1)
        s.add(0)
        self.assertEqual([2, 1, 0], list(s)) # Order preserved.
        s.add(1)
        self.assertEqual([2, 1, 0], list(s)) # Order unchanged.
