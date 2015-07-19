__title__ = 'turkey_vulture'
__version__ = '0.0.1'
__author__ = 'Steven Miller'
__license__ = 'Apache 2.0'

__all__ = ['pull_thread_messages']

import pymongo
import urlparse


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
        self._latest_post_id = self._get_post_id(self._data[-1])
        self._updating = False
        self.thread_id = thread_id
        self._old_latest_post_id = None

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

    def update_thread(self):
        if self._updating is False:
            self._old_latest_post_id = self._latest_post_id
            self._comments_json = self._graph.get_object(self.thread_id + '/comments')
            self._latest_post_id = self._get_post_id(self._data[-1])
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

        # check if there's new comments
        if self._old_latest_post_id == self._latest_post_id:
            self._old_latest_post_id = None
            self._updating = False
            return False

        # check if it's a partial new page
        if self._old_latest_post_id >= self._get_post_id(self._data[0]):
            # pull all posts that happened after the old latest post
            new_post_data = [post for post in self._data if self._get_post_id(post) > self._old_latest_post_id]
            self._posts = self._posts + new_post_data
            self._updating = False
        else:
            self._posts = self._posts + self._data
        return True

    def update_participants(self):
        self.participants = self._graph.get_object(self.thread_id + '/to/data')

    @staticmethod
    def _get_post_id(post):
        return post['id'].split('_')[1]

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
