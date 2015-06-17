__title__ = 'TurkeyVulture'
__version__ = '0.0.1'
__author__ = 'Steven Miller'
__license__ = 'Apache 2.0'

__all__ = ['pull_thread_messages']

import facebook
import ConfigParser
import json
import requests
import pymongo
import re
import time
import operator
import urlparse

VULTURE_CONFIG_FILE = 'config/vulture.ini'


class FacebookThread:
    """Facebook Thread is a class that represents a Facebook Messenger Thread conversation

    This class acts as a container and retriever for a Facebook conversation thread. It pulls the thread
    25 messages at a time due to Graph API limitations. Facebook conversations can be very long, so there's an
    option to "pop" the current array of messages in order to process it and save space in memory.

    Attributes:
        _graph (GraphAPI): A GraphAPI client that has access to the thread contents
        _raw_json ({string: {string}}: A dictionary representation of the current thread page object
        thread_id (string): The id of the messenger thread the FacebookThread represents
        _posts ([{string: {string}]): A running array of the posts retrieved
        participants ([{string: {string}]): An array of the participants in the thread
    """

    def __init__(self, graph, thread_id):
        self._graph = graph
        raw_json = self._graph.get_object(thread_id)
        self.participants = raw_json['to']['data']
        self._comments_json = raw_json['comments']

        self._posts = self._data
        self._latest_post_id = self._data[-1]['id'].split('_')[1]
        self.thread_id = thread_id

    # Public conversation puller
    def get_next_page(self):
        if self._next_page_url is None:
            return False
        else:
            next_parse_url = urlparse.urlparse(self._next_page_url)
            next_path = next_parse_url.path
            next_query = dict(urlparse.parse_qsl(next_parse_url.query))

            try:
                next_query.pop('access_token')
            except KeyError:
                # We want to remove the access token, so if it's already been removed or it
                # doesn't exist in the first place then we should be fine
                pass

            self._comments_json = self._graph.get_object(next_path, **next_query)
            self._posts = self._data + self._posts
            return True

    @property
    def _data(self):
        return self._comments_json['data'] if 'data' in self._comments_json else None

    @property
    def _next_page_url(self):
        return self._comments_json['paging']['next'] if 'paging' in self._comments_json else None

    @property
    def posts(self):
        return self._posts

    def pop_posts(self):
        return_posts = self._posts
        self._posts = []
        return return_posts

    def change_access_token(self, access_token):
        self._graph.access_token = access_token


class DatabaseHandler:
    POSTS_COLLECTION_BASE = 'posts'
    PARTICIPANTS_COLLECTION_BASE = 'participants'

    def __init__(self, database_url, database_name, thread_id=None):
        self._db_connection = pymongo.MongoClient(database_url)
        self._db_name = database_name
        if thread_id is not None:
            self._posts_collection_name = self.POSTS_COLLECTION_BASE + '_' + thread_id
            self._participants_collection_name = self.PARTICIPANTS_COLLECTION_BASE + '_' + thread_id
        else:
            self._posts_collection_name = self.POSTS_COLLECTION_BASE
            self._participants_collection_name = self.PARTICIPANTS_COLLECTION_BASE

    def _db(self):
        return self._db_connection[self._db_name]

    def _posts_collection(self):
        return self._db()[self._posts_collection_name]

    def _participants_collection(self):
        return self._db()[self._participants_collection_name]

    def authenticate(self, username, password):
        self._db().authenticate(username, password, mechanism='SCRAM-SHA-1')

    def add_posts(self, post_list):
        self._posts_collection().insert_many(post_list)

    def add_participants(self, participants_list):
        self._participants_collection().insert_many(participants_list)

    def close(self):
        self._db_connection.close()


