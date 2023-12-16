from typing import Annotated, Any
from http import HTTPStatus
from fastapi import Depends, HTTPException, Header, Body, status, APIRouter, Request
from fastapi.responses import JSONResponse
from botocore.exceptions import ClientError
from redis import Redis, RedisError
from .dynamoclient import DynamoClient
from .db_connection import get_redisdb, get_dynamodb, TableNames
from .enrollment_helper import add_to_waitlist, drop_from_enrollment, get_all_available_classes
from .dependency_injection import sync_user_account
from .models import ClassCreate
from datetime import datetime

WAITLIST_CAPACITY = 15
MAX_NUMBER_OF_WAITLISTS_PER_STUDENT = 3

student_router = APIRouter()


@student_router.get("/classes/available/", dependencies=[Depends(sync_user_account)])
def get_available_classes(student_id: int = Header(alias="x-cwid"), 
                          dynamodb: DynamoClient = Depends(get_dynamodb)):
    try:
        # ---------------------------------------------------------------------
        # Get all the classes that have open seats
        # ---------------------------------------------------------------------
        available_classes = get_all_available_classes(dynamodb)
        

        # ---------------------------------------------------------------------
        # Retrieves all the classes that the student is enrolled or waitlisted
        # ---------------------------------------------------------------------
        kwargs = {"Key": {"cwid": student_id}}
        response = dynamodb.get_item(TableNames.PERSONNEL, kwargs)

        my_classes = []
        
        if "enrollments" in response["Item"]:
            my_classes.extend(list(response["Item"]["enrollments"]))

        if "waitlists" in response["Item"]:
            my_classes.extend(list(response["Item"]["waitlists"]))


        # ---------------------------------------------------------------------
        # Get the available classes for this_student by filtering out
        # the classes that the student is enrolled or waitlisted
        #
        # available_classes_for_this_student = available_classes - enrollments - waitlists
        # ---------------------------------------------------------------------
        for item in my_classes:
            available_classes = [e for e in available_classes if e['id'] != item]

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=e)
    else:
        return available_classes


