.PHONY: all createdb fixtures test

all:


createdb:
	sqlite3 authserver/test.db < schema.sql

fixtures:
	sqlite3 authserver/test.db < fixtures.sql

test:
	curl --cookie xoid='{"pkey_hash":"bc040eb5294c5fe63f5cfd28d6961c7db6b9a2bc"}' http://localhost:5000
