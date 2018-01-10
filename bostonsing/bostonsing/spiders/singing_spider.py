from scrapy.selector import Selector
from urlparse import urlparse, urljoin

from spider_base import SpiderBase

class SingingSpider(SpiderBase):

    name = "singing"
    allowed_domains = ["bostonsing.org"]
    csv_pattern = r'bostonsing\.org/recordings/(.*)'
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

        base_url = '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(response.url))

        song_data = []

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
                song_data.append((pagenum, url))
            else:
                print song

        if song_data:
            self.parse_section(response.url, song_data)
        else:
            print "NO SONGS", response.url
