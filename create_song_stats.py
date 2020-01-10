#!/usr/bin/env python
# encoding: utf-8

from collections import defaultdict
import util

def build_ranks(conn):
    # ranks[year] = sorted [(count, song_id), ...]
    ranks = defaultdict(list)
    cursor = conn.execute("""
        SELECT song_id, COUNT(*), minutes.Year
        FROM song_leader_joins
        JOIN minutes ON song_leader_joins.minutes_id = minutes.id
        GROUP BY minutes.Year, song_id
        ORDER BY minutes.Year ASC, COUNT(*) DESC, song_id ASC
    """)
    for (song_id, count, year) in cursor:
        ranks[year].append((count, song_id))
    return ranks

def create_stats(conn):
    ranks = build_ranks(conn)
    # values = [(song_id, year, lead_count, rank), ...]
    values = []
    for year in sorted(ranks.keys()):
        rank = 1
        last_count = 0
        for i, (count, song_id) in enumerate(ranks[year]):
            if count != last_count:
                rank = i + 1
            last_count = count
            values.append((song_id, year, count, rank))

    conn.executemany("INSERT INTO song_stats (song_id, year, lead_count, rank) VALUES (?, ?, ?, ?)", values)
    conn.commit()
    print("created %d song_stats records" % len(values))


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
