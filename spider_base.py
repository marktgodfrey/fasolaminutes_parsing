# -*- coding: utf-8 -*-
import scrapy
import sqlite3
import difflib
import os
import re
import csv

class SpiderBase(scrapy.Spider):
    def open_db(self):
        # This is run in a subdirectory (bostonsing, or shapenotecds)
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'minutes.db'))
        conn.text_factory = str
        return conn

    def start_requests(self):
        for url in self.get_audio_urls():
            if not self.parse_file(url):
                yield scrapy.Request(url=url, callback=self.parse)

    def get_audio_urls(self):
        conn = self.open_db()

        # Build a query to get audio_urls from that are in allowed_domains
        domains = ['%' + d + '/%' for d in self.allowed_domains]
        query = 'SELECT audio_url FROM minutes WHERE '
        query += ' OR '.join('audio_url LIKE ?' for d in domains)

        urls = []
        for row in conn.execute(query, domains):
            urls.extend(row[0].split(','))

        conn.close()
        return urls

    def parse_file(self, url):
        # Build the regex to extract a filename from a url
        pat = getattr(self, 'csv_pattern', None)
        if pat is None:
            pat = '(?:%s)/(.*)' % '|'.join(self.allowed_domains)
        m = re.search(pat, url)
        if m:
            # Strip trailing / and replace any others with '-'
            filename = re.sub(r'/$', '', m.group(1)) + '.csv'
            filename = filename.replace('/', '-')
            # Try to parse the file
            if os.path.isfile(filename):
                self.parse_csv(filename, url)
                return True

    def parse_csv(self, filename, url):
        with open(filename, 'r') as f:
            self.logger.info('parsing csv file: %s' % filename)
            song_data = list(csv.reader(f))
            self.parse_section(url, song_data)

    def parse_section(self, audio_url, song_data):
        self.logger.info("Parsing %s" % (audio_url))
        conn = self.open_db()
        curs = conn.cursor()

        curs.execute(
            'SELECT id FROM minutes WHERE audio_url=? OR audio_url LIKE ? OR audio_url LIKE ? OR audio_url LIKE ?',
            [audio_url, audio_url + ',%', '%,' + audio_url, '%,' + audio_url + ',%'])

        row = curs.fetchone()
        if not row:
            self.logger.error("no minutes found for audio_url: %s" % (audio_url))
            return

        minutes_id = row[0]

        # make lists of recording urls and song ids
        songs = []
        pages = []
        urls = []
        for pagenum, url in song_data:
            pagenum = pagenum.lower()
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
                self.logger.info("update: %5s %5r %s" % (pagenum, join_ids, url))

        conn.commit()
