import os
import unittest
import requests
from tests.helpers import *
from tests.settings import BASE_URL, USER_DB_PATH, ENROLLMENT_DB_PATH
from tests.dynamodb import DynamoDB
from boto3.dynamodb.conditions import Key

class AutoEnrollmentTest(unittest.TestCase):
    def setUp(self):
        unittest_setUp()

    def tearDown(self):
        unittest_tearDown()

    def test_enable_auto_enrollment(self):
        # Register & Login
        user_register(101, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student", "Registrar"])
        access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Prepare header & message body
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {access_token}"
        }
        body = {
            "auto_enrollment_enabled": True
        }

        # Send request
        url = f'{BASE_URL}/api/auto-enrollment/'
        response = requests.put(url, headers=headers, json=body)

        # Assert
        self.assertEqual(response.status_code, 200)
        # self.assertIn("detail", response.json())

    def test_disable_auto_enrollment(self):
        # Register & Login
        user_register(101, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student", "Registrar"])
        access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Prepare header & message body
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {access_token}"
        }
        body = {
            "auto_enrollment_enabled": False
        }

        # Send request
        url = f'{BASE_URL}/api/auto-enrollment/'
        response = requests.put(url, headers=headers, json=body)

        # Assert
        self.assertEqual(response.status_code, 200)
        # self.assertIn("detail", response.json())


class CreateCourseTest(unittest.TestCase):
    def setUp(self):
        unittest_setUp()

    def tearDown(self):
        unittest_tearDown()

    def test_create_course(self):
        # Register & Login
        user_register(2, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student", "Registrar"])
        access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Prepare header & message body
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {access_token}"
        }
        body = {
            "department_code": "CPSC",
            "course_no": "888",
            "title": "TEST TEST"
        }

        # Send request
        url = f'{BASE_URL}/api/courses/'
        response = requests.post(url, headers=headers, json=body)

        # Assert
        self.assertEqual(response.status_code, 200)
        # self.assertIn("detail", response.json())

    def test_create_duplicate_course(self):
        # Register & Login
        user_register(2, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student", "Registrar"])
        access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Prepare header & message body
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {access_token}"
        }
        body = {
            "department_code": "CPSC",
            "course_no": "888",
            "title": "TEST TEST"
        }

        # Send request
        url = f'{BASE_URL}/api/courses/'
        response = requests.post(url, headers=headers, json=body)
        response = requests.post(url, headers=headers, json=body)

        # Assert
        self.assertEqual(response.status_code, 409)


class CreateClassTest(unittest.TestCase):
    def setUp(self):
        unittest_setUp()

    def tearDown(self):
        unittest_tearDown()

    def test_create_class(self):
        # Register & Login
        user_register(101, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student", "Registrar"])
        access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Send request
        response = create_class("SOC", "301", "2", 2024, "FA", 1, 10, access_token)

        # Assert
        self.assertEqual(response.status_code, 200)

    def test_create_duplicate_class(self):
        # Register & Login
        user_register(101, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student", "Registrar"])
        access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Send request
        response = create_class("SOC", "301", "2", 2024, "FA", 1, 10, access_token)

        response = create_class("SOC", "301", "2", 2024, "FA", 1, 10, access_token)

        # Assert
        self.assertEqual(response.status_code, 409)

    def test_update_class(self):
        # Register & Login
        user_register(101, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student", "Registrar"])
        access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Setup
        old_instructor_id = 1
        new_instructor_id = 2

        # Create a class
        response = create_class("SOC", "301", "1", 2024, "FA", old_instructor_id, 10, access_token)

        inserted_data = response.json()["data"]
        partition_key_value = inserted_data["term"]
        sort_key_value = inserted_data["class"]

        class_term_slug = f"{partition_key_value}_{sort_key_value}"

        # Prepare header & message body        
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {access_token}"
        }
        body = {
            "cwid": new_instructor_id
        }

        # Send request
        url = f'{BASE_URL}/api/classes/{class_term_slug}'
        response = requests.patch(url, headers=headers, json=body)


        # Direct Access DB to check if data has been updated successfully
        query_params = {
            "KeyConditionExpression": Key("term").eq(partition_key_value) 
                                    & Key("class").eq(sort_key_value)
        }
        db = DynamoDB()
        items = db.query("Class", query_params)

        # Assert
        self.assertGreater(len(items), 0)
        self.assertEqual(items[0]["instructor_id"], new_instructor_id)
        self.assertEqual(response.status_code, 200)

    def test_delete_class(self):
        # Register & Login
        user_register(2, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student", "Registrar"])
        access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Create a class
        response = create_class("SOC", "301", "1", 2024, "FA", 1, 10, access_token)

        inserted_data = response.json()["data"]
        partition_key_value = inserted_data["term"]
        sort_key_value = inserted_data["class"]

        class_term_slug = f"{partition_key_value}_{sort_key_value}"

        # Prepare header & message body        
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/classes/{class_term_slug}'
        response = requests.delete(url, headers=headers)
        
        # Direct Access DB to check if data has been updated successfully
        query_params = {
            "KeyConditionExpression": Key("term").eq(partition_key_value) 
                                    & Key("class").eq(sort_key_value)
        }
        db = DynamoDB()
        items = db.query("Class", query_params)

        # Assert
        self.assertEqual(len(items), 0)
        self.assertEqual(response.status_code, 200)

    def test_delete_nonexisting_class(self):
        # Register & Login
        user_register(2, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student", "Registrar"])
        access_token = user_login("abc@csu.fullerton.edu", password="1234")

        inserted_id = "9999_ABC-12"

        # Prepare header & message body        
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/classes/{inserted_id}'
        response = requests.delete(url, headers=headers)
        
        # Assert
        self.assertEqual(response.status_code, 404)
        
    def test_delete_class_invalid_id(self):
        # Register & Login
        user_register(2, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student", "Registrar"])
        access_token = user_login("abc@csu.fullerton.edu", password="1234")

        inserted_id = 999

        # Prepare header & message body        
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/classes/{inserted_id}'
        response = requests.delete(url, headers=headers)
        
        # Assert
        self.assertEqual(response.status_code, 400)
        
if __name__ == '__main__':
    unittest.main()