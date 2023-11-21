from .Dynamo import Dynamo, DYNAMO_TABLENAMES
from .models import Settings
from .db_connection import TableNames

settings = Settings()
dynamo = Dynamo(config=settings)

create_class_table_params = {
    "TableName": DYNAMO_TABLENAMES["class"],
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
    "TableName": DYNAMO_TABLENAMES["course"],
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
    "TableName": DYNAMO_TABLENAMES["personnel"],
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
    "TableName": DYNAMO_TABLENAMES["config"],
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
    "TableName": DYNAMO_TABLENAMES["enrollment"],
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

create_droplist_table_params = {
    "TableName": TableNames.DROPLIST,
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
        }
    ],
    "ProvisionedThroughput": {"ReadCapacityUnits": 3, "WriteCapacityUnits": 3}
}

required_tables = [
                    DYNAMO_TABLENAMES["class"], 
                    DYNAMO_TABLENAMES["course"], 
                    DYNAMO_TABLENAMES["personnel"], 
                    DYNAMO_TABLENAMES["config"],
                    DYNAMO_TABLENAMES["enrollment"],
                    TableNames.DROPLIST
                ]
existing_tables = [table.name for table in dynamo.list_tables()]

params= {
    DYNAMO_TABLENAMES["class"]: create_class_table_params,
    DYNAMO_TABLENAMES["course"]: create_course_table_params,
    DYNAMO_TABLENAMES["personnel"]: create_personnel_table_params,
    DYNAMO_TABLENAMES["config"]: create_config_table_params,
    DYNAMO_TABLENAMES["enrollment"]: create_enrollment_table_params,
    TableNames.DROPLIST: create_droplist_table_params
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

dynamo.put_item(tablename=DYNAMO_TABLENAMES["config"], item=item)