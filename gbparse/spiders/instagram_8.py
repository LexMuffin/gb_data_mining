import json
from datetime import datetime
import scrapy
from ..items import InstagramFollowItem

class Instagram8Spider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['www.instagram.com']
    start_urls = ['https://www.instagram.com/']
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    api_url = '/graphql/query/'
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
        #self.tags = ['python', 'developers']
        #self.users = ['lilpump', 'bos_official']
        self.users = ['zidane']
        self.target = 'vindiesel'
        self.find = 0
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
        user_page = self.js_data_extract(response)['entry_data']['ProfilePage'][0]['graphql']['user']
        variables = {
            'id': user_page['id'],
            'first': 100,
        }

        yield from self.user_follow_parse(response, user_page, variables, follow_type='following')
        yield from self.user_follow_parse(response, user_page, variables, follow_type='followers')

    def user_follow_parse(self, response, user_page, variables, follow_type):
        url = f'{self.api_url}?query_hash={self.query_hash[follow_type]}&variables={json.dumps(variables)}'

        yield response.follow(url, callback=self.followings_parse, cb_kwargs={'user_page': user_page,
                                                                              'follow_type':follow_type,
                                                                              })

    def followings_parse(self, response, user_page, follow_type):
        js_data = response.json()['data']['user'][self.follow_types[follow_type]]

        yield from self.follow_person(response, user_page, js_data['edges'], follow_type)

        if js_data['page_info']['has_next_page']:
            variables = {
                'id': user_page['id'],
                'first': 100,
                'after': js_data['page_info']['end_cursor'],
            }
            yield from self.user_follow_parse(response, user_page, variables, follow_type)

    def follow_person(self, response, user_page, follow_users, follow_type):
        for user in follow_users:
            if follow_type == 'followings':
                yield InstagramFollowItem(username_id = user_page['id'],
                                          username = user_page['username'],
                                          follow_id = user['node']['id'],
                                          follow_name = user['node']['username'],
                                          )
                if user['node']['username'] == self.target:
                    self.find = 1

            elif follow_type == 'followers':
                yield InstagramFollowItem(username_id = user['node']['id'],
                                          username = user['node']['username'],
                                          follow_id = user_page['id'],
                                          follow_name = user_page['username'],
                                          )
                if not self.find:
                    yield response.follow(f'{self.start_urls[0]}{user["node"]["username"]}/', callback=self.user_page_parse)

    @staticmethod
    def js_data_extract(response):
        script = response.xpath('//script[contains(text(), "window._sharedData =")]/text()').get()
        return json.loads(script.replace("window._sharedData =", '')[:-1])
