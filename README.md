# parsing minutes
## run the scripts in this order!
`insert_minutes.py` -> (can change to current year, eg 2016)  
`create_aliases.py`  
`parse_minutes.py`
`insert_locations.py`
`create_leader_stats.py`
`create_song_stats.py`
`create_song_neighbors.py`
`map_minutes_audio.py`  
`cd ./bostonsing; scrapy crawl singing`
`cd ./shapenotecds; scrapy crawl singing`
`cd ./phillysacredharp; scrapy crawl singing`
`cd ./cork; map_audio.py`
`cd ./archiveorg; map_audio.py`
`create_index.py`
