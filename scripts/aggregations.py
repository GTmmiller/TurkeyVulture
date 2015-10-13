import turkey_vulture
import ConfigParser

VULTURE_CONFIG_FILE = '../config/vulture.ini'


def main():

    config = ConfigParser.ConfigParser()
    config.read(VULTURE_CONFIG_FILE)

    thread_id = config.get('graph.facebook.com', 'ThreadId')

    mongo_url = config.get('db', 'mongo_url')
    mongo_database = config.get('db', 'database')
    mongo_username = config.get('db', 'username')
    mongo_password = config.get('db', 'password')

    database_handler = turkey_vulture.DatabaseHandler(mongo_url, mongo_database, thread_id=thread_id)
    database_handler.authenticate(mongo_username, mongo_password)

    database_handler.posts_links_aggregation()
    database_handler.posts_by_user_aggregation()
    database_handler.close()

if __name__ == "__main__":
    main()