import unittest
import requests
from tests.helpers import *
from tests.settings import BASE_URL
from db_connection import get_dynamodb, TableNames
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
        user_register(101, "abc@csu.fullerton.edu", "1234", "nathan",
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
        self.assertEqual(response.status_code, 201)

    def test_create_duplicate_course(self):
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
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 10, access_token)
        
        class_id = response.json()["inserted_id"]
        
        # Assert
        self.assertEqual(response.status_code, 201)
        self.assertGreater(len(class_id), 0)

    def test_create_duplicate_class(self):
        # Register & Login
        user_register(101, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student", "Registrar"])
        access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Send request
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 10, access_token)
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 10, access_token)

        # Assert
        self.assertEqual(response.status_code, 409)

    def test_update_class(self):
        # Register & Login
        user_register(101, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student", "Registrar"])
        access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Data
        old_instructor_id = 1
        new_instructor_id = 2

        # Create a class
        response = create_class("SOC", 301, 2, 2024, "FA", old_instructor_id, 10, access_token)
        
        class_id = response.json()["inserted_id"]

        # Prepare header & message body        
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {access_token}"
        }
        body = {
            "instructor_cwid": new_instructor_id
        }

        # Send request
        url = f'{BASE_URL}/api/classes/{class_id}'
        response = requests.patch(url, headers=headers, json=body)

        # Assert
        self.assertEqual(response.status_code, 200)

        # Direct Access DB to check if data has been updated successfully
        query_params = {
            "KeyConditionExpression": Key("id").eq(class_id)
        }
        dynamodb = get_dynamodb()
        response = dynamodb.Table(TableNames.CLASSES).query(**query_params)
        items = response["Items"]

        # Assert
        self.assertGreater(len(items), 0)
        self.assertEqual(items[0]["instructor_id"], new_instructor_id)
        

    def test_update_nonexisting_class(self):
        # Register & Login
        user_register(101, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student", "Registrar"])
        access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Data
        item_id = 99999
        old_instructor_id = 1
        new_instructor_id = 22

        # Prepare header & message body        
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {access_token}"
        }
        body = {
            "instructor_cwid": new_instructor_id
        }

        # Send request
        url = f'{BASE_URL}/api/classes/{item_id}'
        response = requests.patch(url, headers=headers, json=body)

        # Assert
        self.assertEqual(response.status_code, 404)

    def test_delete_class(self):
        # Register & Login
        user_register(101, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student", "Registrar"])
        access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Send request
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 10, access_token)
        
        class_id = response.json()["inserted_id"]

        # # Prepare header & message body        
        # headers = {
        #     "Content-Type": "application/json;",
        #     "Authorization": f"Bearer {access_token}"
        # }

        # # Send request
        # url = f'{BASE_URL}/api/classes/{class_id}'
        # response = requests.delete(url, headers=headers)
        
        # # Assert
        # self.assertEqual(response.status_code, 200)

        # # Direct Access DB to check if data has been updated successfully
        # query_params = {"KeyConditionExpression": Key("id").eq(class_id)}
        # dynamodb = get_dynamodb()
        # response = dynamodb.Table(TableNames.CLASSES).query(**query_params)
        # items = response["Items"]

        # # Assert
        # self.assertEqual(len(items), 0)
        

    def test_delete_nonexisting_class(self):
        # Register & Login
        user_register(101, "abc@csu.fullerton.edu", "1234", "nathan",
                      "nguyen", ["Student", "Registrar"])
        access_token = user_login("abc@csu.fullerton.edu", password="1234")

        # Data
        item_id = 99999

        # Prepare header & message body        
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/classes/{item_id}'
        response = requests.delete(url, headers=headers)
        
        # Assert
        self.assertEqual(response.status_code, 404)
    
if __name__ == '__main__':
    unittest.main()