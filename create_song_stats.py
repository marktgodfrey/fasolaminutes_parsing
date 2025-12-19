#!/usr/bin/env python
# encoding: utf-8

from collections import defaultdict
import util


def build_ranks(conn):
    # ranks[year] = sorted [(count, song_id), ...]
    counts = build_counts(conn)
    ranks = defaultdict(list)
    for song_id, yearcount in counts.items():
        for year, count in yearcount.items():
            ranks[year].append((count, song_id))
    for data in ranks.values():
        data.sort(reverse=True)
    return ranks


def build_counts(conn):
    curs = conn.cursor()
    # counts[song_id][year] = count
    counts = {}
    years = conn.execute("SELECT DISTINCT year FROM minutes").fetchall()
    for song_id, in db.execute("SELECT id FROM songs"):
        counts[song_id] = {}
        for year, in years:
            counts[song_id][year] = 0

    # Get lessons by song and year; compute counts
    cursor = db.execute("""
        SELECT DISTINCT minutes_id  || ':' || lesson_id, song_id, minutes.Year
        FROM song_leader_joins
        JOIN minutes ON song_leader_joins.minutes_id = minutes.id""")
    for lesson_id, song_id, year in cursor:
        counts[song_id][year] += 1

    conn.commit()
    curs.close()

    return counts


def create_stats(conn):
    ranks = build_ranks(conn)
    # values = [(song_id, year, lesson_count, rank), ...]
    values = []
    for year in sorted(ranks.keys()):
        rank = 1
        last_count = 0
        for i, (count, song_id) in enumerate(ranks[year]):
            if count != last_count:
                rank = i + 1
            last_count = count
            values.append((song_id, year, count, rank))

    conn.executemany("INSERT INTO song_stats (song_id, year, lesson_count, rank) VALUES (?, ?, ?, ?)", values)
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
