#!/usr/bin/env python
# encoding: utf-8

import sqlite3

def open_db():
    conn = sqlite3.connect("minutes.db")
    return conn
