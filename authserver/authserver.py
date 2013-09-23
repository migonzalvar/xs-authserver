import hashlib
import json
import os.path
import re
import sqlite3

from flask import Flask, request, render_template, g


OLPC_XS_DB = '/home/idmgr/identity.db'
DATABASE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test.db'))


def connect_to_database(database):
    return sqlite3.connect(database)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db


def get_olpc_xs_db():
    db = getattr(g, '_olpc_xs_db', None)
    if db is None:
        db = g._olpc_xs_db = connect_to_database(app.config['OLPC_XS_DB'])
        db.row_factory = sqlite3.Row
    return db


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


class Idmgr(object):
    """Laptops registered on idmagr.

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
    @classmethod
    def get_by_pkey_hash(self, pkey_hash):
        query = "SELECT username FROM users WHERE pkey_hash = ?"
        args = (pkey_hash, )
        cur = get_db().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return rv[0] if rv else None


app = Flask(__name__)
app.debug = True

app.config.from_object(__name__)

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
        xoid = json.loads(cookie)
        if xoid:
            pkey_hash = xoid.get('pkey_hash')
            if pkey_hash:
                context.update(pkey_hash=pkey_hash)
                context.update(user=User.get_by_pkey_hash(pkey_hash))

    context['registered_users'] = Idmgr.all()
    return render_template("index.html", **context)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
