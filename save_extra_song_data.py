#!/usr/bin/env python
# encoding: utf-8

import csv
import util


def save_song_data(conn):
    curs = conn.cursor()

    fieldnames = ['id', 'Keys', 'Times', 'Orientation', 'ThreeLiner']
    with open('song_extras.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        cursor = conn.execute("""
            SELECT id, Keys, Times, Orientation, ThreeLiner
            FROM songs
        """)
        for (song_id, keys, times, orientation, three_liner) in cursor:
            three_liner = three_liner if three_liner else 0
            writer.writerow({'id': song_id,
                             'Keys': keys,
                             'Times': times,
                             'Orientation': orientation,
                             'ThreeLiner': three_liner})

    curs.close()


if __name__ == '__main__':
    db = util.open_db()
    save_song_data(db)
    db.close()
