from .Dynamo import Dynamo
from .models import Settings

settings = Settings()
dynamo = Dynamo(config=settings)

create_class_table_params = {
    "TableName":'Class',
    "KeySchema":[
        {
            'AttributeName': 'department',
            'KeyType': 'HASH'
        },
        {
            'AttributeName': 'course_section',
            'KeyType': 'RANGE'
        }
    ],
    "AttributeDefinitions":[
        {
            'AttributeName': 'department',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'course_section',
            'AttributeType': 'S'
        }
    ],
    "ProvisionedThroughput": {"ReadCapacityUnits": 3, "WriteCapacityUnits": 3},
}

create_personnel_table_params = {
    "TableName":'Personnel',
    "KeySchema":[
        {
            'AttributeName': 'role',
            'KeyType': 'HASH'
        },
        {
            'AttributeName': 'cwid',
            'KeyType': 'RANGE'
        }
    ],
    "AttributeDefinitions":[
        {
            'AttributeName': 'role',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'cwid',
            'AttributeType': 'S'
        }
    ],
    "ProvisionedThroughput": {"ReadCapacityUnits": 3, "WriteCapacityUnits": 3},
}

create_enrollment_period_status_table_params = {
    "TableName":'Enrollment_Period_Status',
    "KeySchema":[
        {
            'AttributeName': 'year',
            'KeyType': 'HASH'
        },
        {
            'AttributeName': 'semester',
            'KeyType': 'RANGE'
        }
    ],
    "AttributeDefinitions":[
        {
            'AttributeName': 'year',
            'AttributeType': 'N'
        },
        {
            'AttributeName': 'semester',
            'AttributeType': 'S'
        }
    ],
    "ProvisionedThroughput": {"ReadCapacityUnits": 3, "WriteCapacityUnits": 3},
}

create_enrollment_table_params = {
    "TableName":'Enrollment',
    "KeySchema":[
        {
            'AttributeName': 'department',
            'KeyType': 'HASH'
        },
        {
            'AttributeName': 'course_section',
            'KeyType': 'RANGE'
        }
    ],
    "AttributeDefinitions":[
        {
            'AttributeName': 'department',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'course_section',
            'AttributeType': 'S'
        }
    ],
    "ProvisionedThroughput": {"ReadCapacityUnits": 3, "WriteCapacityUnits": 3},
}

create_waitlist_participation_table_params = {
    "TableName":'Waitlist_Participation',
    "KeySchema":[
        {
            'AttributeName': 'year',
            'KeyType': 'HASH'
        },
        {
            'AttributeName': 'semester',
            'KeyType': 'RANGE'
        }
    ],
    "AttributeDefinitions":[
        {
            'AttributeName': 'year',
            'AttributeType': 'N'
        },
        {
            'AttributeName': 'semester',
            'AttributeType': 'S'
        }
    ],
    "ProvisionedThroughput": {"ReadCapacityUnits": 3, "WriteCapacityUnits": 3},
}

required_tables = ["Class", "Personnel", "Enrollment_Period_Status", "Enrollment", "Waitlist_Participation"]
existing_tables = [table.name for table in dynamo.list_tables()]

params= {
    "Class" : create_class_table_params,
    "Personnel" : create_personnel_table_params,
    "Enrollment_Period_Status" : create_enrollment_period_status_table_params,
    "Enrollment" : create_enrollment_table_params,
    "Waitlist_Participation" : create_waitlist_participation_table_params,
}


for table in required_tables:
    if table in existing_tables:
        print(f'existing table {table} found, recreating table')
        dynamo.delete_table(table)
    dynamo.create_table(create_params=params[table])
    




