from typing import Annotated, Any
import sqlite3
from http import HTTPStatus
from fastapi.responses import JSONResponse
from fastapi import Depends, HTTPException, Header, Body, status, APIRouter, Request
from datetime import datetime
from redis import Redis, RedisError
from .dynamoclient import DynamoClient
from .db_connection import get_db, get_redisdb, get_dynamodb, TableNames
from .enrollment_helper import enroll_students_from_waitlist, is_auto_enroll_enabled
from .dependency_injection import *
from .models import Personnel, ClassCreate
from botocore.exceptions import ClientError

WAITLIST_CAPACITY = 15
MAX_NUMBER_OF_WAITLISTS_PER_STUDENT = 3

student_router = APIRouter()


@student_router.get("/classes/available/", dependencies=[Depends(get_or_create_user)])
def get_available_classes(dynamodb: DynamoClient = Depends(get_dynamodb)):
    try:
        # ---------------------------------------------------------------------
        # Get the information of the class
        # ---------------------------------------------------------------------
        get_class_params = {
            "IndexName": "available_status-index",
            "KeyConditionExpression": "available_status = :value",
            "ExpressionAttributeValues": {":value": "true"},
        }
        responses = dynamodb.query(TableNames.CLASSES, get_class_params)
        response_json = responses["Items"]

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=e)
    else:
        return response_json


@student_router.post("/enrollment/", dependencies=[Depends(get_or_create_user)], status_code=status.HTTP_201_CREATED)
def enroll(class_id: Annotated[int, Body(embed=True)],
           student_id: int = Header(
               alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
           first_name: str = Header(alias="x-first-name"),
           last_name: str = Header(alias="x-last-name"),
           redisdb: Redis = Depends(get_redisdb),
           dynamodb: DynamoClient = Depends(get_dynamodb)):
    """
    Student enrolls in a class

    Parameters:
    - class_id (int, in the request body): The unique identifier of the class where students will be enrolled.
    - student_id (int, in the request header): The unique identifier of the student who is enrolling.

    Returns:
    - HTTP_200_OK on success

    Raises:
    - HTTPException (400): If there are no available seats.
    - HTTPException (404): If the specified class does not exist.
    - HTTPException (409): If a conflict occurs (e.g., The student has already enrolled into the class).
    - HTTPException (500): If there is an internal server error.
    """
    try:
        # API Response data
        response_json = {}

        # ---------------------------------------------------------------------
        # Get the information of the class
        # ---------------------------------------------------------------------
        get_class_params = {
            "Get": {
                "TableName": TableNames.CLASSES,
                "Key": {
                    "id": class_id
                }
            }
        }
        responses = dynamodb.transact_get_items([get_class_params])

        if not responses[0]:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                detail="Class Not Found")

        class_info = ClassCreate(**responses[0]["Item"])

        # ---------------------------------------------------------------------
        # Count the number of students enrolled in the class
        # ---------------------------------------------------------------------
        kwargs = {
            "KeyConditionExpression": "class_id = :value",
            "ExpressionAttributeValues": {":value": class_id},
            "Select": "COUNT"
        }

        response = dynamodb.query(TableNames.ENROLLMENTS, kwargs)

        num_students_enrolled = response["Count"]

        # ---------------------------------------------------------------------
        # If there is an open seat, enroll the student in the class
        # ---------------------------------------------------------------------
        if class_info.room_capacity > num_students_enrolled:

            # After student enrolled in the class,
            # If there will be NO open seats (Class will be full),
            # Then, set available status to "false".
            # Otherwise, "true"
            available_status = "true" if class_info.room_capacity > num_students_enrolled + 1 else "false"

            TransactItems = [
                {
                    'Put': {
                        'TableName': TableNames.ENROLLMENTS,
                        "Item": {
                            "class_id": class_id,
                            "student_cwid": student_id
                        },
                        "ConditionExpression": "attribute_not_exists(class_id) AND attribute_not_exists(student_cwid)"
                    }
                },
                {
                    'Update': {
                        'TableName': TableNames.CLASSES,
                        'Key': {
                            'id': class_id
                        },
                        'UpdateExpression': 'SET available_status = :new_value',
                        'ExpressionAttributeValues': {
                            ':new_value': available_status
                        }
                    }
                }
            ]

            response = dynamodb.transact_write_items(TransactItems)
            print(response)
            # dynamodb.put_item(TableNames.ENROLLMENTS, kwargs)

            response_json = JSONResponse(status_code=HTTPStatus.CREATED, content={
                                         "detail": "Enrolled successfully"})

        # ---------------------------------------------------------------------
        # Else If the waitlist is not full, add the student to the waitlist
        # ---------------------------------------------------------------------
        else:
            num_students_on_waitlist = redisdb.zcard(class_id)

            if num_students_on_waitlist < WAITLIST_CAPACITY:
                current_timestamp = int(datetime.utcnow().timestamp())
                redisdb.zadd(class_id, {student_id: current_timestamp})

                response_json = JSONResponse(status_code=HTTPStatus.CREATED,
                                             content={"detail": "Placed on waitlist"})
            else:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                                    detail="The class & the waitlist is full")

    except ClientError as e:
        if e.response["Error"]["Code"] == "TransactionCanceledException":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Transaction Canceled")
        elif e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Already enrolled")
        else:
            raise Exception(e.response)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=e)
    else:
        return response_json


