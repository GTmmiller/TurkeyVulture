import turkey_vulture
import facebook
import ConfigParser
import time

VULTURE_CONFIG_FILE = '../config/vulture.ini'


def main():

    config = ConfigParser.ConfigParser()
    config.read(VULTURE_CONFIG_FILE)

    access_token = config.get('graph.facebook.com', 'AccessToken')
    thread_id = config.get('graph.facebook.com', 'ThreadId')

    mongo_url = config.get('db', 'mongo_url')
    mongo_database = config.get('db', 'database')
    mongo_username = config.get('db', 'username')
    mongo_password = config.get('db', 'password')

    database_handler = turkey_vulture.DatabaseHandler(mongo_url, mongo_database, thread_id=thread_id)
    database_handler.authenticate(mongo_username, mongo_password)

    graph = facebook.GraphAPI(access_token=access_token, timeout=60)
    thread = turkey_vulture.FacebookThread(graph, thread_id)
    next_page_exists = thread.get_next_page()
    database_handler.set_participants(thread.participants)

    while next_page_exists:
        try:
            next_page_exists = thread.get_next_page()
            if thread.posts:
                database_handler.add_posts(thread.pop_posts())
        except facebook.GraphAPIError as fb_error:
            if fb_error.result['error']['code'] == 613:
                time.sleep(100)
            elif fb_error.result['error']['code'] == 190:
                new_token = str(raw_input('Please input a new access_token'))
                thread.change_access_token(new_token)
            else:
                raise fb_error
        finally:
            database_handler.close()

if __name__ == "__main__":
    main()