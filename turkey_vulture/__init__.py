__title__ = 'turkey_vulture'
__version__ = '0.0.1'
__author__ = 'Steven Miller'
__license__ = 'Apache 2.0'

__all__ = ['pull_thread_messages']

import pymongo
import urlparse
from datetime import datetime
import re
import bson


class FacebookThread:
    """FacebookThread represents a Facebook Messenger Thread conversation

    This class acts as a container and retriever for a Facebook conversation thread. It has the functionality to pull
    all of the messages from a thread given a valid thread id. It can also pull all messages created after a certain
    given message id. This class depends on the facebook-sdk python library and the 'read-mailbox' GraphApi permission.

    Attributes:
        participants (List[Dict{string}]): A json representation of the participants in the thread.
        thread_id (str): The thread id the object targets.

    """

    def __init__(self, graph, thread_id, latest_post_id=None):
        """The Initializer for the FacebookThread object

        Args:
            :param graph: The connection to the Facebook Graph Api
            :param thread_id: The id of the thread to pull messages from
            :param latest_post_id: An optional parameter to specify the last post to start from
            :type graph: facebook.GraphApi
            :type thread_id: str
            :type latest_post_id: str
        """
        self._graph = graph
        if not latest_post_id:
            raw_json = self._graph.get_object(thread_id)
            self.participants = raw_json['to']['data']
            self._comments_json = raw_json['comments']
            self._posts = self._data
            self._latest_post_id = self._get_post_id(self._data[-1])
        else:
            self.participants = []
            self._comments_json = []
            self._posts = []
            self._latest_post_id = latest_post_id
        self._updating = False
        self.thread_id = thread_id
        self._old_latest_post_id = None

    def get_next_page(self):
        """Adds the next 25 posts from the conversation to the FacebookThread object

        :return: If there are more posts to retrieve from the conversation
        :rtype: bool
        """
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
        """Checks for new posts in reference to the latest post retrieved and adds the next 25 posts if they exist

        :return: If there are additional posts to retrieve
        :rtype: bool
        """
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
        # If there aren't then don't bother
        if long(self._old_latest_post_id) == long(self._latest_post_id):
            self._old_latest_post_id = None
            self._updating = False
            return False

        # check if it's a partial new page
        if long(self._old_latest_post_id) >= long(self._get_post_id(self._data[0])):
            # pull all posts that happened after the old latest post
            new_post_data = [post for post in self._data if self._get_post_id(post) > self._old_latest_post_id]
            self._posts = self._posts + new_post_data
            self._updating = False
        else:
            self._posts = self._posts + self._data
            self._updating = True
        return True

    def update_participants(self):
        self.participants = self._graph.get_object(self.thread_id + '/to/data')

    @staticmethod
    def _get_post_id(post):
        """An internal method for retrieving the id of a given post

        :param post: A post to retrieve an id from
        :type post: Dict[str]
        :return: The given post's id
        :rtype: str
        """
        return post['id'].split('_')[1]

    @property
    def _data(self):
        """List[Dict[str]]: The data from the current thread json."""
        return self._comments_json['data'] if 'data' in self._comments_json else None

    @property
    def _next_page_url(self):
        """str: The url for the next page of 25 posts from the current thread json."""
        return self._comments_json['paging']['next'] if 'paging' in self._comments_json else None

    @property
    def posts(self):
        """List[Dict[str]]: The current list of posts retrieved from the thread."""
        return self._posts

    def pop_posts(self):
        """Returns and clears the posts from the object

        Facebook conversation threads can be very long, so sometimes it's necessary to offload posts in order to
        free up memory. This can be used to batch process posts from a thread.

        :return: The current posts array
        :rtype: List[Dict[str]]
        """
        return_posts = self._posts
        self._posts = []
        return return_posts

    def change_access_token(self, access_token):
        """Changes the access token being used by the GraphApi object

        Some Facebook conversations can take a long time to completely pull, so you may need to use this method to
        change your API key if it happens to expire while posts are being pulled

        :param access_token: The new access token for the GraphApi object to use
        :type access_token: str
        """
        self._graph.access_token = access_token


class DatabaseHandler:
    POSTS_COLLECTION_BASE = 'posts'
    PARTICIPANTS_COLLECTION_BASE = 'participants'
    # Special thanks to @gruber
    URL_REGEX = re.compile("(^|\s)((https?://)?[\w-]+(\.[\w-]+)+\.?(:\d+)?(/\S*)?)", re.IGNORECASE)

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
        transformed_post_list = [DatabaseHandler.post_transform(post) for post in post_list]
        self._posts_collection().insert_many(transformed_post_list)

    @staticmethod
    def post_transform(post):
        post["_id"] = post.pop("id")
        post["created_time"] = datetime.strptime(post["created_time"].split("+")[0], "%Y-%m-%dT%H:%M:%S")
        return post

    def set_participants(self, participants_list):
        self._participants_collection().remove({})
        self._participants_collection().insert_many(participants_list)

    @property
    def most_recent_post_id(self):
        # TODO: Save the _id as just the post id
        return self._db_connection[self._db_name][self._posts_collection_name].find_one(sort=[('_id', pymongo.DESCENDING)])["_id"].split('_')[1]

    def posts_by_user_aggregation(self):
        separator_regex = re.compile('[\s\.,\?!;:]+')
        by_user_database_name = self._posts_collection_name + "_words_by_user"
        mapper = bson.Code("""
                           function() { emit( this.from.name, this.message ); }
                           """)
        reducer = bson.Code("""
                            function(key, values) { return values.join(' ') + ' '; }
                            """)

        self._posts_collection().map_reduce(mapper, reducer, by_user_database_name)
        for doc in self._db()[by_user_database_name].find():
            word_array = re.sub(separator_regex, ' ', doc["value"]).lower().split(" ")
            # drop value field and add messages field
            self._db()[by_user_database_name].update_one({"_id": doc['_id']},
                                                         {"$unset": {"value": ""},
                                                          "$set": {"words": word_array}})
        self._db()[by_user_database_name].aggregate(
            [
                {"$unwind": "$words"},
                {"$group": {"_id": {"name": "$_id", "word": "$words"},
                            "count": {"$sum": 1}}},
                {"$out": by_user_database_name}
            ]
        )

        self._db()[by_user_database_name].aggregate(
            [
                {"$group": {"_id": {"word": "$_id.word"}, "count": {"$sum": "$count"}}},
                {"$out": self._posts_collection_name + "_word_counts"}
            ]
        )

    def posts_links_aggregation(self):
        links_database_name = self._posts_collection_name + "_links"
        self._posts_collection().aggregate(
            [
                {"$project": {"created_time": 1, "name": "$from.name", "message": 1, "processed": {"$literal": False}}},
                {"$match": {"message": {"$regex": DatabaseHandler.URL_REGEX}}},
                {"$out": links_database_name}
            ]
        )

        # Pull all matching documents into memory and extract links. Update documents with a links field
        # TODO: Make this a batch operation
        # TODO: Consider doing this in javascript
        update_operations = []
        for doc in self._db()[links_database_name].find():
            links = []
            for match in re.finditer(DatabaseHandler.URL_REGEX, doc["message"]):
                links.append(match.group().strip())
            update_operations.append(pymongo.UpdateOne({"_id": doc["_id"]}, {"$set": {"links": links}}))
        self._db()[links_database_name].bulk_write(update_operations)

    def close(self):
        self._db_connection.close()
