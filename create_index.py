#!/usr/bin/env python
# encoding: utf-8

import sqlite3

def open_db():
    conn = sqlite3.connect("minutes.db")
    conn.text_factory = str
    return conn

def delete_index():
    conn = open_db()
    curs = conn.cursor()
    curs.execute("DROP INDEX song_index")
    curs.execute("DROP INDEX leader_index")
    curs.execute("DROP INDEX minutes_index")
    conn.commit()
    curs.close()
    conn.close()

def create_index():
    conn = open_db()
    curs = conn.cursor()
    curs.execute("CREATE INDEX song_index ON song_leader_joins(song_id)")
    curs.execute("CREATE INDEX leader_index ON song_leader_joins(leader_id)")
    curs.execute("CREATE INDEX minutes_index ON song_leader_joins(minutes_id)")
    conn.commit()
    curs.close()
    conn.close()

if __name__ == '__main__':
    delete_index()
    create_index()
