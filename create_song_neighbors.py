#!/usr/bin/env python
# encoding: utf-8

import time
import numpy as np
import util


# http://nlp.stanford.edu/IR-book/html/htmledition/mutual-information-1.html


def compute_song_neighbors2(conn):
    curs = conn.cursor()

    curs.execute("SELECT COUNT(id) FROM songs")
    num_songs = curs.fetchone()[0]
    num_song_pairs = num_songs * (num_songs - 1) / 2

    curs.execute("SELECT COUNT(id) FROM leaders")
    num_leaders = curs.fetchone()[0]

    song_leader_counts = np.zeros([num_songs, num_leaders])
    curs.execute("""SELECT leader_id, song_id
        FROM song_leader_joins
        GROUP BY song_id, leader_id""")
    song_stats = curs.fetchall()
    for song_stat in song_stats:
        leader_id = song_stat[0]
        song_id = song_stat[1]
        song_leader_counts[song_id - 1, leader_id - 1] = True

    mi = np.zeros([num_songs, num_songs])
    song_count = 0
    tic = time.time()
    for i in range(num_songs):
        for j in range(i+1, num_songs):
            n11 = np.sum(np.logical_and(song_leader_counts[i, :], song_leader_counts[j, :]))
            n10 = np.sum(np.logical_and(song_leader_counts[i, :], np.logical_not(song_leader_counts[j, :])))
            n01 = np.sum(np.logical_and(song_leader_counts[j, :], np.logical_not(song_leader_counts[i, :])))
            n00 = num_leaders - n11 - n10 - n01

            if n11 > 0:
                mi[i, j] += n11 / num_leaders * np.log2(num_leaders * n11 / (n11 + n10) / (n11 + n01))

            if n01 > 0:
                mi[i, j] += n01 / num_leaders * np.log2(num_leaders * n01 / (n01 + n00) / (n11 + n01))

            if n10 > 0:
                mi[i, j] += n10 / num_leaders * np.log2(num_leaders * n10 / (n11 + n10) / (n10 + n00))

            if n00 > 0:
                mi[i, j] += n00 / num_leaders * np.log2(num_leaders * n00 / (n01 + n00) / (n10 + n00))

            song_count += 1
            if ((song_count - 1) % 10000) == 0:
                toc = time.time()
                est_remaining = float(toc - tic) / song_count * (num_song_pairs - song_count)
                print("%d of %d - est rem: %f" % (song_count, num_song_pairs, est_remaining))

    mi += np.transpose(mi)

    curs.execute("DELETE FROM song_neighbors")

    # num_neighbors = 10
    # for i in range(num_songs):
    #     s = np.argsort(-mi[i, :])
    #     for j in range(num_neighbors):
    #         curs.execute("INSERT INTO song_neighbors (from_song_id, to_song_id, rank) VALUES (?,?,?)",
    #                      (i + 1, s[j] + 1, j + 1))
    # conn.commit()

    # values = [(from_song_id, to_song_id, rank), ...]
    values = []
    num_neighbors = 10
    for i in range(num_songs):
        s = np.argsort(-mi[i, :])
        for j in range(num_neighbors):
            values.append((i + 1, int(s[j] + 1), j + 1))

    conn.executemany("INSERT INTO song_neighbors (from_song_id, to_song_id, rank) VALUES (?, ?, ?)", values)
    conn.commit()
    print("created %d song_neighbors records" % len(values))

    curs.close()


if __name__ == '__main__':
    db = util.open_db()
    compute_song_neighbors2(db)
    db.close()
