import unittest
import requests
from tests.helpers import *
from tests.settings import BASE_URL
from tests.db_connection import get_redisdb


class SubscribeTest(unittest.TestCase):
    def setUp(self):
        unittest_setUp()

    def tearDown(self):
        unittest_tearDown()

    # TODO: Need to double check if data exists in RedisDB
    def test_subscribe_email_only(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # Create a class
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 1, users.registrar.access_token)
        class_id = response.json()["inserted_id"]

        # Student 1 enrolls
        response = enroll_class(class_id, users.student1.access_token)

        # Student 2 enrolls
        response = enroll_class(class_id, users.student2.access_token)

        # -------------------- Make API request --------------------
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.student2.access_token}"
        }
        body = {
            "email": "john@fullerton.edu"
        }

        # Send request
        url = f'{BASE_URL}/api/class/{class_id}/subscribe'
        response = requests.post(url, headers=headers, json=body)

        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 200)

    # TODO: Need to double check if data exists in RedisDB
    def test_subscribe_webhook_only(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # Create a class
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 1, users.registrar.access_token)
        class_id = response.json()["inserted_id"]

        # Student 1 enrolls
        response = enroll_class(class_id, users.student1.access_token)

        # Student 2 enrolls
        response = enroll_class(class_id, users.student2.access_token)

        # -------------------- Make API request --------------------
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.student2.access_token}"
        }
        body = {
            "webhook_url": "https://smee.io/CGPVZmrhO5f7v7w"
        }

        # Send request
        url = f'{BASE_URL}/api/class/{class_id}/subscribe'
        response = requests.post(url, headers=headers, json=body)

        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 200)

    # TODO: Need to double check if data exists in RedisDB
    def test_subscribe_email_and_webhook(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # Create a class
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 1, users.registrar.access_token)
        class_id = response.json()["inserted_id"]
        print(class_id)

        # Student 1 enrolls
        response = enroll_class(class_id, users.student1.access_token)

        # Student 2 enrolls
        response = enroll_class(class_id, users.student2.access_token)

        # -------------------- Make API request --------------------
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.student2.access_token}"
        }
        body = {
            "email": "john@fullerton.edu",
            "webhook_url": "https://smee.io/CGPVZmrhO5f7v7w"
        }

        # Send request
        url = f'{BASE_URL}/api/class/{class_id}/subscribe'
        response = requests.post(url, headers=headers, json=body)

        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 200)

    def test_subscribe_wrong_class(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # Wrong class id
        class_id = "This_Is_A_Wrong_Class_ID"

        # Student 1 enrolls
        # response = enroll_class(class_id, users.student1.access_token)

        # -------------------- Make API request --------------------
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.student2.access_token}"
        }
        body = {
            "email": "john@fullerton.edu",
            "webhook_url": "https://smee.io/CGPVZmrhO5f7v7w"
        }

        # Send request
        url = f'{BASE_URL}/api/class/{class_id}/subscribe'
        response = requests.post(url, headers=headers, json=body)

        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 404)

    def test_missing_email_and_webhook(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # Wrong class id
        class_id = "This_Is_A_Wrong_Class_ID"

        # Student 1 enrolls
        response = enroll_class(class_id, users.student1.access_token)

        # Student 2 enrolls
        response = enroll_class(class_id, users.student2.access_token)

        # -------------------- Make API request --------------------
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.student2.access_token}"
        }
        body = {
        }

        # Send request
        url = f'{BASE_URL}/api/class/{class_id}/subscribe'
        response = requests.post(url, headers=headers, json=body)

        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 400)

    def test_email_already_subscribed(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # Create a class
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 1, users.registrar.access_token)
        class_id = response.json()["inserted_id"]

        # Student 1 enrolls
        response = enroll_class(class_id, users.student1.access_token)

        # Student 2 enrolls
        response = enroll_class(class_id, users.student2.access_token)

        # -------------------- Make API request --------------------
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.student2.access_token}"
        }
        body = {
            "email": "john@fullerton.edu"
        }

        # Send request
        url = f'{BASE_URL}/api/class/{class_id}/subscribe'
        response1 = requests.post(url, headers=headers, json=body)

        # Send request
        url = f'{BASE_URL}/api/class/{class_id}/subscribe'
        response2 = requests.post(url, headers=headers, json=body)

        # ------------------------- Assert -------------------------
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 409)

    def test_webhook_already_subscribed(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # Create a class
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 1, users.registrar.access_token)
        class_id = response.json()["inserted_id"]

        # Student 1 enrolls
        response = enroll_class(class_id, users.student1.access_token)

        # Student 2 enrolls
        response = enroll_class(class_id, users.student2.access_token)

        # -------------------- Make API request --------------------
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.student2.access_token}"
        }
        body = {
            "webhook_url": "https://smee.io/CGPVZmrhO5f7v7w"
        }

        # Send request
        url = f'{BASE_URL}/api/class/{class_id}/subscribe'
        response1 = requests.post(url, headers=headers, json=body)

        # Send request
        url = f'{BASE_URL}/api/class/{class_id}/subscribe'
        response2 = requests.post(url, headers=headers, json=body)

        # ------------------------- Assert -------------------------
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 409)


