import boto3

# Initialize a DynamoDB client
dynamodb = boto3.resource("dynamodb", endpoint_url = "http://localhost:8000")

def insert_courses():
    table_name = "Courses"
    table = dynamodb.Table(table_name)
    sample_data = [
        {"department_code": "CPSC", "course_no": 999, "title": "TEST 999"},
        {"department_code": "SOC", "course_no": 301, "title": "TEST 301"},
    ]
    for item in sample_data:
        table.put_item(Item=item)

    print(f"Table {table_name}: {len(sample_data)} items")

def insert_personel():
    table_name = "Personnel"
    table = dynamodb.Table(table_name)
    sample_data = [
        {"cwid": 1, "first_name": "John", "last_name": "Smith", "roles": ["Instructor", "Registrar"]},
        {"cwid": 2, "first_name": "Mary", "last_name": "Brown", "roles": ["Instructor"]},
        {"cwid": 3, "first_name": "Nathan", "last_name": "Doe", "roles": ["Student"]}
    ]
    for item in sample_data:
        table.put_item(Item=item)

    print(f"Table {table_name}: {len(sample_data)} items")

if __name__ == "__main__":
    insert_personel()
    insert_courses()