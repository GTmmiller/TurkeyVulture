import unittest
import turkey_vulture
import data
import facebook
import re


# TODO: Add test for big update
class MockGraphAPI(facebook.GraphAPI):
    def __init__(self):
        facebook.GraphAPI.__init__(self, "access_token", 60)
        self._thread_order = {}
        self.use_default_order()
        self._api_version_regex = re.compile('/v\d\.\d/')

    def use_default_order(self):
        self._thread_order = {
            '999': {
                None: data.START_999_JSON,
                '12': data.UNTIL_12_999_JSON,
                '1': data.LAST_PAGE_JSON
            }
        }

    def use_full_update_order(self):
        self._thread_order = {
            '999': {
                None: data.UPDATE_999_JSON,
                '37': data.START_999_JSON,
                '12': data.UNTIL_12_999_JSON,
                '1': data.LAST_PAGE_JSON
            }
        }

    def use_partial_update_order(self):
        self._thread_order = {
            '999': {
                None: data.PARTIAL_UPDATE_999_JSON
            }
        }

    def get_object(self, id, **kwargs):
        id_array = re.sub(self._api_version_regex, '', id).split('/')

        thread_id = id_array[0]
        data_path = id_array[1:]
        if 'until' in kwargs:
            until = kwargs['until']
        else:
            until = None

        thread_page = self._thread_order[thread_id][until]
        for path in data_path:
            thread_page = thread_page.get(path)
        return thread_page


class FacebookThreadTestCase(unittest.TestCase):
    def setUp(self):
        self.test_thread = turkey_vulture.FacebookThread(MockGraphAPI(), '999')


class UpdateThreadConstructorTestCase(unittest.TestCase):
    def setUp(self):
        self.test_thread = turkey_vulture.FacebookThread(MockGraphAPI(), '999', '36')


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
        self.test_thread._graph.use_full_update_order()
        self.assertTrue(self.test_thread.update_thread())
        self.assertTrue(self.test_thread.update_thread())
        self.assertFalse(self.test_thread.update_thread())
        self.assertEqual(61, len(self.test_thread.posts))

    def test_partial_update_thread(self):
        self.test_thread._graph.use_partial_update_order()
        self.assertTrue(self.test_thread.update_thread())
        self.assertFalse(self.test_thread.update_thread())
        self.assertEqual(42, len(self.test_thread.posts))


class TestUpdateParticipants(UpdateThreadTestCase):
    def test_update_no_new_participants(self):
        self.test_thread.update_participants()
        self.assertEqual(8, len(self.test_thread.participants))

    def test_update_new_participants(self):
        self.test_thread._graph.use_full_update_order()
        self.test_thread.update_participants()
        self.assertEqual(9, len(self.test_thread.participants))

    def test_update_remove_participants(self):
        self.test_thread._graph.use_partial_update_order()
        self.test_thread.update_participants()
        self.assertEqual(7, len(self.test_thread.participants))


class TestGetPostId(FacebookThreadTestCase):
    def test_get_post_id(self):
        self.assertEqual('12', turkey_vulture.FacebookThread._get_post_id(self.test_thread._data[0]))


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


class TestUpdateThreadIdConstructor(UpdateThreadConstructorTestCase):
    def test_full_update(self):
        self.test_thread._graph.use_full_update_order()
        self.assertTrue(self.test_thread.update_thread())
        self.assertTrue(self.test_thread.update_thread())
        self.assertFalse(self.test_thread.update_thread())
        self.assertEqual(25, len(self.test_thread.posts))

    def test_partial_update(self):
        self.test_thread._graph.use_partial_update_order()
        self.assertTrue(self.test_thread.update_thread())
        self.assertFalse(self.test_thread.update_thread())
        self.assertEqual(6, len(self.test_thread.posts))