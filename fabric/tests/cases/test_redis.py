import unittest
from wsgi import application


class TestRedisServer(unittest.TestCase):
    sample_name = "this is a test value that stored in redis"

    def test_set_value(self):
        """
        Function to test the saving of a key in the redis server
        """
        with application.app_context() as app_context:
            from fabric.modules.generic.redis_server import set_redis
            self.assertEqual(set_redis('sample_name', self.sample_name), True)

    def test_get_value(self):
        """
        Function to test the retrieval of a key from the redis server
        """
        with application.app_context() as app_context:
            from fabric.modules.generic.redis_server import get_redis
            self.assertEqual(get_redis('sample_name').decode('utf-8'), self.sample_name)
            self.assertEqual(get_redis('sample_name2'), None)
