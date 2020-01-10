#!/usr/bin/env python
# encoding: utf-8

import csv
import util

def delete_aliases(conn):
    curs = conn.cursor()
    curs.execute("DELETE FROM leader_name_aliases")
    curs.execute("DELETE FROM sqlite_sequence WHERE name='leader_name_aliases'")
    conn.commit()
    curs.close()

def create_aliases(conn):
    f =  open('FaSoLa Minutes Corrections (Responses) - Form Responses.csv', 'r')
    csvreader = csv.reader(f)
    curs = conn.cursor()
    next(csvreader) # skip headers
    for row in csvreader:
        curs.execute("INSERT INTO leader_name_aliases (name, alias, type) VALUES (?,?,?)", [row[2], row[1], row[3]])
    conn.commit()
    curs.close()

def delete_invalid(conn):
    curs = conn.cursor()
    curs.execute("DELETE FROM leader_name_invalid")
    curs.execute("DELETE FROM sqlite_sequence WHERE name='leader_name_invalid'")
    conn.commit()
    curs.close()

def create_invalid(conn):
    f =  open('FaSoLa Minutes Corrections (Responses) - Invalid Names.csv', 'r')
    csvreader = csv.reader(f)
    curs = conn.cursor()
    next(csvreader) # skip headers
    for row in csvreader:
        curs.execute("INSERT INTO leader_name_invalid (name) VALUES (?)", [row[1]])
    conn.commit()
    curs.close()

if __name__ == '__main__':
    db = util.open_db()

    delete_aliases(db)
    create_aliases(db)

    delete_invalid(db)
    create_invalid(db)

    db.close()
