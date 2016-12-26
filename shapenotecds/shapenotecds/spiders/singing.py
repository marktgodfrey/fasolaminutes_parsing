# -*- coding: utf-8 -*-
import scrapy
import json
import sqlite3
import difflib
import os
import re
import csv

def open_db():
    conn = sqlite3.connect("../minutes.db")
    conn.text_factory = str
    return conn


class SingingSpider(scrapy.Spider):
    name = "singing"
    allowed_domains = ["shapenotecds.com"]
    # start_urls = (
    # 'http://www.shapenotecds.com/ivey-memorial-liberty-sunday-march-29-2015//',
    # )

    def start_requests(self):
        conn = open_db()
        curs = conn.cursor()

        # reqs = []
        curs.execute('SELECT audio_url FROM minutes WHERE audio_url LIKE \'%shapenotecds.com%\'')
        # curs.execute('SELECT audio_url FROM minutes WHERE id=4903')
        for row in curs.fetchall():
            # reqs.append(self.make_requests_from_url(row[0]))
            if not self.parse_file(row[0]):
                yield self.make_requests_from_url(row[0])

        curs.close()
        conn.close()

        # return reqs


    def parse(self, response):
        sel = scrapy.Selector(response)
        if len(sel.xpath('//script[@class="wp-playlist-script"]/text()')) == 0:
            self.parse_old(response)
        else:
            self.parse_fancy(response)

    def parse_file(self, url):
        m = re.search(r'shapenotecds\.com/([^/]+)', url)
        if m:
            filename = m.group(1) + '.csv'
            if os.path.isfile(filename):
                print "<FILE: %s>" % filename
                with open(filename, 'rb') as f:
                    song_data = list(csv.reader(f))
                    self.parse_section(url, song_data)
                return True

    def parse_old(self, response):
        sel = scrapy.Selector(response)

        sections = sel.xpath('//ol')
        for section in sections:
            song_data = []
            songs = section.xpath('./li')

            for song in songs:
                url = song.xpath('./a/@href').extract()[0]

                pagenum = None
                p = song.xpath('./a/text()').re(r'-(\d{2,3}[tb]?)')
                if p:
                    pagenum = p[0]
                else:
                    p = song.xpath('./a/text()').re(r'\s(\d{2,3}[tb]?)')
                    if p:
                        pagenum = p[0]
                    else:
                        p = song.xpath('./a/text()').re(r'(\d{2,3}[tb]?)')
                        if p:
                            pagenum = p[0]


                if not pagenum:
                    self.logger.warning("no song id: " + song.xpath('./a/text()').extract()[0])
                    continue

                song_data.append((pagenum, url))

            self.parse_section(response.url, song_data)

    def parse_fancy(self, response):
        sel = scrapy.Selector(response)

        sections = sel.xpath('//script[@class="wp-playlist-script"]/text()').extract()
        for songs in sections:
            song_data = []
            p = json.loads(songs)

            with open(str(minutes_id) + '.json', 'w') as f:
                json.dump(p, f, indent=4, separators=(',', ': '))

            songs = p['tracks']
            for song in songs:
                url = song['src']
                pagenum = song['title']
                song_data.append((pagenum, url))

            self.parse_section(response.url, song_data)

    def parse_section(self, audio_url, song_data):
        conn = open_db()
        curs = conn.cursor()

        curs.execute('SELECT id FROM minutes WHERE audio_url=?', [audio_url])
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
<<<<<<< 6cc5d73057642631ea3aab20d947f5d1c0907fc4
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
=======
            if row is not None:
                song_id = row[0]
            if song_id == 0:
                if pagenum[-1:] == 't' or pagenum[-1:] == 'b':
                    #check for song without "t" or "b"
                    curs.execute("SELECT id FROM songs WHERE PageNum=?", [pagenum[0:-1]])
                    row = curs.fetchone()
                    if row is not None:
                        song_id = row[0]
                else:
                    #check for song on "top"
                    curs.execute("SELECT id FROM songs WHERE PageNum=?", [pagenum+'t'])
                    row = curs.fetchone()
                    if row is not None:
                        song_id = row[0]
            if song_id == 0:
                # print "\tno song id! %s"%(pagenum)
                continue

            # print pagenum + " :  " + url
            # print "%d : %d"%(minutes_id, song_id)

            #TODO: check for same song at the same singing (different day)
            curs.execute("UPDATE song_leader_joins SET audio_url=? WHERE minutes_id=? AND song_id=?", (url, minutes_id, song_id))
>>>>>>> fix indents

        conn.commit()
