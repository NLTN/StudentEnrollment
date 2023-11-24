from db_connection import get_dynamodb, TableNames


def insert_courses():
    sample_data = [
        {"department_code": "CPSC", "course_no": 999, "title": "TEST 999"},
        {"department_code": "SOC", "course_no": 301, "title": "TEST 301"},
    ]

    dynamodb = get_dynamodb()
    for item in sample_data:
        dynamodb.Table(TableNames.COURSES).put_item(Item=item)

def insert_personel():
    sample_data = [
        {"cwid": 1, "first_name": "John", "last_name": "Smith", "roles": ["Instructor", "Registrar"]},
        {"cwid": 2, "first_name": "Mary", "last_name": "Brown", "roles": ["Instructor"]},
        {"cwid": 3, "first_name": "Nathan", "last_name": "Doe", "roles": ["Student"]}
    ]

    dynamodb = get_dynamodb()
    for item in sample_data:
        dynamodb.Table(TableNames.PERSONNEL).put_item(Item=item)

def insert_classes():
    sample_data = [
        {
            "id": "2024.SU.CPSC.101.1",
            "department_code": "CPSC",
            "course_no": 101,
            "section_no": 1,
            "year": 2024,
            "semester": "SU",
            "title": "Intro to programming",
            "instructor_id": 1,
            "room_capacity": 30,
            "available": "true"
        },
        {
            "id": "2024.SP.CPSC.332.3",
            "department_code": "CPSC",
            "course_no": 332,
            "section_no": 3,
            "year": 2024,
            "semester": "SP",
            "title": "Databases",
            "instructor_id": 2,
            "room_capacity": 35,
            "available": "true"
        },
    ]

    dynamodb = get_dynamodb()
    for item in sample_data:
        dynamodb.Table(TableNames.CLASSES).put_item(Item=item)

if __name__ == "__main__":
    insert_personel()
    insert_courses()
    insert_classes()