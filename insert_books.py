#!/usr/bin/env python
# encoding: utf-8

import util

def delete_books(conn):
    curs = conn.cursor()
    curs.execute("DELETE FROM books")
    conn.commit()
    curs.close()

def insert_books(conn):
    curs = conn.cursor()

    curs.execute('INSERT INTO books (title, year) VALUES ("The Sacred Harp: 1991 Edition", 1991)')
    curs.execute('INSERT INTO books (title, year) VALUES ("The Sacred Harp: 2025 Edition", 2025)')

    conn.commit()
    curs.close()

if __name__ == '__main__':
    db = util.open_db()
    delete_books(db)
    insert_books(db)
    db.close()
