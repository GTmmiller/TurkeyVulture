import unittest
import TurkeyVulture


class TestPullThreadMessages(unittest.TestCase):

    def test_bad_input(self):
        TurkeyVulture.pull_thread_messages(None, None)
        self.assertRaises(RuntimeError, msg="")

