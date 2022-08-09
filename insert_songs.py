#!/usr/bin/env python
# encoding: utf-8

import csv
import util

def delete_songs(conn):
    curs = conn.cursor()
    curs.execute("DELETE FROM songs")
    conn.commit()
    curs.close()

def insert_songs(conn):
    curs = conn.cursor()

    reader = csv.reader(open('SongData_Denson_1991.txt', 'r'))
    next(reader)  # skip headers
    for row in reader:
        curs.execute('INSERT INTO songs (PageNum, Title, TitleOrdinal, MeterName, MeterCount, SongText, Comments, \
        Comp1First, Comp1Last, Comp1Date, Comp2First, Comp2Last, Comp2Date, CompAlternateEntry, CompBookTitle, \
        CompBookTitleAlternateEntry, Poet1First, Poet1Last, Poet1Date, Poet2First, Poet2Last, Poet2Date, \
        PoetAlternateEntry, PoetBookTitle, PoetBookTitleAlternateEntry) \
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', row)

    conn.commit()
    curs.close()

def add_extras(conn):
    curs = conn.cursor()

    reader = csv.reader(open('song_extras.csv', 'r'))
    next(reader)  # skip headers
    for row in reader:
        curs.execute("UPDATE songs SET Keys=?, Times=?, Orientation=?, ThreeLiner=? WHERE id=?",
                     (row[1], row[2], row[3], row[4], row[0]))

    conn.commit()
    curs.close()

if __name__ == '__main__':
    db = util.open_db()
    delete_songs(db)
    insert_songs(db)
    add_extras(db)
    db.close()
