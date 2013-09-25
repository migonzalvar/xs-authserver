import json
import os
import sqlite3
import unittest
import tempfile

from werkzeug.datastructures import Headers

import authserver


FIXTURES = {
    'OLPC_XS_DB': """
CREATE TABLE "laptops" (
    serial VARCHAR(20) NOT NULL,
    nickname VARCHAR(200) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    pubkey TEXT NOT NULL,
    uuid VARCHAR(100),
    lastmodified TEXT DEFAULT '1970-11-12 12:34:56',
    class_group INTEGER,
    PRIMARY KEY (serial)
);
INSERT INTO "laptops" VALUES(
    'SHC23800059',
    'miguel',
    '',
    'AAAAB3NzaC1kc3MAAACBALLTqNsDS7t1/GRI6V9hrltCESM7c7Isw+OMieeL6tbCOb/hFlfnuWpreXwaN+IEp9kLbH/pH0U6fpqBbTxFkQ7sKTEm52fIBFIQinqayRqspP4MZp/+IVUZ4F/1N/E2jXpygpwciK+RaYt0T9f7aN1wp0RA7moVGwZ+W6wn6T6zAAAAFQCfuMPxCBN0cs5octiKcYDdIurRuQAAAIAU+K12HJ9p8ua3laen8rVSfSyYL5LMSWALflK6BEcZE7SiMMa1P3wOBFC21HBTZt28CyVhPOFt/6ptVsuzZeVP12141gcBSDPDE0zgGYW2ev7koL5GhiSUCn+Ag3ISjYJ3GHO3bmvQUXDV/vz9ADVX/k9xRdKaHpSx9Gmo5I5MkwAAAIAIT5Pg//ye+Bv23lMo24O2Axz5y2IlpZGKYy+pfOrwjInuPNhtLOAHn1Woq1CEwEqHEvHBxPHKB1P38rmZgajsVNu0OBEQjGwWfCMZa4IZh2+5FxpYFQnOuwDn44cexruLOH2vYHIb9FabTnRGn3XgNVSX86x3gVc7nN/Z1dBS8w==',
    '74EDF4DF-9E81-FF4F-F053-2174AACBFB86',
    '2013-09-19 11:14:34',
    3
);
""",
    'DATABASE': """
CREATE TABLE users (
    username,
    pkey_hash
);
INSERT INTO "users" VALUES(
    'fulano',
    'bc040eb5294c5fe63f5cfd28d6961c7db6b9a2bc'
);
"""
}


class AuthserverTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fds = {}
        for db, sql in FIXTURES.iteritems():
            fd, filename = tempfile.mkstemp()
            conn = sqlite3.connect(filename)
            conn.executescript(sql)
            conn.close()
            self.db_fds[db], authserver.app.config[db] = fd, filename
        authserver.app.config['TESTING'] = True
        self.app = authserver.app.test_client()

    def tearDown(self):
        for fd in self.db_fds.values():
            os.close(fd)
        os.unlink(authserver.app.config['DATABASE'])
        os.unlink(authserver.app.config['OLPC_XS_DB'])

    @staticmethod
    def make_cookie(pkey_hash):
        """Create a the magic XO cookie.

        :rtype : dict
        """
        cookie_value = json.dumps(dict(pkey_hash=pkey_hash))
        cookie = "xoid={cookie_value}".format(cookie_value=cookie_value)
        return cookie

    def test_unregistered(self):
        rv = self.app.get('/')
        assert "Please register your laptop" in rv.data
        assert "pkey_hash: None" in rv.data

    def test_registered_with_account(self):
        username, pkey_hash = 'fulano','bc040eb5294c5fe63f5cfd28d6961c7db6b9a2bc'
        cookie = self.make_cookie(pkey_hash)
        headers = Headers({'Cookie': cookie})
        rv = self.app.get('/', headers=headers)
        assert "Hello {}".format(username) in rv.data
        assert "pkey_hash: {}".format(pkey_hash) in rv.data

    def test_registered_without_account(self):
        username, pkey_hash = 'miguel', '195ed98f4975ebccb1e699d8636278b64e9276b3'
        cookie = self.make_cookie(pkey_hash)
        headers = Headers({'Cookie': cookie})
        rv = self.app.get('/', headers=headers)
        assert "Hello {}".format(username) in rv.data
        assert "pkey_hash: {}".format(pkey_hash) in rv.data


if __name__ == '__main__':
    unittest.main()