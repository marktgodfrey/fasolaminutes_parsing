#!/usr/bin/env python
# encoding: utf-8

import csv
import sqlite3

def open_db():
    conn = sqlite3.connect("minutes.db")
    conn.text_factory = str
    return conn

def delete_aliases():
    conn = open_db()
    curs = conn.cursor()
    curs.execute("DELETE FROM leader_name_aliases")
    curs.execute("DELETE FROM sqlite_sequence WHERE name='leader_name_aliases'")
    conn.commit()
    curs.close()
    conn.close()

def create_aliases():
    conn = conn = open_db()
    f =  open('FaSoLa Minutes Corrections (Responses) - Form Responses.csv', 'rb')
    csvreader = csv.reader(f)
    curs = conn.cursor()
    csvreader.next() # skip headers
    for row in csvreader:
        curs.execute("INSERT INTO leader_name_aliases (name, alias, type) VALUES (?,?,?)", [row[2], row[1], row[3]])
    conn.commit()
    curs.close()
    conn.close()

def delete_invalid():
    conn = open_db()
    curs = conn.cursor()
    curs.execute("DELETE FROM leader_name_invalid")
    curs.execute("DELETE FROM sqlite_sequence WHERE name='leader_name_invalid'")
    conn.commit()
    curs.close()
    conn.close()

def create_invalid():
    conn = open_db()
    f =  open('FaSoLa Minutes Corrections (Responses) - Invalid Names.csv', 'rb')
    csvreader = csv.reader(f)
    curs = conn.cursor()
    csvreader.next() # skip headers
    for row in csvreader:
        curs.execute("INSERT INTO leader_name_invalid (name) VALUES (?)", [row[1]])
    conn.commit()
    curs.close()
    conn.close()

if __name__ == '__main__':
    delete_aliases()
    create_aliases()

    delete_invalid()
    create_invalid()
