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

import collections, inspect

class NoSuchPathException(Exception): pass

class OrderedSet:

    def __init__(self):
        self.d = collections.OrderedDict()

    def add(self, x):
        self.d[x] = None

    def update(self, g):
        for x in g:
            self.add(x)

    def __iter__(self):
        return iter(self.d.keys())

    def __bool__(self):
        return bool(self.d)

    def __nonzero__(self):
        return bool(self.d)

def allfunctions(clazz):
    for name, f in inspect.getmembers(clazz, predicate = lambda f: inspect.ismethod(f) or inspect.isfunction(f)):
        yield name[:-1] if name.endswith('_') else name, clazz.__dict__[name]
