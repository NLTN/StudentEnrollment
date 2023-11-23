import unittest
import requests
from tests.helpers import *
from tests.settings import BASE_URL
from tests.db_connection import get_redisdb

class ClassTest(unittest.TestCase):
    def setUp(self):
        unittest_setUp()

    def tearDown(self):
        unittest_tearDown()

    def test_get_available_class(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # Create a class
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 10, users.registrar.access_token)
        class_id = response.json()["inserted_id"]

        # Student 1 enrolls
        response = enroll_class(class_id, users.student1.access_token)

        # -------------------- Make API request --------------------
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.student1.access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/classes/available/'
        response = requests.get(url, headers=headers)

        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

class EnrollmentTest(unittest.TestCase):
    def setUp(self):
        unittest_setUp()

    def tearDown(self):
        unittest_tearDown()

    def test_enroll_class(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # Create a class
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 10, users.registrar.access_token)
        class_id = response.json()["inserted_id"]

        # Student 1 enrolls
        response = enroll_class(class_id, users.student1.access_token)
        
        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 201)

    def test_enroll_the_same_class(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # Create a class
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 10, users.registrar.access_token)
        class_id = response.json()["inserted_id"]

        # Student 1 enrolls
        response = enroll_class(class_id, users.student1.access_token)

        # Student 1 enrolls in the same class
        response = enroll_class(class_id, users.student1.access_token)
        
        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 409)

    def test_enroll_nonexisting_class(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # Enroll 
        response = enroll_class("111111", users.student1.access_token)
        
        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 404)

    def test_place_on_waitlist(self):
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

        # ------------------------- Assert -------------------------
        # Check if data inserted into Redis
        rdb = get_redisdb()
        rank = rdb.zrange(class_id, 0, -1)

        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(rank)

    def test_already_on_waitlist(self):
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

        # Now, the student 2 is on the waitlist
        # Student 2 try to enroll one more time
        response = enroll_class(class_id, users.student2.access_token)

        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 409)
class DropClassTest(unittest.TestCase):
    def setUp(self):
        unittest_setUp()

    def tearDown(self):
        unittest_tearDown()

    def test_drop_class(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # Create a class
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 10, users.registrar.access_token)
        class_id = response.json()["inserted_id"]

        # Student 1 enrolls
        response = enroll_class(class_id, users.student1.access_token)

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

    def test_drop_nonexisting_class(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # -------------------- Make API request --------------------
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.student1.access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/enrollment/999123/'
        response = requests.delete(url, headers=headers)

        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 404)

class WaitlistTest(unittest.TestCase):
    def setUp(self):
        unittest_setUp()

    def tearDown(self):
        unittest_tearDown()

    def test_get_current_position_on_waitlist(self):
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

        # Send request
        url = f'{BASE_URL}/api/waitlist/{class_id}/position/'
        response = requests.get(url, headers=headers)

        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["position"], 1)

    def test_remove_from_waitlist(self):
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

        # Send request
        url = f'{BASE_URL}/api/waitlist/{class_id}/'
        response = requests.delete(url, headers=headers)

        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()