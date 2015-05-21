__title__ = 'TurkeyVulture'
__version__ = '0.0.1'
__author__ = 'Steven Miller'
__license__ = 'Apache 2.0'

__all__ = ['pull_thread_messages']

import facebook
import configparser

VULTURE_CONFIG_FILE = 'config/vulture.ini'


def pull_thread_messages(access_token, thread_id):
    api = facebook.GraphAPI(access_token=access_token, timeout=60)
    return api.get_object(thread_id)


def main():
    config = configparser.ConfigParser()
    config.read(VULTURE_CONFIG_FILE)


if __name__ == 'main':
    main()