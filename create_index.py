#!/usr/bin/env python
# encoding: utf-8

import util

def delete_index(conn):
    curs = conn.cursor()
    curs.execute("DROP INDEX song_index")
    curs.execute("DROP INDEX leader_index")
    curs.execute("DROP INDEX minutes_index")
    conn.commit()
    curs.close()

def create_index(conn):
    curs = conn.cursor()
    curs.execute("CREATE INDEX song_index ON song_leader_joins(song_id)")
    curs.execute("CREATE INDEX leader_index ON song_leader_joins(leader_id)")
    curs.execute("CREATE INDEX minutes_index ON song_leader_joins(minutes_id)")
    conn.commit()
    curs.close()

if __name__ == '__main__':
    db = util.open_db()
    delete_index(db)
    create_index(db)
    db.close()
