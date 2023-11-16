from .models import Personnel
from boto3.dynamodb.conditions import Key
from fastapi import Request

def get_or_create_user(request: Request):
    personnel_obj = {
        "cwid" : int(request.headers["x-cwid"]),
        "first_name" : request.headers["x-first-name"],
        "last_name" : request.headers["x-last-name"],
        "roles" : request.headers["x-roles"].split(",")
    }

    personnel = Personnel(**personnel_obj)

    query_params = {
        "KeyConditionExpression" : Key("cwid").eq(personnel.cwid)
    }
    
    get_personnel = request.app.state.dynamo.query(tablename= "Personnel", query_params=query_params)
    
    if not get_personnel:
        request.app.state.dynamo.put_item(tablename="Personnel", item=personnel_obj)
   
    request.app.state.current_user = personnel

def get_current_user(request: Request):
    return request.app.state.current_user

def get_dynamo(request: Request):
    return request.app.state.dynamo


