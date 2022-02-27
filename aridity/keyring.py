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

from .model import Scalar
from functools import partial
from getpass import getpass

passwordbase = str

class Password(passwordbase):

    null_exc_info = None, None, None

    def __new__(cls, password, setter):
        p = passwordbase.__new__(cls, password)
        p.setter = setter
        return p

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        if self.setter is not None and self.null_exc_info == exc_info:
            self.setter(self)

def keyring(scope, serviceres, usernameres):
    from keyring import get_password, set_password
    service = serviceres.resolve(scope).cat()
    username = usernameres.resolve(scope).cat()
    password = get_password(service, username)
    return Scalar(Password(*[getpass(), partial(set_password, service, username)] if password is None else [password, None]))