@student_router.post("/enrollment/", dependencies=[Depends(sync_user_account)], status_code=status.HTTP_201_CREATED)
def enroll(class_id: Annotated[str, Body(embed=True)],
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
    - HTTPException (409): If one of these conflicts occurs:
      - The student already enrolled in the class.
      - The student is already on the waitlist.
      - Database conflicts.
    - HTTPException (500): If there is an internal server error.
    - HTTPException (503): If the waitlist is full. Unable to accept new entries at this time.
    """
    try:
        # API Response data
        response_json = {}

        # ---------------------------------------------------------------------
        # Get class information: room_capacity & enrollment_count
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
        # If there is an open seat, enroll the student in the class
        # ---------------------------------------------------------------------
        if class_info.room_capacity > class_info.enrollment_count:

            # After student enrolled in the class,
            # If there will be NO open seats (Class will be full),
            # Then, set available status to "false".
            # Otherwise, "true"
            available = "true" if class_info.room_capacity > class_info.enrollment_count + 1 else "false"

            TransactItems = [
                {
                    # ***********************************************
                    # INSERT new item INTO enrollments table
                    # ***********************************************
                    "Put": {
                        "TableName": TableNames.ENROLLMENTS,
                        "Item": {
                            "class_id": class_id,
                            "student_cwid": student_id,
                            "student_info": {
                                "first_name": first_name,
                                "last_name": last_name
                            }
                        },
                        "ConditionExpression": "attribute_not_exists(class_id) AND attribute_not_exists(student_cwid)"
                    }
                },
                {
                    # ***********************************************
                    # UPDATE class available status & enrollment_count
                    # ***********************************************
                    "Update": {
                        "TableName": TableNames.CLASSES,
                        "Key": {
                            "id": class_id
                        },
                        "UpdateExpression": "SET available = :status, \
                                                enrollment_count = enrollment_count + :step_size",
                        "ExpressionAttributeValues": {
                            ":status": available,
                            ":step_size": 1
                        }
                    }
                },
                {
                    # TODO: refactoring needed
                    # ***********************************************
                    # UPDATE PERSONNEL `enrollments` attribute
                    # ***********************************************
                    "Update": {
                        "TableName": TableNames.PERSONNEL,
                        "Key": {
                            "cwid": student_id
                        },
                        "UpdateExpression": "ADD enrollments :value",
                        "ExpressionAttributeValues": {
                            ":value": {class_id}
                        },
                    }
                }
            ]

            dynamodb.transact_write_items(TransactItems)

            response_json = JSONResponse(status_code=HTTPStatus.CREATED, content={
                                         "detail": "Enrolled successfully"})

        # ---------------------------------------------------------------------
        # Else, Check & Add the student to the waitlist
        # ---------------------------------------------------------------------
        else:
            # ***********************************************
            # Check number of waitlists limit per student
            # ***********************************************
            kwargs = {"Key": {"cwid": student_id}}
            response = dynamodb.get_item(TableNames.PERSONNEL, kwargs)

            if "waitlists" in response["Item"] and MAX_NUMBER_OF_WAITLISTS_PER_STUDENT <= len(response["Item"]["waitlists"]):
                raise HTTPException(status_code=HTTPStatus.CONFLICT,
                                    detail="Exceed number of waitlists limit")

            # ***********************************************
            # Generate redis sorted set member name
            # ***********************************************
            new_member = f"{student_id}#{first_name}#{last_name}"

            # ***********************************************
            # Check if the student is already on the waitlist
            # ***********************************************
            rank = redisdb.zrank(class_id, new_member)

            if rank is not None:
                raise HTTPException(status_code=HTTPStatus.CONFLICT,
                                    detail="Already on the waitlist")

            # ***********************************************
            # Check waitlist capacity
            # ***********************************************
            num_students_on_waitlist = redisdb.zcard(class_id)

            if num_students_on_waitlist >= WAITLIST_CAPACITY:
                raise HTTPException(status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                                    detail="Waitlist is full")

            # ***********************************************
            # OK. Checks passed. Place the student on waitlist
            # ***********************************************
            score = int(datetime.utcnow().timestamp())
            add_to_waitlist(class_id, class_info.title, student_id, new_member, score)

            # Return value
            response_json = JSONResponse(status_code=HTTPStatus.CREATED,
                                         content={"detail": "Successfully placed on the waitlist"})

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
    finally:
        redisdb.close()  # Close the Redis connection


@student_router.delete("/enrollment/{class_id}", status_code=status.HTTP_200_OK)
def drop_class(
        class_id: str,
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
    administrative = False
    drop_from_enrollment(class_id, student_id, administrative, dynamodb)

def get_last_modified_timestamp(class_id: str, redisdb: Redis) -> float:
   last_modified_key = f"{class_id}:last_modified"
   last_modified_timestamp = redisdb.get(last_modified_key)
   return float(last_modified_timestamp) if last_modified_timestamp else None

def update_last_modified_timestamp(class_id: str, redisdb: Redis):
   last_modified_key = f"{class_id}:last_modified"
   new_last_modified_timestamp = int(datetime.utcnow().timestamp())
   redisdb.set(last_modified_key, new_last_modified_timestamp)

@student_router.get("/waitlist/{class_id}/position/")
def get_current_waitlist_position(
        request: Request,
        class_id: str,
        student_id: int = Header(
            alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
        first_name: str = Header(alias="x-first-name"),
        last_name: str = Header(alias="x-last-name"),
        redisdb: Redis = Depends(get_redisdb)):
    try:
        # Get the rank of the member in the sorted set
        member = f"{student_id}#{first_name}#{last_name}"

        # Get the last modified timestamp for the resource
        last_modified_timestamp = get_last_modified_timestamp(class_id, redisdb)

        if last_modified_timestamp is not None:
            last_modified_datetime = datetime.utcfromtimestamp(last_modified_timestamp)

            # Extracting If-Modified-Since
            if_modified_since_header = request.headers.get("if-modified-since")
            if_modified_since = datetime.strptime(if_modified_since_header, "%a, %d %b %Y %H:%M:%S %Z") if if_modified_since_header else None

            # Checking if the timestamp has changed
            if if_modified_since is not None and last_modified_datetime <= if_modified_since:
                raise HTTPException(status_code=304, detail="Not Modified")

            # Get the current waitlist position
            position = redisdb.zrank(class_id, member) + 1

            # Updating timestamp
            update_last_modified_timestamp(class_id, redisdb)

            response_json = {"position": position}
        else:
            # Return a 200 status code with a message when the resource is not found
            response_json = {"detail": "Record Not Found"}
            
    except RedisError as e:
        print(f"RedisError: {e}")
        return JSONResponse(content={"detail": "Internal Server Error - RedisError"}, status_code=500)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return JSONResponse(content={"detail": "Internal Server Error - Unexpected Error"}, status_code=500)
    else:
        return response_json
    finally:
        # Close the Redis connection
        redisdb.close()



@student_router.delete("/waitlist/{class_id}/", status_code=status.HTTP_200_OK)
def remove_from_waitlist(
        class_id: str,
        student_id: int = Header(
            alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
        redisdb: Redis = Depends(get_redisdb),
        dynamodb: DynamoClient = Depends(get_dynamodb)):
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
            # ***********************************************
            # UPDATE PERSONNEL waitlists attributes
            # ***********************************************
            kwargs = {
                "Key": {
                    "cwid": student_id
                },
                "ConditionExpression": "attribute_exists(cwid)",
                "UpdateExpression": "DELETE waitlists :value",
                "ExpressionAttributeValues": {
                    ":value": {class_id}
                },
                "ReturnValues": "UPDATED_NEW"
            }

            dynamodb.update_item(TableNames.PERSONNEL, kwargs)

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
