import unittest
import requests
from tests.helpers import *
from tests.settings import BASE_URL
from tests.db_connection import get_redisdb

class AutoEnrollmentTest(unittest.TestCase):
    def setUp(self):
        unittest_setUp()

    def tearDown(self):
        unittest_tearDown()

    def test_auto_enrollment(self):
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
            "Authorization": f"Bearer {users.student1.access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/enrollment/{class_id}/'
        response = requests.delete(url, headers=headers)

        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 200)

        # Check if the waitlist is updated
        rdb = get_redisdb()
        members = rdb.zrange(class_id, 0, -1)
        self.assertEqual(len(members), 0)

if __name__ == '__main__':
    unittest.main()