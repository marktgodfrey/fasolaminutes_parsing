#!/usr/bin/env python
# encoding: utf-8

import time
from numpy import array, log2
from collections import defaultdict
import util

def count_total_leads(leader_id, counts):
    lc = array(counts, dtype=float)
    lcnorm = lc / sum(lc)
    lead_count = sum(lc)
    song_entropy = sum(lcnorm * log2(lcnorm)) / -9.1137421660491889
    return lead_count, song_entropy

def create_counts(conn):
    curs = conn.cursor()

    # Read all leader_song_stats at once
    all_stats = defaultdict(list)
    for (id, count) in curs.execute("SELECT leader_id, lead_count FROM leader_song_stats"):
        all_stats[id].append(count)

    for (id, counts) in all_stats.items():
        lead_count, song_entropy = count_total_leads(id, counts)
        curs.execute("UPDATE leaders SET lead_count=?, song_entropy=? WHERE id=?", [lead_count, song_entropy, id])

    print "updated %d leaders records" % len(all_stats)
    conn.commit()
    curs.close()

def create_stats(conn):
    curs = conn.cursor()
    curs.execute("""
        INSERT INTO leader_song_stats (leader_id, song_id, lead_count)
        SELECT leader_id, song_id, COUNT(*) as count
        FROM song_leader_joins
        GROUP BY leader_id, song_id
        ORDER BY leader_id, count DESC
    """)
    print "created %d leader_song_stats records" % curs.rowcount
    conn.commit()
    curs.close()

def delete_stats(conn):
    curs = conn.cursor()
    curs.execute("DELETE FROM leader_song_stats")
    curs.execute("DELETE FROM sqlite_sequence WHERE name='leader_song_stats'")
    conn.commit()
    curs.close()

if __name__ == '__main__':
    db = util.open_db()
    delete_stats(db)
    create_stats(db)
    create_counts(db)
    db.close()
