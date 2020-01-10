#!/usr/bin/env python
# encoding: utf-8

import csv
import util

def map_minutes_audio(conn):
    curs = conn.cursor()

    reader = csv.reader(open("minutes_audio.csv", 'r'))
    next(reader) # skip headers
    for row in reader:
        curs.execute("UPDATE minutes SET audio_url=? WHERE Name LIKE ? AND \
            Date LIKE ?", (row[2], row[0], row[1]))

    conn.commit()
    curs.close()

if __name__ == '__main__':
    db = util.open_db()
    map_minutes_audio(db)
    db.close()
