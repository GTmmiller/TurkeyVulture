__title__ = 'TurkeyVulture'
__version__ = '0.0.1'
__author__ = 'Steven Miller'
__license__ = 'Apache 2.0'

__all__ = ['pull_thread_messages']

import facebook
import ConfigParser
import json
import requests
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


# Public conversation puller
def pull_first_conversation_page(access_token, thread_id):
    api = facebook.GraphAPI(access_token=access_token, timeout=60)
    return api.get_object(thread_id)


def pull_all_conversation_pages(access_token, thread_id):
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

    first_messages = pull_first_conversation_page(access_token, thread_id)
    print(json.dumps(first_messages['comments']['data'], sort_keys=True, indent=4, separators=(',', ': ')))
    print(first_messages['comments']['paging']['next'])

    second_messages = requests.get(first_messages['comments']['paging']['next']).json()
    print(json.dumps(second_messages['data'], sort_keys=True, indent=4, separators=(',', ': ')))
    print(second_messages['paging']['next'])

    total_messages = second_messages['data'] + first_messages['comments']['data']

    all_messages = pull_all_conversation_pages(access_token, thread_id)
    print(json.dumps(all_messages, sort_keys=True, indent=4, separators=(',', ': ')))


if __name__ == "__main__":
    main()