class UnsubscribeTest(unittest.TestCase):
    def setUp(self):
        unittest_setUp()

    def tearDown(self):
        unittest_tearDown()

    def test_unsubscribe(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # Create a class
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 1, users.registrar.access_token)
        class_id = response.json()["inserted_id"]

        # Student 1 enrolls
        response = enroll_class(class_id, users.student1.access_token)

        # Student 2 enrolls
        response = enroll_class(class_id, users.student2.access_token)

        # -------------------- Make API request to Subscribe --------------------
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.student2.access_token}"
        }
        body = {
            "email": "john@fullerton.edu",
            "webhook_url": "https://smee.io/CGPVZmrhO5f7v7w"
        }

        # Send request
        url = f'{BASE_URL}/api/class/{class_id}/subscribe'
        response1 = requests.post(url, headers=headers, json=body)

        # -------------------- Make API request to Unsubscribe --------------------
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.student2.access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/class/{class_id}/unsubscribe'
        response2 = requests.delete(url, headers=headers, json=body)

        # ------------------------- Assert -------------------------
        self.assertEqual(response1.status_code, 200)
        print(response2)

    def test_unsubscribe_wrong_class(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # Wrong class id
        class_id = "This_Is_A_Wrong_Class_ID"

        # -------------------- Make API request --------------------
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.student2.access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/class/{class_id}/unsubscribe'
        response = requests.delete(url, headers=headers)

        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 404)


class GetSubscriptionTest(unittest.TestCase):
    def setUp(self):
        unittest_setUp()

    def tearDown(self):
        unittest_tearDown()

    # TODO: Need to double check if data exists in RedisDB
    def test_get_subscriptions(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # Create a class
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 1, users.registrar.access_token)
        class_id = response.json()["inserted_id"]

        # Student 1 enrolls
        response = enroll_class(class_id, users.student1.access_token)

        # Student 2 enrolls
        response = enroll_class(class_id, users.student2.access_token)

        # -------------------- Make API request to Subscribe --------------------
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.student2.access_token}"
        }
        body = {
            "email": "john@fullerton.edu",
            "webhook_url": "https://smee.io/CGPVZmrhO5f7v7w"
        }

        # Send request
        url = f'{BASE_URL}/api/class/{class_id}/subscribe'
        response = requests.post(url, headers=headers, json=body)

        # -------------------- Make API request to Get Subscriptions --------------------
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.student2.access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/subscriptions'
        response = requests.get(url, headers=headers)

        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 200)

        data = response.json()
        first_key = list(data.keys())[0]
        
        self.assertGreater(len(data), 0)
        self.assertEqual(len(data[first_key]), 1)


if __name__ == '__main__':
    unittest.main()