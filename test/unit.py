import unittest
import TurkeyVulture
import json
import facebook
import re


class MockGraphAPI(facebook.GraphAPI):
    def __init__(self):
        facebook.GraphAPI.__init__(self, "access_token", 60)
        with open('data/999.json', 'r') as thread_999_file:
            self.thread_999_start_json = json.load(thread_999_file)

        with open('data/999_until_12.json', 'r') as thread_999_until_12_file:
            self.thread_999_until_12_json = json.load(thread_999_until_12_file)

        with open('data/last_page.json', 'r') as last_page_file:
            self.last_page_json = json.load(last_page_file)

    def get_object(self, id, **kwargs):
        if id == '999':
            return self.thread_999_start_json
        elif id == '999/comments' or re.search('/v\d+\.\d+/\d+/comments', id) is not None:
            if 'until' in kwargs:
                if kwargs['until'] == '12':
                    return self.thread_999_until_12_json
                elif kwargs['until'] == '1':
                    return self.last_page_json
        else:
            return None


class FacebookThreadTestCase(unittest.TestCase):
    def setUp(self):
        self.test_thread = TurkeyVulture.FacebookThread(MockGraphAPI(), '999')


class TestConstructThread(FacebookThreadTestCase):
    def test_assign_participants(self):
        self.assertEqual(8, len(self.test_thread.participants))

    def test_assign_thread_id(self):
        self.assertEqual('999', self.test_thread.thread_id)

    def test_assign_posts(self):
        self.assertListEqual(self.test_thread._data, self.test_thread.posts)
        self.assertEqual(25, len(self.test_thread.posts))


class TestGetNextPage(FacebookThreadTestCase):
    def test_get_next_page_exists(self):
        self.assertTrue(self.test_thread.get_next_page())
        self.assertEqual(36, len(self.test_thread.posts))
        self.assertFalse(self.test_thread.get_next_page())


class TestNextPageUrl(FacebookThreadTestCase):
    def test_next_page_exists(self):
        expected_url = 'https://graph.facebook.com/v2.3/999/comments?access_token=placeholder&limit=25&until=12&__paging_token=enc_AxccviosOthErPLaCEHoLDer'
        self.assertEqual(expected_url, self.test_thread._next_page_url)

    def test_next_page_does_not_exist(self):
        self.test_thread.get_next_page()
        self.test_thread.get_next_page()
        self.assertEqual(None, self.test_thread._next_page_url)


class TestPopPosts(FacebookThreadTestCase):
    def test_pop_posts(self):
        old_posts = self.test_thread.posts
        self.assertListEqual(old_posts, self.test_thread.pop_posts())
        self.assertListEqual([], self.test_thread.posts)


class TestChangeAccessToken(FacebookThreadTestCase):
    def test_change_access_token(self):
        self.test_thread.change_access_token('Barry')
        self.assertEquals('Barry', self.test_thread._graph.access_token)


if __name__ == '__main__':
    unittest.main()



