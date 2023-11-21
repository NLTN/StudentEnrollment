from .db_connection import get_dynamodb, TableNames

dynamodb = get_dynamodb()

create_class_table_params = {
    "TableName": TableNames.CLASSES,
    "KeySchema": [
        {
            "AttributeName": "id",
            "KeyType": "HASH"
        }
    ],
    "AttributeDefinitions": [
        {
            "AttributeName": "id",
            "AttributeType": "N"
        },
        {
            "AttributeName": "available_status",
            "AttributeType": "S"
        }
    ],
    "ProvisionedThroughput": {"ReadCapacityUnits": 3, "WriteCapacityUnits": 3},
    "GlobalSecondaryIndexes": [
        {
            "IndexName": "available_status-index",
            "KeySchema": [
                {"AttributeName": "available_status", "KeyType": "HASH"}
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

create_course_table_params = {
    "TableName": TableNames.COURSES,
    "KeySchema": [
        {
            'AttributeName': 'department_code',
            'KeyType': 'HASH'
        },
        {
            'AttributeName': 'course_no',
            'KeyType': 'RANGE'
        }
    ],
    "AttributeDefinitions": [
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
    "TableName": TableNames.PERSONNEL,
    "KeySchema": [
        {
            "AttributeName": "cwid",
            "KeyType": "HASH"
        }
    ],
    "AttributeDefinitions": [
        {
            "AttributeName": "cwid",
            "AttributeType": "N"
        }
    ],
    "ProvisionedThroughput": {"ReadCapacityUnits": 3, "WriteCapacityUnits": 3},
}

create_config_table_params = {
    "TableName": TableNames.CONFIGS,
    "KeySchema": [
        {
            'AttributeName': 'variable_name',
            'KeyType': 'HASH'
        }
    ],
    "AttributeDefinitions": [
        {
            'AttributeName': 'variable_name',
            'AttributeType': 'S'
        }
    ],
    "ProvisionedThroughput": {"ReadCapacityUnits": 3, "WriteCapacityUnits": 3},
}

create_enrollment_table_params = {
    "TableName": TableNames.ENROLLMENTS,
    "KeySchema": [
        {
            "AttributeName": "class_id",
            "KeyType": "HASH"
        },
        {
            "AttributeName": "student_cwid",
            "KeyType": "RANGE"
        }
    ],
    "AttributeDefinitions": [
        {
            "AttributeName": "class_id",
            "AttributeType": "N"
        },
        {
            "AttributeName": "student_cwid",
            "AttributeType": "N"
        }
    ],
    "ProvisionedThroughput": {"ReadCapacityUnits": 3, "WriteCapacityUnits": 3}
}

create_droplist_table_params = {
    "TableName": TableNames.DROPLIST,
    "KeySchema": [
        {
            "AttributeName": "class_id",
            "KeyType": "HASH"
        },
        {
            "AttributeName": "student_cwid",
            "KeyType": "RANGE"
        }
    ],
    "AttributeDefinitions": [
        {
            "AttributeName": "class_id",
            "AttributeType": "N"
        },
        {
            "AttributeName": "student_cwid",
            "AttributeType": "N"
        }
    ],
    "ProvisionedThroughput": {"ReadCapacityUnits": 3, "WriteCapacityUnits": 3}
}


# ---------------------------------------------------------------------
# Delete all existing tables
# ---------------------------------------------------------------------
existing_tables = [table.name for table in dynamodb.list_tables()]

for table in existing_tables:
    dynamodb.delete_table(table)


# ---------------------------------------------------------------------
# Create tables
# ---------------------------------------------------------------------
dynamodb.create_table(create_class_table_params)
dynamodb.create_table(create_course_table_params)
dynamodb.create_table(create_personnel_table_params)
dynamodb.create_table(create_config_table_params)
dynamodb.create_table(create_enrollment_table_params)
dynamodb.create_table(create_droplist_table_params)


# ---------------------------------------------------------------------
# seeding auto_enrollment_enabled config
# ---------------------------------------------------------------------
kwargs = {
    "Item": {
        "variable_name": "auto_enrollment_enabled",
        "value": True
    }
}

dynamodb.put_item(TableNames.CONFIGS, kwargs)
