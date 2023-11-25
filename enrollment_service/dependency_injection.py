from fastapi import Header, Depends
from .dynamoclient import DynamoClient
from .db_connection import get_dynamodb, TableNames


def sync_user_account(
        cwid: int = Header(alias="x-cwid"),
        first_name: str = Header(alias="x-first-name"),
        last_name: str = Header(alias="x-last-name"),
        roles: list[str] = Header(alias="x-roles"),
        dynamodb: DynamoClient = Depends(get_dynamodb)):
    """
    Synchronizes user account information to a DynamoDB table.

    Parameters:
    - cwid (int): The user's unique identifier.
    - first_name (str): The user's first name.
    - last_name (str): The user's last name.
    - roles (str): A comma-separated string of user roles.
    - dynamodb (DynamoClient): DynamoDB client used to interact with the database.

    Raises:
    - Exception: Any unexpected error during the process.

    Example:
    ```python
    @registrar_router.post("/classes/", dependencies=[Depends(sync_user_account)])
    ```

    Note:
    This function is designed to be used as a FastAPI dependency in web applications.
    """
    try:
        kwargs = {"Key": {"cwid": cwid}}
        response = dynamodb.get_item(TableNames.PERSONNEL, kwargs)

        if "Item" not in response:
            # ***********************************************
            # New user detected. INSERT user
            # ***********************************************
            kwargs = {
                "Item": {
                    "cwid": cwid,
                    "first_name": first_name,
                    "last_name": last_name,
                    "roles": roles
                }
            }
            dynamodb.put_item(TableNames.PERSONNEL, kwargs)

        elif response["Item"]["first_name"] != first_name \
                or response["Item"]["last_name"] != last_name \
                or response["Item"]["roles"] != roles:
            # ***********************************************
            # Data changes dectected. UPDATE data
            # ***********************************************
            kwargs = {
                "Key": {"cwid": cwid},
                "UpdateExpression": "SET first_name = :first_name, last_name = :last_name, roles = :roles",
                "ExpressionAttributeValues": {":first_name": first_name, ":last_name": last_name, ":roles": roles},
            }
            dynamodb.update_item(TableNames.PERSONNEL, kwargs)

    except Exception as e:
        raise Exception(f"UserAccountSyncFailed: {e}")
