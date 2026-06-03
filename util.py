#!/usr/bin/env python
# encoding: utf-8

import sqlite3
import os

def open_db():
    conn = sqlite3.connect(os.environ.get("MINUTES_DB", "minutes.db"))
    return conn
