# from typing import Annotated
import sqlite3
from fastapi import Depends, HTTPException, Header, status, APIRouter
from redis import Redis, RedisError
from .dynamoclient import DynamoClient
from .db_connection import get_db, get_redisdb, get_dynamodb, TableNames
from .enrollment_helper import drop_from_enrollment, enroll_students_from_waitlist, is_auto_enroll_enabled

instructor_router = APIRouter()


@instructor_router.get("/classes/{class_id}/students")
def get_current_enrollment(class_id: str,
                           dynamodb: DynamoClient = Depends(get_dynamodb)):
    """
    Retreive current enrollment for the classes.

    Parameters:
    - class_id (int): The ID of the class.

    Returns:
    - dict: A dictionary containing the details of the classes
    """
    try:
        kwargs = {
            "KeyConditionExpression": "class_id = :value",
            "ExpressionAttributeValues": {":value": class_id}
        }
        responses = dynamodb.query(TableNames.ENROLLMENTS, kwargs)
        response_json = responses["Items"]

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=e)
    else:
        return response_json


@instructor_router.get("/classes/{class_id}/waitlist/")
def get_waitlist(class_id: str,
                 redisdb: Redis = Depends(get_redisdb)):
    """
    Retreive current waiting list for the class.

    Parameters:
    - class_id (int): The ID of the class.

    Returns:
    - dict: A dictionary containing the details of the classes
    """
    response_json = []
    try:
        sorted_set_elements = redisdb.zrange(class_id, 0, -1, withscores=True)

        for member, score in sorted_set_elements:
            student_id, first_name, last_name = member.decode('utf-8').split("#")
            item = {
                "student_cwid": student_id,
                "first_name": first_name,
                "last_name": last_name,
                "created_at": score 
            }
            response_json.append(item)
        
    except RedisError as e:
        print(f"RedisError: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    else:
        return response_json
    finally:
        redisdb.close()  # Close the Redis connection


@instructor_router.get("/classes/{class_id}/droplist/")
def get_droplist(class_id: str,
                 dynamodb: DynamoClient = Depends(get_dynamodb)):
    """
    Retreive students who have dropped the class.

    Parameters:
    - class_id (int): The ID of the class.
    
    Returns:
    - dict: A dictionary containing the details of the classes
    """
    try:
        kwargs = {
            "KeyConditionExpression": "class_id = :value",
            "ExpressionAttributeValues": {":value": class_id}
        }
        responses = dynamodb.query(TableNames.DROPLIST, kwargs)
        response_json = responses["Items"]

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=e)
    else:
        return response_json


@instructor_router.delete("/enrollment/{class_id}/{student_id}/administratively/", status_code=status.HTTP_200_OK)
def drop_class(class_id: str,
               student_id: int,
               dynamodb: DynamoClient = Depends(get_dynamodb)):
    """
    Handles a DELETE request to administratively drop a student from a specific class.

    Parameters:
    - class_id (int): The ID of the class from which the student is being administratively dropped.
    - student_id (int): The ID of the student being administratively dropped.
    - instructor_id (int, In the header): A unique ID for students, instructors, and registrars.

    Returns:
    - dict: A dictionary with the detail message indicating the success of the administrative drop.

    Raises:
    - HTTPException (409): If there is a conflict in the delete operation.
    """
    administrative = True
    drop_from_enrollment(class_id, student_id, administrative, dynamodb)
