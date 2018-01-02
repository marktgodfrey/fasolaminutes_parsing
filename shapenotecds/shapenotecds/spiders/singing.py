# -*- coding: utf-8 -*-
import scrapy
import json
import os
import re

from spider_base import SpiderBase

class SingingSpider(SpiderBase):
    name = "singing"
    allowed_domains = ["shapenotecds.com"]
    # start_urls = (
    # 'http://www.shapenotecds.com/ivey-memorial-liberty-sunday-march-29-2015//',
    # )

    def start_requests(self):
        conn = self.open_db()
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
                self.parse_csv(filename, url)
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

            # with open(str(minutes_id) + '.json', 'w') as f:
            #     json.dump(p, f, indent=4, separators=(',', ': '))

            songs = p['tracks']
            for song in songs:
                url = song['src']
                pagenum = song['title']
                song_data.append((pagenum, url))

            self.parse_section(response.url, song_data)
