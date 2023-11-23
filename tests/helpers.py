import os
import requests
from tests.settings import *

class SampleUsers:
    class registrar:
        id: int
        access_token: str
    class instructor:
        id: int
        access_token: str
    class student1:
        id: int
        access_token: str
    class student2:
        id: int
        access_token: str

def create_sample_users():
    users = SampleUsers()
    users.registrar.id = 800001
    users.instructor.id = users.registrar.id
    users.student1.id = 900001
    users.student2.id = 900002

    # ------------------ Registrar & Instructor ------------------
    user_register(users.registrar.id, "john@fullerton.edu", "1234", "john",
                    "smith", ["Registrar", "Instructor"])
    users.registrar.access_token = user_login("john@fullerton.edu", password="1234")
    users.instructor.access_token = users.registrar.access_token
    
    # ------------------ Student 01 ------------------
    user_register(users.student1.id, "abc@csu.fullerton.edu", "1234", "nathan",
                    "nguyen", ["Student"])
    users.student1.access_token = user_login("abc@csu.fullerton.edu", password="1234")

    # ------------------ Student 02 ------------------
    user_register(users.student2.id, "abc2@csu.fullerton.edu", "1234", "nathan",
                    "nguyen", ["Student"])
    users.student2.access_token = user_login("abc2@csu.fullerton.edu", password="1234")

    return users
    
def unittest_setUp():
    if USING_LITEFS_TO_REPLICATE_USER_DATABASE:
        # ------- If you're using LiteFS, READ ME -----------
        # In case of using LiteFS to replicate user service database,
        # the data in user database will be reset.

        # Delete the current database, then create a new one
        os.system(f"[ ! -f {USER_DB_PATH} ] || rm {USER_DB_PATH}")
        os.system("sh ./bin/create-user-db.sh > /dev/null")
    else:
        # Backup the current database, then create a new one
        os.system(f"[ ! -f {USER_DB_PATH} ] || cp {USER_DB_PATH} {USER_DB_PATH}.backup")
        os.system("sh ./bin/create-user-db.sh > /dev/null")

    # Reset Enrollment service database
    os.system("sh ./bin/seed.sh > /dev/null")
    os.system("python3 tests/sample_data.py")

    # Reset Redis DB
    os.system("redis-cli FLUSHDB")

def unittest_tearDown():
    if USING_LITEFS_TO_REPLICATE_USER_DATABASE:
        os.system(f"[ ! -f {USER_DB_PATH} ] || rm {USER_DB_PATH}")
        os.system("sh ./bin/create-user-db.sh > /dev/null")
    else:
        # Restore database
        os.system(f"rm -f {USER_DB_PATH}")
        os.system(f"[ ! -f {USER_DB_PATH}.backup ] || mv {USER_DB_PATH}.backup {USER_DB_PATH}")

    # Reset Enrollment service database
    # os.system("sh ./bin/seed.sh > /dev/null")

    # Reset Redis DB
    # os.system("redis-cli FLUSHDB")

def user_register(user_id, username, password, first_name, last_name, roles: list[str]):
    url = f'{BASE_URL}/api/register'
    myobj = {
        "id": user_id,
        "username": username,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
        "roles": roles
    }
    response = requests.post(url, json = myobj)
    return response.status_code == 201 or response.status_code == 200

def user_login(username, password):
    url = f'{BASE_URL}/api/login'
    myobj = {
        "username": username,
        "password": password
    }
    response = requests.post(url, json = myobj)
    if response.status_code == 200:
        data = response.json()
        if "access_token" in data:
            return data["access_token"]
    
    return None

def create_class(dept_code, course_no, section_no, academic_year, semester,
                instructor_id, room_capacity, access_token):
    # Prepare header & message body
    headers = {
        "Content-Type": "application/json;",
        "Authorization": f"Bearer {access_token}"
    }
    body = {
        "department_code": dept_code,
        "course_no": course_no,
        "section_no": section_no,
        "year": academic_year,
        "semester": semester,
        "instructor_cwid": instructor_id,
        "room_capacity": room_capacity
    }

    # Send request
    url = f'{BASE_URL}/api/classes/'
    response = requests.post(url, headers=headers, json=body)
    return response

def enroll_class(class_id, access_token):
    # Prepare header & message body
    headers = {
        "Content-Type": "application/json;",
        "Authorization": f"Bearer {access_token}"
    }
    body = {
        "class_id": class_id
    }

    # Send request
    url = f'{BASE_URL}/api/enrollment/'
    response = requests.post(url, headers=headers, json=body)
    return response