def main():

    config = ConfigParser.ConfigParser()
    config.read(VULTURE_CONFIG_FILE)

    access_token = config.get('graph.facebook.com', 'AccessToken')
    thread_id = config.get('graph.facebook.com', 'ThreadId')

    mongo_url = config.get('db', 'mongo_url')
    mongo_database = config.get('db', 'database')

    api = facebook.GraphAPI(access_token=access_token, timeout=60)
    stuff = api.get_object(thread_id)
    other_stuff = api.get_object(thread_id + '/comments', until=stuff['comments']['data'][0]['id'].split('_')[1])
    more_other_stuff = api.get_object(thread_id + '/comments', until=other_stuff['data'][0]['id'].split('_')[1])

    print(stuff['comments']['data'][0]['id'].split('_')[1])
    other_data = other_stuff['data']
    other_data.pop()
    print(json.dumps(more_other_stuff, sort_keys=True, indent=4, separators=(',', ': ')))
    print(json.dumps(other_data, sort_keys=True, indent=4, separators=(',', ': ')))
    print(json.dumps(stuff, sort_keys=True, indent=4, separators=(',', ': ')))
    print(stuff['to']['data'])
    thread = FacebookThread(access_token, thread_id, timeout=60)
    graph = facebook.GraphAPI(access_token=access_token, timeout=60)
    thread = FacebookThread(graph, thread_id)
    thread.get_next_page()
    #next_page_exists = thread.get_next_page()
    #while next_page_exists:
    #    try:
    #        next_page_exists = thread.get_next_page()
    #    except facebook.GraphAPIError as fb_error:
    #        if fb_error.result['error']['code'] == 613:
    #            time.sleep(100)
    #       elif fb_error.result['error']['code'] == 190:
    #            new_token = str(raw_input('Please input a new access_token'))
    #            thread.change_access_token(new_token)
    #        else:
    #            raise fb_error

    # api = facebook.GraphAPI(access_token=access_token, timeout=60)
    # stuff = api.get_object(thread_id)
    # other_stuff = api.get_object(thread_id + '/comments', until=stuff['comments']['data'][0]['id'].split('_')[1])
    #more_other_stuff = api.get_object(thread_id + '/comments', until=other_stuff['data'][0]['id'].split('_')[1])

    # print(stuff['comments']['data'][0]['id'].split('_')[1])
    # other_data = other_stuff['data']
    # other_data.pop()
    # print(json.dumps(more_other_stuff, sort_keys=True, indent=4, separators=(',', ': ')))
    # print(json.dumps(other_data, sort_keys=True, indent=4, separators=(',', ': ')))
    # print(json.dumps(stuff, sort_keys=True, indent=4, separators=(',', ': ')))
    # print(stuff['to']['data'])
    #other_stuff['data'].pop()
    #print(json.dumps(other_stuff['data'] + stuff['comments']['data'], sort_keys=True, indent=4, separators=(',', ': ')))
    #print other_stuff
    #[0:len(other_stuff['data']) - 1]

    #db_handler = DatabaseHandler(mongo_url, mongo_database, thread_id=thread_id)
    #db_handler.authenticate(config.get('db', 'username'), config.get('db', 'password'))

    #first_messages = ThreadPage(stuff)
    #second_messages = ThreadPage(other_stuff)
    #print('pulled messages!')

    #db_handler.add_posts(first_messages.data)
    #db_handler.add_posts(second_messages.data)
    #print('added messages')
    #db_handler.close()

    print('It worked!')

    #print(json.dumps(first_messages['comments']['data'], sort_keys=True, indent=4, separators=(',', ': ')))
    #print(first_messages['comments']['paging']['next'])

    #second_messages = requests.get(first_messages['comments']['paging']['next']).json()
    #print(json.dumps(second_messages['data'], sort_keys=True, indent=4, separators=(',', ': ')))
    #print(second_messages['paging']['next'])

    #total_messages = second_messages['data'] + first_messages['comments']['data']

    #all_messages = pull_all_conversation_pages(access_token, thread_id)
    #print(json.dumps(all_messages, sort_keys=True, indent=4, separators=(',', ': ')))


if __name__ == "__main__":
    main()