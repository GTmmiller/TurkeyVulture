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

VULTURE_CONFIG_FILE = 'config/vulture.ini'


class ThreadPage:
    def __init__(self, page_json):
        if 'comments' in page_json:
            self.data = page_json['comments']['data']
            self.next_page = page_json['comments']['paging']['next']
        else:
            self.data = page_json['data']
            self.next_page = page_json['paging']['next'] if 'paging' in page_json else None

        self.raw_json = page_json


class DatabaseHandler:
    POSTS_COLLECTION_NAME = 'posts'

    def __init__(self, database_url, database_name):
        self._db_connection = pymongo.MongoClient(database_url)
        self._db_name = database_name

    def _db(self):
        return self._db_connection[self._db_name]

    def _posts_collection(self):
        return self._db()[self.POSTS_COLLECTION_NAME]

    def authenticate(self, username, password):
        self._db().authenticate(username, password, mechanism='SCRAM-SHA-1')

    def add_posts(self, post_list):
        self._posts_collection().insert_many(post_list)

    def close(self):
        self._db_connection.close()


# Public conversation puller
def pull_first_conversation_page(access_token, thread_id):
    api = facebook.GraphAPI(access_token=access_token, timeout=60)
    return api.get_object(thread_id)


def pull_all_conversation_pages(access_token, thread_id, database_handler):
    current_thread_page = ThreadPage(pull_first_conversation_page(access_token, thread_id))
    all_messages = current_thread_page.data

    while current_thread_page is not None:
        current_page_json = requests.get(current_thread_page.next_page).json()
        #if 'code' in current_page_json:
            # Encountered an api issue
        if 'data' in current_page_json:
            current_thread_page = ThreadPage(current_page_json)
            all_messages = current_thread_page.data + all_messages

    return all_messages


def main():

    config = ConfigParser.ConfigParser()
    config.read(VULTURE_CONFIG_FILE)

    access_token = config.get('graph.facebook.com', 'AccessToken')
    thread_id = config.get('graph.facebook.com', 'ThreadId')

    mongo_url = config.get('db', 'mongo_url')
    mongo_database = config.get('db', 'database')

    db_handler = DatabaseHandler(mongo_url, mongo_database)
    db_handler.authenticate(config.get('db', 'username'), config.get('db', 'password'))

    first_messages = ThreadPage(pull_first_conversation_page(access_token, thread_id))
    print('pulled messages!')

    #print first_messages

    db_handler.add_posts(first_messages.data)
    print('added messages')

    db_handler.close()

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