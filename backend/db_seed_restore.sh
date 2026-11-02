#!/bin/bash
# Runs once, from /docker-entrypoint-initdb.d/, on the Mongo image's first start
# (before it accepts external connections). DockerfileMongo copies db_seed/ into
# /opt, so /opt holds one directory per database (here /opt/staycation/*.bson);
# `mongorestore --drop /opt` treats /opt as a dump root and restores the
# `staycation` database, dropping each collection first so a rebuild is clean.
set -e
mongorestore --drop /opt
