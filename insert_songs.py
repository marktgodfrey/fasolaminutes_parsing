#!/usr/bin/env python
# encoding: utf-8

import csv
import json

import util

REPLACE_SONGS = ['37t', '78', '211']
IGNORE_SONGS = ['24t', '24b', '25']

def pagenum_convert(pagenum_sort):
    if '.' in pagenum_sort:
        pagenum, sort_idx = pagenum_sort.split('.')
        if sort_idx == '1':
            return pagenum + 't'
        elif sort_idx == '2':
            return pagenum + 'b'
        else:
            print(f'unrecognized sort index: {sort_idx}')
            return pagenum
    else:
        return pagenum_sort

def insert_song(curs, song):
    curs.execute('INSERT INTO songs (title, meter, music_attribution) \
                VALUES (?,?,?)', (song['title'], song['meter'], song['composer']))
    song_id = curs.lastrowid
    return song_id

def insert_join(curs, song, book_id, song_id):
    curs.execute('INSERT INTO book_song_joins (book_id, song_id, page_num, text, words_attribution, keys, times, orientation) \
                                                        VALUES (?,?,?,?,?,?,?,?)',
                 (book_id, song_id, song['pagenum'], song['text'], song['poet'], song['keys'], song['times'], song['orientation']))

def delete_songs(conn):
    curs = conn.cursor()
    curs.execute("DELETE FROM songs")
    curs.execute("DELETE FROM book_song_joins")
    conn.commit()
    curs.close()

def insert_songs(conn):
    curs = conn.cursor()

    with open('SongData_1991.json') as jsonfile:
        songs91 = json.load(jsonfile)
        songs91_map = {}
        for song in songs91:
            songs91_map[song['pagenum']] = song

    with open('SongData_2025.json') as jsonfile:
        songs25 = json.load(jsonfile)
        songs25_map = {}
        for song in songs25:
            songs25_map[song['pagenum']] = song

    # this gives us time signatures
    with open('New Song Data - Mode of Time and 3-Liner.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            song = songs25_map[pagenum_convert(row['Page in 2025'])]
            song['times'] = row['Time Mode']
            # print(song)
        for song in songs25_map.values():
            if not 'times' in song:
                print(f'missing time mode! {song["pagenum"]}')

    curs.execute('SELECT id FROM books WHERE Title == "The Sacred Harp: 1991 Edition"')
    book_id_91 = curs.fetchone()[0]

    curs.execute('SELECT id FROM books WHERE Title == "The Sacred Harp: 2025 Edition"')
    book_id_25 = curs.fetchone()[0]

    with open("SongData_2025_translation_table.tsv") as tsvfile:
        reader = csv.DictReader(tsvfile, delimiter="\t")
        for row in reader:
            action = row['Action']
            pagenum_91 = pagenum_convert(row['Page in 1991'])
            pagenum_25 = pagenum_convert(row['Page in 2025'])

            # since these songs have totally new lyrics, treat as new songs
            if pagenum_25 in REPLACE_SONGS:
                action = 'replace'

            song_91 = songs91_map[pagenum_91] if pagenum_91 in songs91_map else None
            song_25 = songs25_map[pagenum_25] if pagenum_25 in songs25_map else None
            
            # | `keep`          | The song is in both the 1991 and 2025 editions, with the same page number.                           |
            # | `replace`       | The song on the page in the 1991 edition is replaced by the song(s) on the page in the 2025 edition. |
            # | `replace-inner` | Subsequent songs replacing the song on this page in the 1991 edition.                                |
            # | `renumber`      | The song in the 1991 edition has been kept, but has been moved or renumbered.                        |
            # | `insert`        | A new song was inserted at this page location because of new space available.                        |
            # | `new`           | A new page was added to the 2025 edition.                                                            |
            # | `remove`        | The page was removed (as a song) in the 2025 edition.                                                |

            # TODO: three-liner
            if action == "keep" or action == "renumber":
                # inserting only 2025 song for both books, NOTE may be different meter and music_attribution
                song_id = insert_song(curs, song_25)
                insert_join(curs, song_91, book_id_91, song_id)
                insert_join(curs, song_25, book_id_25, song_id)
            elif action == "replace":
                # inserting both songs to both books
                song_id_91 = insert_song(curs, song_91)
                song_id_25 = insert_song(curs, song_25)
                insert_join(curs, song_91, book_id_91, song_id_91)
                insert_join(curs, song_25, book_id_25, song_id_25)
            elif action == "replace-inner" or action == "insert" or action == "new":
                # inserting new 2025 song
                song_id = insert_song(curs, song_25)
                insert_join(curs, song_25, book_id_25, song_id)
            elif action == "remove":
                # inserting only 1991 song
                if pagenum_91 not in IGNORE_SONGS:
                    song_id = insert_song(curs, song_91)
                    insert_join(curs, song_91, book_id_91, song_id)

    conn.commit()
    curs.close()

if __name__ == '__main__':
    db = util.open_db()
    delete_songs(db)
    insert_songs(db)
    db.close()