@student_router.delete("/enrollment/{class_id}", status_code=status.HTTP_200_OK)
def drop_class(
        class_id: int,
        student_id: int = Header(
            alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
        dynamodb: DynamoClient = Depends(get_dynamodb)):
    """
    Handles a DELETE request to drop a student (himself/herself) from a specific class.

    Parameters:
    - class_id (int): The ID of the class from which the student wants to drop.
    - student_id (int, in the header): A unique ID for students, instructors, and registrars.

    Returns:
    - dict: A dictionary with the detail message indicating the success of the operation.

    Raises:
    - HTTPException (409): If a conflict occurs
    """
    try:
        # ---------------------------------------------------------------------
        # DELETE FROM enrollment table
        # ---------------------------------------------------------------------
        kwargs = {
            "Key": {
                "class_id": class_id,
                "student_cwid": student_id
            },
            # check if the item exists
            "ConditionExpression": "attribute_exists(class_id) AND attribute_exists(student_cwid)"
        }
        dynamodb.delete_item(TableNames.ENROLLMENTS, kwargs)

        # ---------------------------------------------------------------------
        # INSERT INTO droplist table
        # ---------------------------------------------------------------------
        kwargs = {
            "Item": {
                "class_id": class_id,
                "student_cwid": student_id
            }
        }
        dynamodb.put_item(TableNames.DROPLIST, kwargs)

        # ---------------------------------------------------------------------
        # Trigger auto enrollment
        # ---------------------------------------------------------------------

    except ClientError as e:
        print(e.response)
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                detail="Item already exists")
        else:
            raise Exception(e.response)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                            detail="INTERNAL SERVER ERROR")
    else:
        return {"detail": "Item deleted successfully"}


@student_router.get("/waitlist/{class_id}/position/")
def get_current_waitlist_position(
        class_id: int,
        student_id: int = Header(
            alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
        redisdb: Redis = Depends(get_redisdb)):
    """
    Retreive the position of the student on the waitlist.

    Returns:
    - int: The position of the student on the waitlist

    Raises:
    - HTTPException (404): If record not found
    """
    try:
        # Get the rank of the member in the sorted set
        rank = redisdb.zrank(class_id, student_id)

        if rank is not None:
            response_json = {"position": rank + 1}
        else:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                detail="Record Not Found")
    except RedisError as e:
        print(f"RedisError: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    else:
        return response_json
    finally:
        redisdb.close()  # Close the Redis connection


@student_router.delete("/waitlist/{class_id}/", status_code=status.HTTP_200_OK)
def remove_from_waitlist(
        class_id: int,
        student_id: int = Header(
            alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
        redisdb: Redis = Depends(get_redisdb)):
    """
    Students remove themselves from waitlist

    Parameters:
    - class_id (int): The ID of the class from which the student wants to drop.
    - student_id (int, in the header): A unique ID for students, instructors, and registrars.

    Returns:
    - dict: A dictionary with the detail message indicating the success of the operation.

    Raises:
    - HTTPException (409): If a conflict occurs
    """
    try:
        # Get the rank of the member in the sorted set
        deleted_count = redisdb.zrem(class_id, student_id)

        if deleted_count > 0:
            response_json = {"detail": "Item deleted successfully"}
        else:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                detail="Record Not Found")
    except RedisError as e:
        print(f"RedisError: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    else:
        return response_json
    finally:
        redisdb.close()  # Close the Redis connection
