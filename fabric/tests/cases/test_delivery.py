import unittest
from fabric.core.models import PickupRequest, Order
from fabric.modules.generic.classes import SerializeSQLAResult
from wsgi import application
from flask import json, current_app
from fabric import db


class TestDeliveryApp(unittest.TestCase):
    """
    Unit test cases for the delivery route.
    """

    # Variable to store the access key gained from the login request.
    access_key = None
    # Variable to store the delivery user id gained from the login request.
    user_id = None
    # Variable to store the delivery user's branch code gained from the login request.
    branch_code = None
    # Variable to store the delivery user api-key
    api_key = None
    # Variable to store a pickup request id (Any).
    pickup_request_id = None
    # Variable to store a order id (Any).
    order_id = None

    @classmethod
    def setUpClass(cls):
        """
        This setUpClass calls login API to get the credentials for the testing.
        By calling the login API, access_key will be gained.
        Also getting a pickup request id belongs to that delivery user.
        @return:
        """
        print("\nsetUpClass call for delivery route (Class variables will be set by calling the login API)")
        with application.app_context() as app_context:
            # Getting the api_key from the config file within the application context.
            cls.api_key = current_app.config["API_KEY"]

        tester = application.test_client(cls)
        login_response = tester.post('/delivery/login', content_type='application/json',
                                     data=json.dumps(dict(mobile_number="9876543210", password="123")),
                                     headers={"api-key": cls.api_key})

        response = json.loads(login_response.data)
        if response.get('status') == 'success':
            # After successfully logging in, save the access key, user_id and branch_code to
            # the corresponding class variables.
            cls.access_key = response['result']['access_key']
            cls.user_id = response['result']['user_id']
            cls.branch_code = response['result']['branch_code']

        with application.app_context() as app_context:
            # Getting a pickup request id from the pickup requests table belongs to that delivery user.
            try:
                pickup_request = db.session.query(PickupRequest.PickupRequestId).filter(
                    PickupRequest.BranchCode == cls.branch_code, PickupRequest.DUserId == cls.user_id,
                    PickupRequest.IsCancelled == 0).first()
                pickup_request = SerializeSQLAResult(pickup_request).serialize_one()
                cls.pickup_request_id = pickup_request['PickupRequestId']
            except Exception as e:
                print(e)

            # Getting any order id from the orders table belongs to that delivery user.
            try:
                order = db.session.query(Order.OrderId).filter(Order.DUserId == cls.user_id, Order.IsDeleted == 0,
                                                               Order.BranchCode == cls.branch_code).first()
                order_id = SerializeSQLAResult(order).serialize_one()
                cls.order_id = order_id['OrderId']
            except Exception as e:
                print(e)

    @classmethod
    def tearDownClass(cls):
        """
        This tearDownClass calls the logout API after all the testing are done.
        Thus making the access key invalid.
        @return:
        """
        print("\ntearDownClass call for delivery route (Logout will be initiated)")
        tester = application.test_client(cls)
        tester.post('/delivery/logout', content_type='application/json',
                    headers={"api-key": cls.api_key,
                             "access-key": cls.access_key,
                             "user-id": cls.user_id})

    def test_home(self):
        """
        Function to test the home API route.
        @return:
        """
        print("\nTesting home API route")
        tester = application.test_client(self)
        home_response = tester.post('/delivery/home', content_type='application/json',
                                    data=json.dumps(dict(branch_code=self.branch_code)),
                                    headers={"api-key": self.api_key,
                                             "access-key": self.access_key,
                                             "user-id": self.user_id})
        response = json.loads(home_response.data)
        # The status_code can be either DATA_FOUND or DATA_NOT_FOUND
        self.assertIn(response['status_code'], ['DATA_FOUND', 'DATA_NOT_FOUND'])

    def test_home_invalid_api_key(self):
        """
        Function to test the home API route with invalid API key.
        @return:
        """
        print("\nTesting home API route (Testing INVALID_API_KEY scenario)")
        tester = application.test_client(self)
        # Invalid API Key case.
        invalid_api_key = tester.post('/delivery/home', content_type='application/json',
                                      data=json.dumps(dict(branch_code=self.branch_code)),
                                      headers={"api-key": f"{self.api_key}ine34",
                                               "access-key": self.access_key,
                                               "user-id": self.user_id})
        response = json.loads(invalid_api_key.data)
        # The status_code will be INVALID_API_KEY.
        self.assertEqual(response['status_code'], "INVALID_API_KEY")

    def test_home_invalid_access_key(self):
        """
        Function to test the home API route with invalid access key.
        @return:
        """

        print("\nTesting home API route (Testing INVALID_ACCESS_KEY scenario)")
        tester = application.test_client(self)
        invalid_access_key = tester.post('/delivery/home', content_type='application/json',
                                         data=json.dumps(dict(branch_code=self.branch_code)),
                                         headers={"api-key": self.api_key,
                                                  "access-key": f"{self.access_key}sdsdw",
                                                  "user-id": self.user_id})

        response = json.loads(invalid_access_key.data)
        # The status_code will be INVALID_ACCESS_KEY.
        self.assertEqual(response['status_code'], "INVALID_ACCESS_KEY")

    def test_activity_list(self):
        """
        Function to test the get_activity_list API route.
        @return:
        """
        print("\nTesting get_activity_list API route")
        tester = application.test_client(self)
        activity_list_response = tester.post('/delivery/get_activity_list', content_type='application/json',
                                             data=json.dumps(dict(branch_code=self.branch_code,
                                                                  sorting_method="TIME_SLOT")),
                                             headers={"api-key": self.api_key,
                                                      "access-key": self.access_key,
                                                      "user-id": self.user_id})
        response = json.loads(activity_list_response.data)
        # The status_code can be either DATA_FOUND or DATA_NOT_FOUND
        self.assertIn(response['status_code'], ['DATA_FOUND', 'DATA_NOT_FOUND'])

    def test_pending_pickup_details(self):
        """
        Function to test the get_pending_pickup_details API route.
        @return:
        """
        print("\nTesting the get_pending_pickup_details API route")
        tester = application.test_client(self)
        pending_pickup_response = tester.post('/delivery/get_pending_pickup_details', content_type='application/json',
                                              data=json.dumps(dict(pickup_request_id=self.pickup_request_id)),
                                              headers={"api-key": self.api_key,
                                                       "access-key": self.access_key,
                                                       "user-id": self.user_id})
        response = json.loads(pending_pickup_response.data)
        # The status_code can be either DATA_FOUND or DATA_NOT_FOUND
        self.assertIn(response['status_code'], ['DATA_FOUND', 'DATA_NOT_FOUND'])

    def test_get_order_garments(self):
        """
        Function to test the get_order_garments API route.
        @return:
        """
        print("\nTesting the get_order_garments API route")
        tester = application.test_client(self)
        get_order_garments_response = tester.post('/delivery/get_order_garments', content_type='application/json',
                                                  data=json.dumps(dict(order_id=self.order_id, service_tat_id=1)),
                                                  headers={"api-key": self.api_key,
                                                           "access-key": self.access_key,
                                                           "user-id": self.user_id})
        response = json.loads(get_order_garments_response.data)
        # The status_code can be either DATA_FOUND or DATA_NOT_FOUND
        self.assertIn(response['status_code'], ['DATA_FOUND', 'DATA_NOT_FOUND'])

    def test_add_order_garments(self):
        """
        Function to test the add_order_garments API route.
        @return:
        """
        print("\nTesting the add_order_garments API route")
        print("\nEnter a garment id: ")
        garment_id = int(input())
        print("\nEnter count of garments: ")
        garments_count = int(input())
        print("\nEnter service tat id: ")
        service_tat_id = int(input())
        print("\nEnter service type id: ")
        service_type_id = int(input())
        garments = [{"garment_id": garment_id, "garment_count": garments_count}]

        tester = application.test_client(self)
        add_order_garments_response = tester.post('/delivery/add_order_garments', content_type='application/json',
                                                  data=json.dumps(dict(pickup_request_id=self.pickup_request_id,
                                                                       service_tat_id=service_tat_id,
                                                                       service_type_id=service_type_id,
                                                                       garments=garments)),
                                                  headers={"api-key": self.api_key,
                                                           "access-key": self.access_key,
                                                           "user-id": self.user_id})
        response = json.loads(add_order_garments_response.data)
        print(f"Status code is {response['status_code']}")
        # The status_code can be either DATA_SAVED or DATA_SAVE_FAILED
        # If the service tat id, service type id, garment id and garment count are same as previous,
        # data won't be saved.
        # Data will be saved only if the garment counts is higher than the previous record.
        self.assertIn(response['status_code'], ['DATA_SAVED', 'DATA_SAVE_FAILED'])

    def test_remove_order_garments(self):
        """
        Function to test the remove_order_garments API route.
        @return:
        """
        print("\nTesting the remove_order_garments API route")
        print("\nEnter an order garment id: ")
        order_garment_id = int(input())
        tester = application.test_client(self)
        remove_order_garments_response = tester.post('/delivery/remove_order_garment', content_type='application/json',
                                                     data=json.dumps(dict(order_garment_id=order_garment_id
                                                                          )),
                                                     headers={"api-key": self.api_key,
                                                              "access-key": self.access_key,
                                                              "user-id": self.user_id})
        response = json.loads(remove_order_garments_response.data)
        print(f"Status code is {response['status_code']}")
        # The status_code can be either DATA_DELETED or DATA_DELETE_FAILED
        self.assertIn(response['status_code'], ['DATA_DELETED', 'DATA_DELETE_FAILED'])
