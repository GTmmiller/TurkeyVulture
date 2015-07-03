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

        with open('data/999_update.json', 'r') as update_page_file:
            self.update_page_json = json.load(update_page_file)

        with open('data/999_partial_update.json', 'r') as partial_update_page_file:
            self.partial_update_page_json = json.load(partial_update_page_file)

        self.enable_update = False
        self.enable_partial_update = False

    def get_object(self, id, **kwargs):
        if id == '999':
            if self.enable_update:
                return self.update_page_json
            elif self.enable_partial_update:
                return self.partial_update_page_json
            else:
                return self.thread_999_start_json
        elif id == '999/to/data':
            if self.enable_update:
                return self.update_page_json['to']['data']
            elif self.enable_partial_update:
                return self.partial_update_page_json['to']['data']
            else:
                return self.thread_999_start_json['to']['data']
        elif id == '999/comments' or re.search('/v\d+\.\d+/\d+/comments', id) is not None:
            if 'until' in kwargs:
                if kwargs['until'] == '37':
                    return self.thread_999_start_json
                elif kwargs['until'] == '12':
                    return self.thread_999_until_12_json
                elif kwargs['until'] == '1':
                    return self.last_page_json
            elif self.enable_update:
                return self.update_page_json['comments']
            elif self.enable_partial_update:
                return self.partial_update_page_json['comments']
            else:
                return self.thread_999_start_json['comments']
        else:
            return None


class FacebookThreadTestCase(unittest.TestCase):
    def setUp(self):
        self.test_thread = TurkeyVulture.FacebookThread(MockGraphAPI(), '999')


class UpdateThreadTestCase(FacebookThreadTestCase):
    def setUp(self):
        super(UpdateThreadTestCase, self).setUp()
        next_page_exists = self.test_thread.get_next_page()
        while next_page_exists is True:
            next_page_exists = self.test_thread.get_next_page()


class TestConstructThread(FacebookThreadTestCase):
    def test_assign_participants(self):
        self.assertEqual(8, len(self.test_thread.participants))

    def test_assign_thread_id(self):
        self.assertEqual('999', self.test_thread.thread_id)

    def test_assign_posts(self):
        self.assertListEqual(self.test_thread._data, self.test_thread.posts)
        self.assertEqual(25, len(self.test_thread.posts))

    def test_assign_latest_post_id(self):
        self.assertEqual('36', self.test_thread._latest_post_id)


class TestGetNextPage(FacebookThreadTestCase):
    def test_get_next_page(self):
        self.assertTrue(self.test_thread.get_next_page())
        self.assertEqual(36, len(self.test_thread.posts))
        self.assertTrue(self.test_thread.get_next_page())
        self.assertEqual(36, len(self.test_thread.posts))
        self.assertFalse(self.test_thread.get_next_page())


class TestUpdateThread(UpdateThreadTestCase):
    def test_no_update_thread(self):
        self.assertFalse(self.test_thread.update_thread())

    def test_update_thread(self):
        self.test_thread._graph.enable_update = True
        self.assertTrue(self.test_thread.update_thread())
        self.assertFalse(self.test_thread.update_thread())
        self.assertEqual(61, len(self.test_thread.posts))

    def test_partial_update_thread(self):
        self.test_thread._graph.enable_partial_update = True
        self.assertTrue(self.test_thread.update_thread())
        self.assertFalse(self.test_thread.update_thread())
        self.assertEqual(42, len(self.test_thread.posts))


class TestUpdateParticipants(UpdateThreadTestCase):
    def test_update_no_new_participants(self):
        self.test_thread.update_participants()
        self.assertEqual(8, len(self.test_thread.participants))

    def test_update_new_participants(self):
        self.test_thread._graph.enable_update = True
        self.test_thread.update_participants()
        self.assertEqual(9, len(self.test_thread.participants))

    def test_update_remove_participants(self):
        self.test_thread._graph.enable_partial_update = True
        self.test_thread.update_participants()
        self.assertEqual(7, len(self.test_thread.participants))


class TestGetPostId(FacebookThreadTestCase):
    def test_get_post_id(self):
        self.assertEqual('12', TurkeyVulture.FacebookThread._get_post_id(self.test_thread._data[0]))


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



