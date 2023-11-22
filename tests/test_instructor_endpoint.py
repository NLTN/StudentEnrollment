import os
import unittest
import requests
from tests.helpers import *
from tests.settings import BASE_URL, USER_DB_PATH, ENROLLMENT_DB_PATH

class CurrentEnrollmentTest(unittest.TestCase):
    def setUp(self):
        unittest_setUp()

    def tearDown(self):
        unittest_tearDown()

    def test_get_current_enrollment_for_class(self):
        # ------------------ Registrar ------------------
        # Register & Login
        user_register(881234, "john@fullerton.edu", "1234", "john",
                      "smith", ["Registrar", "Instructor"])
        registrar_access_token = user_login("john@fullerton.edu", password="1234")

        # Create a class for testing
        response = create_class("SOC", "301", "2", 2024, "FA", 1, 10, registrar_access_token)

        class_id = response.json()["inserted_id"]

        # ------------------ Student ------------------
        # Register & Login
        user_register(9991234, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student"])
        student_access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Enroll 
        response = enroll_class(class_id, student_access_token)

        # Prepare header & message body
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {registrar_access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/classes/{class_id}/students/'
        response = requests.get(url, headers=headers)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_get_students_who_dropped_class(self):
        # ------------------ Registrar ------------------
        # Register & Login
        user_register(881234, "john@fullerton.edu", "1234", "john",
                      "smith", ["Registrar", "Instructor"])
        registrar_access_token = user_login("john@fullerton.edu", password="1234")

        # Create a class for testing
        response = create_class("SOC", "301", "2", 2024, "FA", 1, 10, registrar_access_token)
        
        class_id = response.json()["inserted_id"]

        # ------------------ Student ------------------
        # Register & Login
        user_register(9991234, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student"])
        student_access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Enroll 
        response = enroll_class(class_id, student_access_token)
        
        # Assert
        self.assertEqual(response.status_code, 201)

        # ------------- DROP CLASS --------

        # Prepare header & message body
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {student_access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/enrollment/{class_id}/'
        response = requests.delete(url, headers=headers)

        # ------------- CHECK --------
        # Prepare header & message body
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {registrar_access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/classes/{class_id}/droplist/'
        response = requests.get(url, headers=headers)

        # Assert
        self.assertEqual(response.status_code, 200)

    def test_get_students_on_waitlist(self):
        # ------------------ Registrar ------------------
        # Register & Login
        user_register(881234, "john@fullerton.edu", "1234", "john",
                      "smith", ["Registrar", "Instructor"])
        registrar_access_token = user_login("john@fullerton.edu", password="1234")

        # Create a class for testing
        response = create_class("SOC", "301", "2", 2024, "FA", 1, 1, registrar_access_token)

        class_id = response.json()["inserted_id"]

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

        # Prepare header & message body
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {registrar_access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/classes/{class_id}/waitlist/'
        response = requests.get(url, headers=headers)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_drop_student_administratively(self):
        # ------------------ Registrar ------------------
        # Register & Login
        user_register(881234, "john@fullerton.edu", "1234", "john",
                      "smith", ["Registrar", "Instructor"])
        registrar_access_token = user_login("john@fullerton.edu", password="1234")

        # Create a class for testing
        response = create_class("SOC", "301", "2", 2024, "FA", 1, 10, registrar_access_token)
        
        class_id = response.json()["inserted_id"]

        # ------------------ Student ------------------
        # Register & Login
        student_id = 9991234
        user_register(student_id, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student"])
        student_access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Enroll 
        response = enroll_class(class_id, student_access_token)
        
        # Assert
        self.assertEqual(response.status_code, 201)

        # ------------- DROP CLASS --------
        # Prepare header & message body
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {registrar_access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/enrollment/{class_id}/{student_id}/administratively/'
        response1 = requests.delete(url, headers=headers)
        response2 = requests.delete(url, headers=headers)

        # Assert
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 404)


if __name__ == '__main__':
    unittest.main()