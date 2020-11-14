import json
from datetime import datetime
import scrapy
from ..items import InstagramPostItem, InstagramTagItem, InstagramUserItem

class Instagram8Spider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['www.instagram.com']
    start_urls = ['https://www.instagram.com/']
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    api_url = 'https://www.instagram.com/graphql/query/'
    follow_types = {
        'following': 'edge_follow',
        'followers': 'edge_followed_by',
    }
    query_hash = {
        'tags': '9b498c08113f1e09617a1703c22b2f32',
        'followers': 'c76146de99bb02f6415203be841dd25a',
        'following': 'd04b0a864b4b54837c0d870b0e77e076',
    }

    def __init__(self, login, enc_password, *args, **kwargs):
        self.tags = ['python', 'developers']
        self.users = ['lilpump', 'bos_official']
        self.login = login
        self.enc_passwd = enc_password
        super().__init__(*args, **kwargs)

    def parse(self, response, **kwargs):
        try:
            js_data = self.js_data_extract(response)
            yield scrapy.FormRequest(
                self.login_url,
                method='POST',
                callback=self.parse,
                formdata={
                    'username': self.login,
                    'enc_password': self.enc_passwd,
                },
                headers={'X-CSRFToken': js_data['config']['csrf_token']}
            )
        except AttributeError as e:
            if response.json().get('authenticated'):
                for user in self.users:
                    yield response.follow(f'/{user}/', callback=self.user_page_parse)

    def user_page_parse(self, response):
        pass


    @staticmethod
    def js_data_extract(response):
        script = response.xpath('//script[contains(text(), "window._sharedData =")]/text()').get()
        return json.loads(script.replace("window._sharedData =", '')[:-1])
