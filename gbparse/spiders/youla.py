import re
import base64
import scrapy
from urllib.parse import unquote
from pymongo import MongoClient


class YoulaSpider(scrapy.Spider):
    name = 'youla'
    allowed_domains = ['auto.youla.ru']
    start_urls = ['https://auto.youla.ru/']
    xpath = {
        'brands': '//div[@class="TransportMainFilters_brandsList__2tIkv"]//a[@class="blackLink"]/@href',
        'ads': '//div[@id="serp"]//article//a[@data-target="serp-snippet-title"]/@href',
        'pagination': '//div[contains(@class, "Paginator_block")]/a/@href',
    }

    db_client = MongoClient('mongodb://localhost:27017')

    def parse(self, response, **kwargs):
        for url in response.xpath(self.xpath['brands']):
            yield response.follow(url, callback=self.brand_parse)

    def brand_parse(self, response, **kwargs):
        for url in response.xpath(self.xpath['pagination']):
            yield response.follow(url, callback=self.brand_parse)

        for url in response.xpath(self.xpath['ads']):
            yield response.follow(url, callback=self.ads_parse)

    def ads_parse(self, response, **kwargs):
        ads_template = {
            'name': '//div[contains(@class, "AdvertCard_advertTitle")]/text()',
            'images': '//div[contains(@class, "PhotoGallery_block")]//img/@src',
            'price': '//div[contains(@class, "AdvertCard_price")]/text()',
            'parametres': {
                            'year_of_issue': '//div[contains(@data-target, "advert-info-year")]/a/text()',
                            'mileage': '//div[contains(@data-target, "advert-info-mileage")]/text()',
                            'bodytype': '//div[contains(@data-target, "advert-info-bodyType")]/a/text()',
                            'transmission': '//div[contains(@data-target, "advert-info-transmission")]/text()',
                            'engine': '//div[contains(@data-target, "advert-info-engineInfo")]/text()',
                            'steering_wheel': '//div[contains(@data-target, "advert-info-wheelType")]/text()',
                            'color': '//div[contains(@data-target, "advert-info-color")]/text()',
                            'driving_type': '//div[contains(@data-target, "advert-info-driveType")]/text()',
                            'power': '//div[contains(@data-target, "advert-info-enginePower")]/text()',
                            'vin': '//div[contains(@data-target, "advert-info-vinCode")]/text()',
                            'is_custom': '//div[contains(@data-target, "advert-info-isCustom")]/text()',
                            'owners': '//div[contains(@data-target, "advert-info-owners")]/text()',
                          },
            'description': '//div[contains(@class, "AdvertCard_descriptionInner")]/text()',

        }

        product = {}

        for key, value in ads_template.items():
            try:
                if key == 'name':
                    product[key] = (response.xpath(value).extract_first()).split(',')[0]
                if key == 'images':
                    product[key] = response.xpath(value).extract()
                if key == 'price':
                    product[key] = response.xpath(value).extract_first()
                    product[key] = float(''.join(product[key].split('\u2009')))
                for key_2, value_2 in ads_template['parametres'].items():
                    try:
                        product[key_2] = response.xpath(value_2).extract_first()
                    except Exception:
                        product[key_2] = None
                if key == 'description':
                    product[key] = response.xpath(value).extract_first()
            except Exception:
                product[key] = None
                print(1)

        seller, phone_num = self.js_decoder(response)
        product['seller'] = seller
        product['phone'] = phone_num

        self.save_to(product)

    def js_decoder(self, response, **kwargs):
        find_js = response.xpath('//script[contains(text(), "window.transitState =")]/text()').get()
        find_id = re.compile(r"youlaId%22%2C%22([0-9|a-zA-Z]+)%22%2C%22avatar")
        person = re.findall(find_id, find_js)
        seller = f'https://youla.ru/user/{person[0]}' if person else None

        find_seller_phone = re.compile(r"phone%22%2C%22([0-9a-zA-Z]{33}w%3D%3D)%22%2C%22time")
        encoded_phone = re.findall(find_seller_phone, find_js)
        encoded_phone_dec_1 = base64.b64decode(unquote(encoded_phone[0]).encode('utf-8'))
        encoded_phone_dec_2 = base64.b64decode(encoded_phone_dec_1)
        phone_num = encoded_phone_dec_2.decode('utf-8')

        return seller, phone_num

    # процедура соранения в БД
    def save_to(self, product):
        db = self.db_client['youla_parse']
        collection = db['youla_auto']
        collection.insert_one(product)