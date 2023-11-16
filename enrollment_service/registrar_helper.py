from boto3.dynamodb.conditions import Key, Attr
from .models import *

def generate_get_enrollment_period_params():
    query_params = {
        "KeyConditionExpression" : Key("variable_name").eq("auto_enrollment_enabled")
    }
    return query_params

def generate_update_enrollment_period_params(enabled: bool):
    update_params = {
        "Key" : {
            "variable_name" : "auto_enrollment_enabled"
        },
        "UpdateExpression" : "SET #value = :i",
        "ExpressionAttributeValues": {
            ":i" : enabled
        },
        "ExpressionAttributeNames":  {
            "#value" : "value"
        },
        "ReturnValues": "UPDATED_NEW"
    }
    return update_params

def generate_get_course_params(request: Course, **kwargs):
    query_params = {
        "KeyConditionExpression" : Key("department_code").eq(request.department_code) & Key("course_no").eq(request.course_no)
    }
    if kwargs:
        query_params.update(kwargs)
    return query_params

def generate_get_class_params(request: ClassCreate, **kwargs):
    query_params = {
        "KeyConditionExpression" : Key("term").eq(f'{request.semester}-{request.year}') & Key("class").eq(f'{request.department_code}-{request.course_no}-{request.section_no}')
    }
    if kwargs:
        query_params.update(kwargs)
    return query_params