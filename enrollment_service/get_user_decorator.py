from functools import wraps
from .models import Personnel
from boto3.dynamodb.conditions import Key
from fastapi import Request

def get_or_create_user(request: Request):
    personnel_obj = {
        "cwid" : request.headers["x-cwid"],
        "first_name" : request.headers["x-first-name"],
        "last_name" : request.headers["x-last-name"],
        "roles" : request.headers["x-roles"].split(",")
    }
    # print(type(personnel_obj["cwid"]))
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
# def get_personnel(*, role: str):
#     def inner(func):
#         @wraps(func)
#         def get_personnel_method( *args, **kwargs):
            
#             # db = kwargs["request"].app.state.dynamo
            
#             # user_cwid = kwargs["request"].headers["x-cwid"]
#             # user_first_name =  kwargs["request"].headers["x-first-name"]
#             # user_last_name =  kwargs["request"].headers["x-last-name"]
#             # user_roles = kwargs["request"].headers["x-roles"].split(",")
           
#             # query_params = {
#             #     "KeyConditionExpression" : Key("cwid").eq(user_cwid) 
#             # }
#             # get_personnel = db.query(tablename="Personnel", query_params=query_params)
#             # if get_personnel:
#             #     personnel = Personnel(**{
#             #         "cwid" : int(get_personnel[0]["cwid"]),
#             #         "first_name" : get_personnel[0]["first_name"],
#             #         "last_name" : get_personnel[0]["last_name"],
#             #         "roles" : list(get_personnel[0]["roles"])
#             #     }) 

#             #     kwargs["user"] = personnel
                
#             # else:
              
#             #     new_user = {
#             #         "cwid" : user_cwid,
#             #         "first_name" : user_first_name,
#             #         "last_name" : user_last_name,
#             #         "roles" : user_roles
#             #     }

#             #     if db.put_item(tablename="Personnel", item=new_user):
#             #         kwargs["user"] = Personnel(**new_user)

#             # kwargs["dynamo"] = db
#             print(kwargs)
#             return func(*args, **kwargs)
#         return get_personnel_method
#     return inner

