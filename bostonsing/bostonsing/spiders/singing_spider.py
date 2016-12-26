from scrapy.spider import Spider
from scrapy.selector import Selector

import sqlite3
from urlparse import urlparse, urljoin

def open_db():
    conn = sqlite3.connect("../minutes.db")
    conn.text_factory = str
    return conn

class SingingSpider(Spider):

    name = "singing"
    allowed_domains = ["bostonsing.org"]
    # global g_start_urls
    # g_start_urls = [
    # 	"http://www.bostonsing.org/recordings/alabama-state-2010/",
    # 	"http://www.bostonsing.org/recordings/chattahoochee-2010/",
    # 	"http://www.bostonsing.org/recordings/holly-springs/",
    # 	"http://www.bostonsing.org/recordings/georgia-state/",
    # 	"http://www.bostonsing.org/recordings/piccolo-spoleto/",
    # 	"http://www.bostonsing.org/recordings/new-york-state-2009/",
    # 	"http://www.bostonsing.org/recordings/aldridge-memorial/aldridge-2010/",
    # 	"http://www.bostonsing.org/recordings/aldridge-memorial/aldridge-2011/"
    # ]
    # start_urls = g_start_urls

    def start_requests(self):
        conn = open_db()
        curs = conn.cursor()

        reqs = []
        curs.execute('SELECT audio_url FROM minutes WHERE audio_url LIKE \'%bostonsing.org%\' AND id=3499')
        for row in curs:
            reqs.append(self.make_requests_from_url(row[0]))

        curs.close()
        conn.close()

        return reqs

    def parse(self, response):

        # print g_start_urls
        #
        # minutes_id = 0
        # if response.url == g_start_urls[0]:
        # 	minutes_id = 3499	#AL State 2010
        # elif response.url == g_start_urls[1]:
        # 	minutes_id = 3404	#Chattahoochee 2010
        # elif response.url == g_start_urls[2]:
        # 	minutes_id = 3614	#Holly Spring 2011
        # elif response.url == g_start_urls[3]:
        # 	minutes_id = 3561	#GA State 2011
        # elif response.url == g_start_urls[4]:
        # 	minutes_id = 3342	#Piccolo Spoleto 2010
        # elif response.url == g_start_urls[5]:
        # 	minutes_id = 3192	#NY State 2009
        # elif response.url == g_start_urls[6]:
        # 	minutes_id = 3359	#Aldrige Memorial 2010
        # elif response.url == g_start_urls[7]:
        # 	minutes_id = 3622	#Aldrige Memorial 2011
        #
        # if minutes_id == 0:
        # 	return
        # print minutes_id

        conn = open_db()
        curs = conn.cursor()

        curs.execute('SELECT id FROM minutes WHERE audio_url=?', [response.url])
        row = curs.fetchone()
        minutes_id = row[0]

        base_url = '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(response.url))

        sel = Selector(response)
        songs = sel.xpath('//div[@class="j-module n j-downloadDocument "]')
        for song in songs:
            url = None
            u = song.xpath('.//div[@class="leftDownload"]')[0].xpath('./a/@href').extract()
            if u:
                url = urljoin(base_url, u[0])
                # print url

            pagenum = None

            p = song.xpath('.//div[@class="rightDownload"]/div/div[@class="cc-m-download-file-name"]/text()').re(r'\d{2,3}[tb]?(?=\s)')
            if p:
                pagenum = p[0]
                if pagenum[0] == '0':
                    pagenum = pagenum[1:]
            else:
                print song.xpath('.//div[@class="rightDownload"]/div/div[@class="cc-m-download-file-name"]/text()').extract()

            if pagenum:
                print pagenum

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
                    print "\tno song id! %s"%(pagenum)
                    continue

                print pagenum + ":  " + url

                #TODO: check for same song at the same singing (different day)
                curs.execute("UPDATE song_leader_joins SET audio_url=? WHERE minutes_id=? AND song_id=?", (url, minutes_id, song_id))
                conn.commit()
            else:
                print song

        curs.close()
        conn.close()
