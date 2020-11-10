import json
from datetime import datetime
import scrapy
from ..items import InstagramPostItem, InstagramTagItem, InstagramUserItem

class Instagram7Spider(scrapy.Spider):
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

    def user_page_parse(self, response, user_data=None, variables=None):
        if user_data is None:
            user_data = self.js_data_extract(response)['entry_data']['ProfilePage'][0]['graphql']['user']
        if variables is None:
            variables = {
                'id': user_data['id'],
                'first': 100,
            }
        for follow_type in self.follow_types.keys():
            url = f'{self.api_url}?query_hash={self.query_hash[follow_type]}&variables={json.dumps(variables)}'
            yield response.follow(url, callback=self.is_following_parse, cb_kwargs={'user_data': user_data,
                                                                                    'follow_type': follow_type,
                                                                                    })

    def is_following_parse(self, response, user_data, follow_type):
        js_data = response.json()['data']['user'][self.follow_types[follow_type]]
        yield from self.follow_person(user_data, js_data['edges'], follow_type)
        if js_data['page_info']['has_next_page']:
            variables = {
                'id': user_data['id'],
                'first': 100,
                'after': js_data['page_info']['end_cursor'],
            }
            yield from self.user_page_parse(response, user_data, variables)


    def follow_person(self, user_data, follow_persons, follow_type):
        for person in follow_persons:
            if follow_type == 'following':
                yield InstagramUserItem(username_id=user_data['id'],
                                    username=user_data['username'],
                                    follow_id=person['node']['id'],
                                    follow_username=person['node']['username'],
                                    )
            else:
                yield InstagramUserItem(username_id=person['node']['id'],
                                    username=person['node']['username'],
                                    follow_id=user_data['id'],
                                    follow_username=user_data['username'],
                                    )

    @staticmethod
    def js_data_extract(response):
        script = response.xpath('//script[contains(text(), "window._sharedData =")]/text()').get()
        return json.loads(script.replace("window._sharedData =", '')[:-1])

    def tag_parse(self, response, **kwargs):
        tag = self.js_data_extract(response)['entry_data']['TagPage'][0]['graphql']['hashtag']

        yield InstagramTagItem(date_of_parse = datetime.now(),
                               data = {'id': tag['id'], 'name': tag['name']},
                               img=tag['profile_pic_url'],
                               )

        yield from self.get_tag_parse(tag, response)

    def pagination_parse(self, response):
        yield from self.get_tag_parse(response, response.json()['data']['hashtag'])

    def get_tag_parse(self, tag, response):
        if tag['edge_hashtag_to_media']['page_info']['has_next_page']:
            variables = {
                'tag_name': tag['name'],
                'first': 100,
                'after': tag['edge_hashtag_to_media']['page_info']['end_cursor']
            }
            url = f'{self.api_url}?query_hash={self.query_hash["tags"]}&variables={json.dumps(variables)}'
            yield response.follow(url, callback=self.pagination_parse)

        yield from self.post_parse(tag)

    @staticmethod
    def post_parse(edges):
        for edge in edges['edge_hashtag_to_media']['edges']:
            yield InstagramPostItem(date_of_parse=datetime.now(),
                                    data=edge['node'],
                                    img=edge['node']['display_url'],
                                    )