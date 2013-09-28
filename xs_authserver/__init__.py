# -*- coding: utf-8 -*-

# Copyright © 2013 Miguel González <migonzalvar@activitycentral.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import hashlib
import json
import os.path
import re
import sqlite3
import uuid

from flask import Flask, request, render_template, g

# Default config
ENV_PREFIX = 'XS_AUTHSERVER'
ENV_VARS = {
    'OLPC_XS_DB': '/home/idmgr/identity.db',
    'DATABASE': os.path.abspath(os.path.join(os.path.dirname(__file__), 'test.db')),
}


def connect_to_database(database):
    return sqlite3.connect(database)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db


def init_db():
    try:
        with app.app_context():
            db = get_db()
            with app.open_resource('schema.sql', mode='r') as f:
                db.cursor().executescript(f.read())
            db.commit()
            return True
    except sqlite3.OperationalError as err:
        return False

def get_olpc_xs_db():
    db = getattr(g, '_olpc_xs_db', None)
    if db is None:
        db = g._olpc_xs_db = connect_to_database(app.config['OLPC_XS_DB'])
        db.row_factory = sqlite3.Row
    return db


class Idmgr(object):
    """Laptops registered on idmgr.

    Correspond to a register in table ``laptop`` on idmgr database. The
    schema is defined as:

    .. code:: sql

        CREATE TABLE laptops (
            serial VARCHAR(20) NOT NULL,
            nickname VARCHAR(200) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            pubkey TEXT NOT NULL,
            uuid VARCHAR(100),
            lastmodified TEXT DEFAULT '1970-11-12 12:34:56',
            class_group INTEGER,
            PRIMARY KEY (serial)
        );
    """
    fields = ("serial", "nickname", "full_name", "pubkey")

    @classmethod
    def all(cls):
        query = "SELECT {} FROM laptops".format(",".join(cls.fields))
        cur = get_olpc_xs_db().execute(query)
        rv = cur.fetchall()
        cur.close()
        return [cls(**dict(zip(r.keys(), r))) for r in rv]

    def __init__(self, **kwargs):
        self.values = {k: kwargs[k] for k in kwargs if k in self.fields}

    def __getattr__(self, name):
        if name in self.fields:
            return self.values.get(name, None)
        raise AttributeError("%r object has no attribute %r" %
                             (self.__class__, name))

    @property
    def pkey_hash(self):
        return hashlib.sha1(self.pubkey).hexdigest()

    def __repr__(self):
        d = {'pkey_hash': self.pkey_hash}
        d.update(self.values)
        return repr(d)


class User(object):
    """User registered in xs-authserver custom database.

    .. code:: sql

        CREATE TABLE users (
            uuid VARCHAR(36) NOT NULL,
            nickname VARCHAR(200) NOT NULL,
            pkey_hash VARCHAR(40) NOT NULL,
            PRIMARY KEY (uuid),
            UNIQUE (pkey_hash)
        );

    """

    @classmethod
    def _get_users_by_pkey_hash(cls, pkey_hash):
        query = "SELECT uuid FROM users WHERE pkey_hash = ?"
        args = (pkey_hash, )
        cur = get_db().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return rv

    @classmethod
    def by_pkey_hash(cls, pkey_hash):
        rv = cls._get_users_by_pkey_hash(pkey_hash)
        if rv == []:
            sync_idmgr()
            rv = cls._get_users_by_pkey_hash(pkey_hash)
        if rv:
            return cls(uuid=rv[0]['uuid'])
        else:
            return None

    def __init__(self, **kwargs):
        if 'uuid' in kwargs:
            self.uuid = kwargs['uuid']
            self._load()
        else:
            self.uuid = None
            for field in kwargs:
                if field in ('nickname', 'pkey_hash'):
                    setattr(self, field, kwargs[field])

    def _load(self):
        query = "SELECT nickname, pkey_hash FROM users WHERE uuid = ?"
        args = (self.uuid, )
        cur = get_db().execute(query, args)
        rv = cur.fetchall()
        if rv:
            self.nickname = rv[0]['nickname']
            self.pkey_hash = rv[0]['pkey_hash']
        else:
            raise LookupError("User with UUID {uuid} not found".format(uuid=self.uuid))

    def save(self):
        if self.uuid:
            uuid_ = self.uuid
            query = "REPLACE users VALUES (?, ?, ?)"
        else:
            uuid_ = str(uuid.uuid4())
            query = "INSERT INTO users VALUES (?, ?, ?)"
        args = (uuid_, self.nickname, self.pkey_hash)
        get_db().execute(query, args)
        self.uuid = uuid_


def sync_idmgr():
    """Create new accounts from idmgr."""
    for i in Idmgr.all():
        u = User(nickname=i.nickname, pkey_hash=i.pkey_hash)
        try:
            u.save()
        except sqlite3.IntegrityError:
            # pkey_hash is not unique
            pass


app = Flask(__name__)

# Config section
for var in ENV_VARS:
    env_var = ENV_PREFIX + '_' + var
    value = os.environ.get(env_var) or ENV_VARS[var]
    app.config[var] = value


@app.teardown_appcontext
def close_connection(exception):
    for db_name in ('_database', '_olpc_xs_db'):
        db = getattr(g, db_name, None)
        if db is not None:
            db.close()


def identify_user_agent(user_agent):
    for sugar_ua in re.findall(r'SugarLabs/[\d\.]+', user_agent):
        platform = True
        version = sugar_ua.split("/")[1]
        break
    else:
        platform, version = False, None
    return {'sugar_platform': platform, 'sugar_version': version}


@app.route('/')
def index():
    context = dict(request=request)
    context.update(identify_user_agent(request.user_agent.string))

    context.update(pkey_hash=None, user=None)
    cookie = request.cookies.get('xoid')
    if cookie:
        # TODO: secure reading cookie
        xoid = json.loads(cookie)
        if xoid:
            pkey_hash = xoid.get('pkey_hash')
            if pkey_hash:
                context.update(pkey_hash=pkey_hash)
                context.update(user=User.by_pkey_hash(pkey_hash))

    context['registered_users'] = Idmgr.all()
    return render_template("index.html", **context)
