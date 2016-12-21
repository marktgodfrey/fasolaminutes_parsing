#!/usr/bin/env python
# encoding: utf-8

import time
from numpy import array, log2
import util

def count_leads(conn, leader_id):
    curs = conn.cursor()
    curs.execute("SELECT songs.id, COUNT(*) as count FROM song_leader_joins INNER JOIN songs ON song_leader_joins.song_id = songs.id WHERE leader_id=? GROUP BY song_id ORDER BY count DESC", [leader_id])
    rows = curs.fetchall()
    l = {}
    l['leader_id'] = leader_id
    l['songs'] = []
    for row in rows:
        song_id = row[0]
        lead_count = row[1]
        l['songs'].append({'song_id': song_id, 'lead_count': lead_count})
    curs.close()
    return l

def count_total_leads(conn, leader_id):
    curs = conn.cursor()
    curs.execute("SELECT lead_count FROM leader_song_stats WHERE leader_id=?", [leader_id])
    rows = curs.fetchall()
    l = {}
    l['leader_id'] = leader_id
    lead_counts = []
    for row in rows:
        lead_count = row[0]
        lead_counts.append(float(lead_count))
    curs.close()
    lc = array(lead_counts)
    l['lead_count'] = sum(lc)
    lcnorm = lc / sum(lc)
    l['song_entropy'] = sum(lcnorm * log2(lcnorm)) / -9.1137421660491889
    return l


def create_counts(conn):
    curs = conn.cursor()
    curs.execute("SELECT id FROM leaders")
    rows = curs.fetchall()

    num_leaders = len(rows)
    leader_count = 0

    tic = time.time()

    for row in rows:
        leader_id = row[0]
        l = count_total_leads(conn, leader_id)
        # note this is funny looking because i was trying
        # to make the function mappable so we could support multiprocessing
        leader_id = l['leader_id']
        lead_count = l['lead_count']
        song_entropy = l['song_entropy']
        curs.execute("UPDATE leaders SET lead_count=?, song_entropy=? WHERE id=?", [lead_count, song_entropy, leader_id])
        conn.commit()
        leader_count += 1

        if (int(leader_count) % 1000) == 0:
            toc = time.time()
            est_remaining = float(toc - tic) / leader_count * (num_leaders - leader_count)
            print "est rem: %f" % (est_remaining) # / 60)

    curs.close()

def create_stats(conn):
    curs = conn.cursor()

    curs.execute("SELECT id FROM leaders")
    rows = curs.fetchall()

    num_leaders = len(rows)
    leader_count = 0

    tic = time.time()

    for row in rows:
        leader_id = row[0]
        l = count_leads(conn, leader_id)
        for s in l['songs']:
            song_id = s['song_id']
            lead_count = s['lead_count']
            curs.execute("INSERT INTO leader_song_stats (song_id, leader_id, lead_count) VALUES (?,?,?)", [song_id, leader_id, lead_count])
        conn.commit()
        leader_count += 1
        if (int(leader_count) % 1000) == 0:
            toc = time.time()
            est_remaining = float(toc - tic) / leader_count * (num_leaders - leader_count)
            print "est rem: %f" % (est_remaining) # / 60)

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
