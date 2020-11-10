import os
from dotenv import load_dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from gbparse import settings
from gbparse.spiders.youla import YoulaSpider
from gbparse.spiders.hh import HHSpider
from gbparse.spiders.instagram_7 import Instagram7Spider

load_dotenv('.env')

if __name__ == '__main__':
    crawl_settings = Settings()
    crawl_settings.setmodule(settings)
    crawl_proc = CrawlerProcess(settings=crawl_settings)
    crawl_proc.crawl(Instagram7Spider, login=os.getenv('USERNAMEE'), enc_password=os.getenv('ENC_PASSWORD'))
    crawl_proc.start()