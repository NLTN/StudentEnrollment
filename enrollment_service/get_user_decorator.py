from functools import wraps
from .models import Personnel
from boto3.dynamodb.conditions import Key

def get_personnel(*, role: str):
    def inner(func):
        @wraps(func)
        def get_personnel_method( *args, **kwargs):
            db = kwargs["request"].app.state.dynamo
            
            user_cwid = kwargs["request"].headers["x-cwid"]
            query_params = {
                "KeyConditionExpression" : Key("role").eq(role) & Key("cwid").eq(user_cwid)
            }
            get_personnel = db.query(tablename="Personnel", query_params=query_params)
            
            if get_personnel:
                personnel = Personnel(**{
                    "cwid" : int(get_personnel[0]["cwid"]),
                    "first_name" : get_personnel[0]["first_name"],
                    "last_name" : get_personnel[0]["last_name"],
                    "role" :get_personnel[0]["role"]
                }) 
           
            kwargs["user"] = personnel
            return func(*args, **kwargs)
        return get_personnel_method
    return inner

