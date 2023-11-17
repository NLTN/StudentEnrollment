from .Dynamo import Dynamo
from .models import Settings

settings = Settings()
dynamo = Dynamo(config=settings)

create_class_table_params = {
    "TableName":"Classes",
    "KeySchema":[
        {
            "AttributeName": "id",
            "KeyType": "HASH"
        }
    ],
    "AttributeDefinitions":[
        {
            "AttributeName": "id",
            "AttributeType": "N"
        }
    ],
    "ProvisionedThroughput": {"ReadCapacityUnits": 3, "WriteCapacityUnits": 3},
}

create_course_table_params = {
    "TableName":'Courses',
    "KeySchema":[
        {
            'AttributeName': 'department_code',
            'KeyType': 'HASH'
        },
        {
            'AttributeName': 'course_no',
            'KeyType': 'RANGE'
        }
    ],
    "AttributeDefinitions":[
        {
            'AttributeName': 'department_code',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'course_no',
            'AttributeType': 'N'
        }
    ],
    "ProvisionedThroughput": {"ReadCapacityUnits": 3, "WriteCapacityUnits": 3},
}

create_personnel_table_params = {
    "TableName":"Personnel",
    "KeySchema":[
        {
            "AttributeName": "cwid",
            "KeyType": "HASH"
        }
    ],
    "AttributeDefinitions":[
        {
            "AttributeName": "cwid",
            "AttributeType": "N"
        }
    ],
    "ProvisionedThroughput": {"ReadCapacityUnits": 3, "WriteCapacityUnits": 3},
}

create_config_table_params = {
    "TableName":'Configs',
    "KeySchema":[
        {
            'AttributeName': 'variable_name',
            'KeyType': 'HASH'
        }
    ],
    "AttributeDefinitions":[
        {
            'AttributeName': 'variable_name',
            'AttributeType': 'S'
        }        
    ],
    "ProvisionedThroughput": {"ReadCapacityUnits": 3, "WriteCapacityUnits": 3},
}

create_enrollment_table_params = {
    "TableName":"Enrollments",
    "KeySchema":[
        {
            "AttributeName": "class_id",
            "KeyType": "HASH"
        },
        {
            "AttributeName": "student_cwid",
            "KeyType": "RANGE"
        }
    ],
    "AttributeDefinitions":[
        {
            "AttributeName": "class_id",
            "AttributeType": "N"
        },
        {
            "AttributeName": "student_cwid",
            "AttributeType": "N"
        },
        {
            "AttributeName": "term",
            "AttributeType": "S"
        }
    ],
    "ProvisionedThroughput": {"ReadCapacityUnits": 3, "WriteCapacityUnits": 3},
    "GlobalSecondaryIndexes": [
        {
            "IndexName": "term-index",
            "KeySchema": [
                { "AttributeName": "term", "KeyType": "HASH" }
            ],
            "Projection": {
                "ProjectionType": "ALL"
            },
            "ProvisionedThroughput": {
                "ReadCapacityUnits": 3,
                "WriteCapacityUnits": 3
            }
        }
    ]
}

required_tables = ["Classes", "Courses", "Personnel", "Configs","Enrollments"]
existing_tables = [table.name for table in dynamo.list_tables()]

params= {
    "Classes" : create_class_table_params,
    "Courses" : create_course_table_params,
    "Personnel" : create_personnel_table_params,
    "Configs" : create_config_table_params,
    "Enrollments" : create_enrollment_table_params,
}


for table in required_tables:
    if table in existing_tables:
        print(f"existing table {table} found, recreating table")
        dynamo.delete_table(table)
    dynamo.create_table(create_params=params[table])

# seeding auto_enrollment_enabled config
item = {
    "variable_name" : "auto_enrollment_enabled",
    "value" : True
}

dynamo.put_item(tablename="Configs", item=item)