import unittest
import requests
from tests.helpers import *
from tests.settings import BASE_URL

class CurrentEnrollmentTest(unittest.TestCase):
    def setUp(self):
        unittest_setUp()

    def tearDown(self):
        unittest_tearDown()

    def test_get_current_enrollment_for_class(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # Create a class
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 1, users.registrar.access_token)
        class_id = response.json()["inserted_id"]

        # Student 1 enrolls
        response = enroll_class(class_id, users.student1.access_token)

        # -------------------- Make API request --------------------
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.instructor.access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/classes/{class_id}/students/'
        response = requests.get(url, headers=headers)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_get_students_who_dropped_class(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # Create a class
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 1, users.registrar.access_token)
        class_id = response.json()["inserted_id"]

        # Student 1 enrolls
        response = enroll_class(class_id, users.student1.access_token)

        # Student 1 drop class
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.student1.access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/enrollment/{class_id}/'
        response = requests.delete(url, headers=headers)

        # -------------------- Make API request --------------------
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.instructor.access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/classes/{class_id}/droplist/'
        response = requests.get(url, headers=headers)

        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 200)

    def test_get_students_on_waitlist(self):
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
            "Authorization": f"Bearer {users.instructor.access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/classes/{class_id}/waitlist/'
        response = requests.get(url, headers=headers)

        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_drop_student_administratively(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # Create a class
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 1, users.registrar.access_token)
        class_id = response.json()["inserted_id"]

        # Student 1 enrolls
        response = enroll_class(class_id, users.student1.access_token)

        # -------------------- Make API request --------------------
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.instructor.access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/enrollment/{class_id}/{users.student1.id}/administratively/'
        response1 = requests.delete(url, headers=headers)
        response2 = requests.delete(url, headers=headers)

        # Assert
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 404)


if __name__ == '__main__':
    unittest.main()