# -*- coding: utf-8 -*-
import scrapy
import sqlite3
import difflib
import os
import csv

class SpiderBase(scrapy.Spider):
    def open_db(self):
        # This is run in a subdirectory (bostonsing, or shapenotecds)
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'minutes.db'))
        conn.text_factory = str
        return conn

    def parse_csv(self, filename, url):
        with open(filename, 'rb') as f:
            song_data = list(csv.reader(f))
            self.parse_section(url, song_data)

    def parse_section(self, audio_url, song_data):
        conn = self.open_db()
        curs = conn.cursor()

        curs.execute(
            'SELECT id FROM minutes WHERE audio_url=? OR audio_url LIKE ? OR audio_url LIKE ? OR audio_url LIKE ?',
            [audio_url, audio_url + ',%', '%,' + audio_url, '%,' + audio_url + ',%'])

        row = curs.fetchone()
        minutes_id = row[0]

        # make lists of recording urls and song ids
        songs = []
        pages = []
        urls = []
        for pagenum, url in song_data:
            altpage = ''
            if pagenum[-1:] in ('t', 'b'):
                altpage = pagenum[:-1]
            else:
                altpage = pagenum + 't'

            curs.execute("SELECT id FROM songs WHERE PageNum IN (?, ?)", [pagenum, altpage])
            row = curs.fetchone()
            if row:
                song_id = row[0]
                songs.append(song_id)
                urls.append(url)
                pages.append(pagenum)
            else:
                self.logger.warning("no song id: " + pagenum)

        # make list of songs and ids from the minutes
        minutes_songs = []
        minutes_ids = []
        curs.execute("SELECT id, song_id FROM song_leader_joins WHERE minutes_id=?", [minutes_id])
        for id, song_id in curs:
            if not minutes_songs or minutes_songs[-1] != song_id:
                minutes_songs.append(song_id)
                minutes_ids.append([id])
            else:
                minutes_ids[-1].append(id)

        # get the longest subsequence from recordings and minutes
        s = difflib.SequenceMatcher(a=songs, b=minutes_songs)
        last_a = 0
        for a, b, n in s.get_matching_blocks():
            for pagenum, url in zip(pages[last_a:a], urls[last_a:a]):
                self.logger.warning("skip: %5s %s" % (pagenum, url))
            last_a = a+n
            for pagenum, url, join_ids in zip(pages[a:a+n], urls[a:a+n], minutes_ids[b:b+n]):
                for id in join_ids:
                    curs.execute("UPDATE song_leader_joins SET audio_url=? WHERE id=?", (url, id))
                    self.logger.info("update: %5s %5s %s" % (id, pagenum, url))

        conn.commit()
