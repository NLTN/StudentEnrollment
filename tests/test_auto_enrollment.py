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

        # Student 3 enrolls
        user_register(900003, "abc9898@csu.fullerton.edu", "1234", "Tom",
                        "Miller", ["Student"])
        access_token = user_login("abc9898@csu.fullerton.edu", password="1234")
        response = enroll_class(class_id, access_token)


        # BEFORE TEST: Get number of students on the waitlist before sending the request
        rdb = get_redisdb()
        count1 = rdb.zcard(class_id)
        # -------------------- Make API request --------------------
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.student1.access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/enrollment/{class_id}/'
        response = requests.delete(url, headers=headers)


        # AFTER TEST: Get number of students on the waitlist after sending the request
        count2 = rdb.zcard(class_id)

        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 200)
        self.assertEqual(count1, 2)
        self.assertEqual(count2, 1)

if __name__ == '__main__':
    unittest.main()