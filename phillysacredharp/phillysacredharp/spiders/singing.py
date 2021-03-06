# -*- coding: utf-8 -*-
import scrapy
import json
import os
import re

from spider_base import SpiderBase

class SingingSpider(SpiderBase):
    name = "singing"
    allowed_domains = ["phillysacredharp.org"]

    def start_requests(self):
        for url in self.get_audio_urls():
            if not self.parse_file(url):
                # Keystone recordings are all on the same page, so we split
                # them up by using a url hash. Because these will resolve to
                # the same url and scrapy does duplicate filtering, we need
                # to set dont_filter
                request = scrapy.Request(url, dont_filter=True)
                request.meta['original_url'] = url
                m = re.search(r'#(\d+)$', url)
                if m:
                    request.meta['year'] = m.group(1)
                yield request

    def parse(self, response):
        year = response.meta.get('year')
        sel = scrapy.Selector(response)

        sections = sel.xpath('//script[@class="wp-playlist-script"]/text()').extract()
        for songs in sections:
            song_data = []
            p = json.loads(songs)

            songs = p['tracks']
            for song in songs:
                if year and year not in song['meta']['artist'] and year not in song['meta']['album']:
                    continue

                url = song['src']
                m = re.search(r'^(\d+[tb]?)', song['title'])
                if m:
                    pagenum = m.group()
                    song_data.append((pagenum, url))
                else:
                    self.logger.warning("No song found in: " + song['title'])

            if song_data:
                self.parse_section(response.meta['original_url'], song_data)
