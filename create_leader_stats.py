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

    print("updated %d leaders records" % len(all_stats))
    conn.commit()
    curs.close()

def create_top20_counts(conn):
    curs = conn.cursor()

    cursor = conn.execute("""
        SELECT leader_id, COUNT(*)
        FROM leader_song_stats
        WHERE lead_rank <= 20 AND lead_count >= 5
        GROUP BY leader_id
    """)
    for (id, count) in cursor:
        curs.execute("UPDATE leaders SET top20_count=? WHERE id=?", [count, id])

    print("updated top20_counts")
    conn.commit()
    curs.close()

def create_location_counts(conn):
    curs = conn.cursor()

    cursor = conn.execute("""
        SELECT leader_id, COUNT(DISTINCT(location_id)) as c
        FROM song_leader_joins
        INNER JOIN minutes_location_joins ON minutes_location_joins.minutes_id = song_leader_joins.minutes_id
        WHERE location_id IS NOT NULL
        GROUP BY leader_id
        ORDER BY c DESC
    """)
    for (id, count) in cursor:
        curs.execute("UPDATE leaders SET location_count=? WHERE id=?", [count, id])

    print("updated location_counts")
    conn.commit()
    curs.close()

def create_stats(conn):
    curs = conn.cursor()

    ranks = defaultdict(list)
    cursor = conn.execute("""
        SELECT leader_id, song_id, COUNT(*) as count
        FROM song_leader_joins
        GROUP BY song_id, leader_id
        ORDER BY song_id, count DESC, leader_id
    """)
    for (leader_id, song_id, count) in cursor:
        ranks[song_id].append((count, leader_id))

    values = []
    for song_id in sorted(ranks.keys()):
        rank = 1
        last_count = 0
        for i, (count, leader_id) in enumerate(ranks[song_id]):
            if count != last_count:
                rank = i + 1
            last_count = count
            values.append((leader_id, song_id, count, rank))

    conn.executemany("INSERT INTO leader_song_stats (leader_id, song_id, lead_count, lead_rank) VALUES (?, ?, ?, ?)", values)

    print("created %d leader_song_stats records" % len(values))
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
    create_top20_counts(db)
    create_location_counts(db)
    db.close()
