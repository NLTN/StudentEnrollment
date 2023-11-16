import boto3
from botocore.exceptions import ClientError

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