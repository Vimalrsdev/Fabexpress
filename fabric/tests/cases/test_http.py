import unittest
from wsgi import application
from flask import json


class TestHTTPRequests(unittest.TestCase):
    def test_index_route(self):
        """
        Function to test the http response of the index route
        """
        print(".\nTesting the index API route")
        tester = application.test_client(self)
        http_index_route_response = tester.get('/', content_type="html/text")
        self.assertEqual(http_index_route_response.status_code, 200)

    def test_invalid_route(self):
        """
        Function to test the http response of an invalid route
        """
        print("\nTesting the invalid API route")
        tester = application.test_client(self)
        invalid_http_response = tester.get('/thisisaninvalidroute', content_type="application/json")
        self.assertEqual(invalid_http_response.status_code, 404)
        self.assertTrue(b'failed' in invalid_http_response.data)
        # Json testing
        json_response_data = json.loads(invalid_http_response.data)
        self.assertEqual(json_response_data.get('status'), 'failed')
