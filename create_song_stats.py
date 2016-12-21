#!/usr/bin/env python
# encoding: utf-8

import time
import util

def create_stats(conn):
    curs = conn.cursor()

    curs.execute("SELECT DISTINCT year FROM minutes")
    year_rows = curs.fetchall()
    num_years = len(year_rows)
    year_count = 0

    tic = time.time()

    for year_row in year_rows:
        year = year_row[0]
        rank = 1
        curs.execute("SELECT song_id, COUNT(*) FROM song_leader_joins \
            INNER JOIN minutes ON song_leader_joins.minutes_id = minutes.id \
            WHERE minutes.year = ? GROUP BY song_id ORDER BY count(*) DESC", \
            [year])
        song_rows = curs.fetchall()
        for song_row in song_rows:
            song_id = song_row[0]
            lead_count = song_row[1]
            curs.execute("INSERT INTO song_stats (year, song_id, lead_count, \
                rank) VALUES (?,?,?,?)", [year, song_id, lead_count, rank])
            rank = rank + 1
        conn.commit()

        # fill in zeros
        curs.execute("SELECT id FROM songs")
        song_rows = curs.fetchall()
        curs.execute("SELECT DISTINCT year FROM song_stats")
        year_rows = curs.fetchall()
        for song_row in song_rows:
            for year_row in year_rows:
                song_id = song_row[0]
                year = year_row[0]
                curs.execute("SELECT * FROM song_stats WHERE song_id = ? AND \
                    year = ?", [song_id, year])
                if curs.fetchone() is None:
                    curs.execute("INSERT INTO song_stats (year, song_id, \
                        lead_count, rank) VALUES (?,?,0,554)", [year, song_id])
        conn.commit()

        year_count = year_count + 1
        toc = time.time()
        est_remaining = float(toc - tic) / year_count * (num_years - year_count)
        print "est rem: %f" % (est_remaining) # / 60)

    curs.close()

def delete_stats(conn):
    curs = conn.cursor()
    curs.execute("DELETE FROM song_stats")
    curs.execute("DELETE FROM sqlite_sequence WHERE name='song_stats'")
    conn.commit()
    curs.close()

if __name__ == '__main__':
    db = util.open_db()
    delete_stats(db)
    create_stats(db)
    db.close()
