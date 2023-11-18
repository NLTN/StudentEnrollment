import boto3
from botocore.exceptions import ClientError

DYNAMO_TABLENAMES = {
    'class' : "Class",
    "course" : "Course",
    "personnel" : "Personnel",
    "enrollment" : "Enrollment",
    "config" : "Config",
    "waitlist_participation" : "Waitlist_Participation"
}

def get_db():
    # Initialize a DynamoDB client
    dynamodb = boto3.resource("dynamodb", endpoint_url = "http://localhost:8000")
    return dynamodb

class DynamoDB:
    def query(self, tablename: str, query_params: dict):
        try:
            dynamodb = get_db()
            result = dynamodb.Table(tablename).query(**query_params)
            items = result["Items"]
            return items
        except ClientError as err:
            raise err

    def put_item(self, tablename: str, item: dict):
        try:
            dynamodb = get_db()
            dynamodb.Table(tablename).put_item(Item=item)
            return True

        except ClientError as err:
            raise err