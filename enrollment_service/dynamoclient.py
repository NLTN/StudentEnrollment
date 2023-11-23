# Based off https://github.com/Jordan-Ng/cpsc449-project3-group8/commit/849e96fbb9b64a790cd6e7b631c66f2ce09b2d68

import boto3


class DynamoClient:
    def __init__(self,
                 aws_access_key: str = None,
                 aws_secret_key: str = None,
                 aws_region: str = None,
                 endpoint_url: str = None):
        self.dyn_resource = boto3.resource("dynamodb",
                                           aws_access_key_id=aws_access_key,
                                           aws_secret_access_key=aws_secret_key,
                                           region_name=aws_region,
                                           endpoint_url=endpoint_url
                                           )

    def list_tables(self):
        return list(self.dyn_resource.tables.all())

    def create_table(self, kwargs: dict):
        self.dyn_resource.create_table(**kwargs)

    def delete_table(self, table_name: str):
        client = self.dyn_resource.meta.client
        response = client.delete_table(TableName=table_name)
        return response

    def get_item(self, tablename: str, kwargs: dict):
        return self.dyn_resource.Table(tablename).get_item(**kwargs)
    
    def put_item(self, tablename: str, kwargs: dict):
        return self.dyn_resource.Table(tablename).put_item(**kwargs)

    def update_item(self, tablename: str, kwargs: dict):
        return self.dyn_resource.Table(tablename).update_item(**kwargs)
    
    def batch_write_item(self, kwargs: dict):
        return self.dyn_resource.batch_write_item(**kwargs)

    def query(self, tablename: str, kwargs: dict):
        return self.dyn_resource.Table(tablename).query(**kwargs)

    def delete_item(self, tablename: str, kwargs: dict):
        return self.dyn_resource.Table(tablename).delete_item(**kwargs)

    def transact_get_items(self, TransactItems: list):
        client = self.dyn_resource.meta.client
        result = client.transact_get_items(TransactItems=TransactItems)
        return result["Responses"]

    def transact_write_items(self, TransactItems: list):
        client = self.dyn_resource.meta.client
        return client.transact_write_items(TransactItems=TransactItems)
