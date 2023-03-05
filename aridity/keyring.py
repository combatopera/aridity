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
from .util import null_exc_info
from base64 import b64decode
from functools import partial
from getpass import getpass
from subprocess import check_output
from tempfile import NamedTemporaryFile
from threading import Semaphore
import logging, os

log = logging.getLogger(__name__)
passwordbase = str
setenvonce = Semaphore()

class Password(passwordbase):

    def __new__(cls, password, setter):
        p = passwordbase.__new__(cls, password)
        p.setter = setter
        return p

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        if self.setter is not None and null_exc_info == exc_info:
            self.setter(self)

def keyring(scope, serviceres, usernameres):
    if scope.resolved('keyring_cron').scalar and setenvonce.acquire(False):
        key = 'DBUS_SESSION_BUS_ADDRESS'
        value = "unix:path=/run/user/%s/bus" % os.geteuid()
        log.debug("Set %s to: %s", key, value)
        os.environ[key] = value
    from keyring import get_password, set_password
    service = serviceres.resolve(scope).cat()
    username = usernameres.resolve(scope).cat()
    password = None if scope.resolved('keyring_force').scalar else get_password(service, username)
    return Scalar(Password(*[getpass(), partial(set_password, service, username)] if password is None else [password, None]))

def gpg(scope, resolvable):
    with NamedTemporaryFile() as f:
        f.write(b64decode(resolvable.resolve(scope).cat()))
        f.flush()
        return Scalar(Password(check_output(['gpg', '-d', f.name]).decode('ascii'), None))
