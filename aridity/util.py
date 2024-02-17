# Copyright 2017, 2020 Andrzej Cichocki

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

from importlib_metadata import entry_points
import collections, inspect, sys

dotpy = '.py'
ispy2 = sys.version_info.major < 3
null_exc_info = None, None, None

class NoSuchPathException(Exception): pass

class UnparseNoSuchPathException(NoSuchPathException):

    def __str__(self):
        from .model import Text
        path, = self.args
        return ' '.join(Text(word).unparse() for word in path)

class TreeNoSuchPathException(NoSuchPathException):

    def __str__(self):
        from .model import Text
        path, causes = self.args # XXX: Also collect (and show) where in the tree the causes happened?
        causestrtocount = collections.OrderedDict()
        for causestr in map(str, causes):
            try:
                causestrtocount[causestr] += 1
            except KeyError:
                causestrtocount[causestr] = 1
        lines = [' '.join(Text(word).unparse() for word in path)]
        for causestr, count in causestrtocount.items():
            causelines = causestr.splitlines()
            lines.append("%sx %s" % (count, causelines[0]))
            for l in causelines[1:]:
                lines.append("    %s" % l)
        return '\n'.join(lines)

class CycleException(Exception): pass

class UnsupportedEntryException(Exception): pass

class OrderedDictWrapper:

    def __init__(self, *args):
        self.d = collections.OrderedDict(*args)

    def __bool__(self):
        return bool(self.d)

    def __nonzero__(self):
        return self.__bool__()

class OrderedDict(OrderedDictWrapper):

    def __setitem__(self, k, v):
        self.d[k] = v

    def __getitem__(self, k):
        return self.d[k]

    def __delitem__(self, k):
        del self.d[k]

    def get(self, k, default = None):
        return self.d.get(k, default)

    def keys(self):
        return self.d.keys()

    def values(self):
        return self.d.values()

    def items(self):
        return self.d.items()

    def __iter__(self):
        return iter(self.d.values())

    def __eq__(self, that):
        return self.d == that

    def __repr__(self):
        return repr(self.d)

    def update(self, other):
        return self.d.update(other)

def realname(name):
    def apply(f):
        f.realname = name
        return f
    return apply

def allfunctions(clazz):
    for name, f in inspect.getmembers(clazz, predicate = lambda f: inspect.ismethod(f) or inspect.isfunction(f)):
        try:
            realname = f.realname
        except AttributeError:
            realname = name
        yield realname, clazz.__dict__[name]

def openresource(package_or_name, resource_name, encoding = 'ascii'):
    from .model import Resource
    return Resource(package_or_name, resource_name, encoding).open(False)

def solo(v):
    x, = v
    return x

def qualname(obj):
    try:
        return obj.__qualname__
    except AttributeError:
        name = obj.__name__
        if getattr(sys.modules[obj.__module__], name) is not obj:
            raise
        return name

def selectentrypoints(group):
    obj = entry_points()
    try:
        select = obj.select
    except AttributeError:
        return obj[group]
    return select(group = group)
