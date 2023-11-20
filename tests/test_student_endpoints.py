import os
import unittest
import requests
from tests.helpers import *
from tests.settings import BASE_URL, USER_DB_PATH, ENROLLMENT_DB_PATH
from db_connection import get_redisdb

class ClassTest(unittest.TestCase):
    def setUp(self):
        unittest_setUp()

    def tearDown(self):
        unittest_tearDown()

    def test_get_available_class(self):
        # Register & Login
        user_register(2, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student"])
        access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Prepare header & message body
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {access_token}"
        }
        body = {
            "enabled": True
        }

        # Send request
        url = f'{BASE_URL}/api/classes/available/'
        response = requests.get(url, headers=headers)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertIn("classes", response.json())

class EnrollmentTest(unittest.TestCase):
    def setUp(self):
        unittest_setUp()

    def tearDown(self):
        unittest_tearDown()

    def test_enroll_class(self):
        # ------------------ Registrar ------------------
        # Register & Login
        user_register(881234, "john@fullerton.edu", "1234", "john",
                      "smith", ["Registrar"])
        registrar_access_token = user_login("john@fullerton.edu", password="1234")

        # Create a class for testing
        class_id = 99999
        response = create_class(class_id, "SOC", "301", "2", 2024, "FA", 1, 10, registrar_access_token)

        # ------------------ Student ------------------
        # Register & Login
        user_register(9991234, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student"])
        student_access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Enroll 
        response = enroll_class(class_id, student_access_token)
        
        # Assert
        self.assertEqual(response.status_code, 201)

    def test_enroll_the_same_class(self):
        # ------------------ Registrar ------------------
        # Register & Login
        user_register(881234, "john@fullerton.edu", "1234", "john",
                      "smith", ["Registrar"])
        registrar_access_token = user_login("john@fullerton.edu", password="1234")

        # Create a class for testing
        class_id = 99999
        response = create_class(class_id, "SOC", "301", "2", 2024, "FA", 1, 10, registrar_access_token)

        # ------------------ Student ------------------
        # Register & Login
        user_register(9991234, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student"])
        student_access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Enroll 
        response = enroll_class(class_id, student_access_token)

        # Enroll one more time
        response = enroll_class(class_id, student_access_token)
        
        # Assert
        self.assertEqual(response.status_code, 409)

    def test_enroll_nonexisting_class(self):
        # Register & Login
        user_register(9991234, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student"])
        student_access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Enroll 
        response = enroll_class(111111, student_access_token)
        
        # Assert
        self.assertEqual(response.status_code, 404)

    def test_enroll_full_class_then_placed_on_waitlist(self):
        # ------------------ Registrar ------------------
        # Register & Login
        user_register(881234, "john@fullerton.edu", "1234", "john",
                      "smith", ["Registrar"])
        registrar_access_token = user_login("john@fullerton.edu", password="1234")

        # Create a class for testing
        class_id = 99999
        response = create_class(class_id, "SOC", "301", "2", 2024, "FA", 1, 1, registrar_access_token)

        # ------------------ Student 01: Enroll Success ------------------
        # Register & Login
        user_register(9991234, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student"])
        student_access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Enroll 
        response = enroll_class(class_id, student_access_token)
        
        # Assert
        self.assertEqual(response.status_code, 201)

        # ------------------ Student 02: Placed on Waitlist ------------------
        # Register & Login
        student_id = 88812801
        user_register(student_id, "abc2@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student"])
        student_access_token = user_login("abc2@csu.fullerton.edu", password="1234")

        # Enroll 
        response = enroll_class(class_id, student_access_token)

        # Check if data inserted into Redis
        rdb = get_redisdb()
        rank = rdb.zrank(class_id, student_id)

        # Assert
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(rank)


class DropClassTest(unittest.TestCase):
    def setUp(self):
        unittest_setUp()

    def tearDown(self):
        unittest_tearDown()

    def test_drop_class(self):
        # ------------------ Registrar ------------------
        # Register & Login
        user_register(881234, "john@fullerton.edu", "1234", "john",
                      "smith", ["Registrar"])
        registrar_access_token = user_login("john@fullerton.edu", password="1234")

        # Create a class for testing
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 10,
                                "2023-06-12", "2023-06-01 09:00:00", "2024-06-15 17:00:00", registrar_access_token)
        class_id = response.json()["inserted_id"]

        # ------------------ Student ------------------
        # Register & Login
        user_register(9991234, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student"])
        student_access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Enroll 
        response = enroll_class(class_id, student_access_token)
        
        # Assert
        self.assertEqual(response.status_code, 200)

        # ------------- DROP CLASS --------

        # Prepare header & message body
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {student_access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/enrollment/{class_id}/'
        response = requests.delete(url, headers=headers)

        # Assert
        self.assertEqual(response.status_code, 200)

    def test_drop_nonexisting_class(self):
        # Register & Login
        user_register(9991234, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student"])
        student_access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Prepare header & message body
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {student_access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/enrollment/999123/'
        response = requests.delete(url, headers=headers)

        # Assert
        self.assertEqual(response.status_code, 404)

class WaitlistTest(unittest.TestCase):
    def setUp(self):
        unittest_setUp()

    def tearDown(self):
        unittest_tearDown()

    def test_get_current_position_on_waitlist(self):
        # ------------------ Registrar ------------------
        # Register & Login
        user_register(881234, "john@fullerton.edu", "1234", "john",
                      "smith", ["Registrar"])
        registrar_access_token = user_login("john@fullerton.edu", password="1234")

        # Create a class for testing
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 1,
                                "2023-06-12", "2023-06-01 09:00:00", "2024-06-15 17:00:00", registrar_access_token)
        class_id = response.json()["inserted_id"]

        # ------------------ Student #1------------------
        # Register & Login
        user_register(9991234, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student"])
        student_access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Enroll 
        response = enroll_class(class_id, student_access_token)
        
        # ------------------ Student #2------------------
        # Register & Login
        user_register(9991235, "abc2@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student", "Instructor"])
        student_access_token = user_login("abc2@csu.fullerton.edu", password="1234")

        # Enroll 
        response = enroll_class(class_id, student_access_token)
        
        # Prepare header & message body
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {student_access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/waitlist/{class_id}/position/'
        response = requests.get(url, headers=headers)

        # Assert
        self.assertEqual(response.status_code, 200)

    def test_remove_from_waitlist(self):
        # ------------------ Registrar ------------------
        # Register & Login
        user_register(881234, "john@fullerton.edu", "1234", "john",
                      "smith", ["Registrar"])
        registrar_access_token = user_login("john@fullerton.edu", password="1234")

        # Create a class for testing
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 1,
                                "2023-06-12", "2023-06-01 09:00:00", "2024-06-15 17:00:00", registrar_access_token)
        class_id = response.json()["inserted_id"]

        # ------------------ Student #1------------------
        # Register & Login
        user_register(9991234, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student"])
        student_access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Enroll 
        response = enroll_class(class_id, student_access_token)
        
        # ------------------ Student #2------------------
        # Register & Login
        user_register(9991235, "abc2@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student", "Instructor"])
        student_access_token = user_login("abc2@csu.fullerton.edu", password="1234")

        # Enroll 
        response = enroll_class(class_id, student_access_token)
        
        # Prepare header & message body
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {student_access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/waitlist/{class_id}/'
        response = requests.delete(url, headers=headers)

        # Assert
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()