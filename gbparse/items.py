# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class GbparseItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class HHVacancyItem(scrapy.Item):
    _id = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    salary = scrapy.Field()
    description = scrapy.Field()
    skills = scrapy.Field()
    hh_company_url = scrapy.Field()

class HHCompanyItem(scrapy.Item):
    _id = scrapy.Field()
    url = scrapy.Field()
    company_name = scrapy.Field()
    company_url = scrapy.Field()
    field_of_activities = scrapy.Field()
    desc_company = scrapy.Field()

class InstagramTagItem(scrapy.Item):
    _id = scrapy.Field()
    date_of_parse = scrapy.Field()
    data = scrapy.Field()
    img = scrapy.Field()

class InstagramPostItem(scrapy.Item):
    _id = scrapy.Field()
    date_of_parse = scrapy.Field()
    data = scrapy.Field()
    img = scrapy.Field()