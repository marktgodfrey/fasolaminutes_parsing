from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request

import os
import sqlite3
import re

class SingingsSpider(BaseSpider):

	name = "allsingings"
	allowed_domains = ["bostonsing.org"]
	start_urls = [
		"http://www.bostonsing.org/index/sources/"
	]
	
	def parse(self, response):		
		hxs = HtmlXPathSelector(response)
		sites = hxs.select("//div[@class='n j-table']//a/@href").extract()
		for site in sites:
			print site
			if site[0:25] == 'http://www.bostonsing.org':
				yield Request(site, callback=self.parse_singing)
			else:
				#TODO: deal with other sites
				pass
				
	def parse_singing(self, response):
		
		hxs = HtmlXPathSelector(response)
		
		s = hxs.select("//div[@class='n j-header']/h1/text()").extract()
		if not s:
			s = hxs.select("//div[@class='n j-text']/h1/text()").extract()
			if not s:
				return
			
			s = s[0]
			
			ss = hxs.select("//div[@class='n j-text']//p/text()").extract()
			if not ss:
				return
			year = None
			for sss in ss:
				ys = re.search('(19|20)\d{2}', sss)
				if ys:
					year = ys.group(0)
					break
			if not year:
				return
		else:		
			s = s[0]
			year = None
			ys = re.search('(19|20)\d{2}', s)
			if ys:
				year = ys.group(0)
			if not year:
				ss = hxs.select("//div[@class='n j-text']//p/text()").extract()
				if not ss:
					return
				year = None
				for sss in ss:
					ys = re.search('(19|20)\d{2}', sss)
					if ys:
						year = ys.group(0)
						break
				if not year:
					return
			
		tokens = re.findall('(?!Memorial|Singing|All|Day|Convention|Annual|Sacred|Harp|Session)[A-Z]\w+', s)
		
		ts = '%'
		for t in tokens:
			ts += t + '%'
		
		conn = sqlite3.connect("/Users/mark/Documents/sacredharp/minutes_data/minutes.db")
		conn.text_factory = str
		curs = conn.cursor()
		
		print ts
		print year
		curs.execute('SELECT id FROM minutes WHERE name LIKE ? AND year=? AND isDenson=1', [ts,year])
		row = curs.fetchone()
		if row:
			print "Minutes ID: %d"%row[0]
			curs.execute("UPDATE minutes SET audio_url=? WHERE id=?", (response.url,row[0]))
			conn.commit()
		else:
			print "Not Found!"
		
		
		curs.close()
		conn.close()
		
