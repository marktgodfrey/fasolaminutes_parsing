# -*- coding: utf-8 -*-
import scrapy
import json
import sqlite3

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
        for row in curs:
        	# reqs.append(self.make_requests_from_url(row[0]))
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

    def parse_old(self, response):
        sel = scrapy.Selector(response)

        conn = open_db()
        curs = conn.cursor()

        curs.execute('SELECT id FROM minutes WHERE audio_url=?', [response.url])
        row = curs.fetchone()
        minutes_id = row[0]

        songs = sel.xpath('//ol/li')
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
                print "SHIT " + song.xpath('./a/text()').extract()[0]
                continue


            # print pagenum + " :  " + url


            song_id = 0
            curs.execute("SELECT id FROM songs WHERE PageNum=?", [pagenum])
            row = curs.fetchone()
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

        conn.commit()

    def parse_fancy(self, response):
        sel = scrapy.Selector(response)
        s = sel.xpath('//script[@class="wp-playlist-script"]/text()').extract()[0]
        p = json.loads(s)

        conn = open_db()
        curs = conn.cursor()

        curs.execute('SELECT id FROM minutes WHERE audio_url=?', [response.url])
        row = curs.fetchone()
        minutes_id = row[0]

        songs = p['tracks']
        for song in songs:
            url = song['src']
            pagenum = song['title']

            song_id = 0
            curs.execute("SELECT id FROM songs WHERE PageNum=?", [pagenum])
            row = curs.fetchone()
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

        conn.commit()
