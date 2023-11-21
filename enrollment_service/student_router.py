from typing import Annotated, Any
import sqlite3
from http import HTTPStatus
from fastapi.responses import JSONResponse
from fastapi import Depends, HTTPException, Header, Body, status, APIRouter, Request
from datetime import datetime
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
def get_available_classes(db: Any = Depends(get_dynamo), user: Personnel = Depends(get_current_user)):
    '''
    EXAMPLE ONLY (please reimplement this endpoint)
    requirements:
        - "x-cwid", "x-first-name", "x-last-name", "x-roles" headers from krakend must be propagated

    example of dependency injection usage:
        1: "dependencies = [get_or_create_user]" -> this function retrieves or create user information based on 
            the propagated headers. (syncs with user db). user info is stored in request state
        2: get_dynamo -> abstraction to make dynamo accesible within the endpoint. the dynamo wrapper instance was 
            instantiated in app.py and already stored in the app state. this function just returns the object

            **why are we reusing the same instance of dynamo wrapper?
              - botocore has a built in db connection pool, of default 10 connections. that's why we only
                need one instance for the dynamo wrapper

        3: get_current_user -> abstraction to make current user accessible within the endpoint. this function just returns
            the user object saved in request state from get_or_create_user 
    '''
    return {"user": user.cwid}
# def get_available_classes(db: sqlite3.Connection = Depends(get_db),  student_id: int = Header(
#         alias="x-cwid", description="A unique ID for students, instructors, and registrars")):
#     """
#     Retreive all available classes.

#     Returns:
#     - dict: A dictionary containing the details of the classes
#     """
#     print(student_id)
#     try:
#         classes = db.execute(
#             """
#             SELECT c.*
#             FROM "class" as c
#             WHERE datetime('now') BETWEEN c.enrollment_start AND c.enrollment_end
#                 AND (
#                         (c.room_capacity >
#                             (SELECT COUNT(enrollment.student_id)
#                             FROM enrollment
#                             WHERE class_id=c.id) > 0)
#                         OR ((SELECT COUNT(waitlist.student_id)
#                             FROM waitlist
#                             WHERE class_id=c.id) < ?)
#                     );
#             """, [WAITLIST_CAPACITY]
#         )
#     except sqlite3.Error as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail={"type": type(e).__name__, "msg": str(e)},
#         )
#     finally:
#         return {"classes": classes.fetchall()}


@student_router.post("/enrollment/", dependencies=[Depends(get_or_create_user)], status_code=status.HTTP_201_CREATED)
def enroll(class_id: Annotated[int, Body(embed=True)],
           student_id: int = Header(
               alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
           first_name: str = Header(alias="x-first-name"),
           last_name: str = Header(alias="x-last-name"),
           redisdb=Depends(get_redisdb),
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
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Class Not Found")

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
            kwargs = {
                "Item": {
                    "class_id": class_id,
                    "student_cwid": student_id
                },
                "ConditionExpression": "attribute_not_exists(class_id) AND attribute_not_exists(student_cwid)"
            }

            dynamodb.put_item(TableNames.ENROLLMENTS, kwargs)

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
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Item already exists")
        else:
            raise Exception(e.response)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e)
    else:
        return response_json


@student_router.delete("/enrollment/{class_id}", status_code=status.HTTP_200_OK)
def drop_class(
    class_id: int,
    student_id: int = Header(
        alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
    dynamodb: DynamoClient = Depends(get_dynamodb)
):
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
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="INTERNAL SERVER ERROR")
    else:
        return {"detail": "Item deleted successfully"}


@student_router.get("/waitlist/{class_id}/position/")
def get_current_waitlist_position(
        class_id: int,
        student_id: int = Header(
            alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
        db: sqlite3.Connection = Depends(get_db)):
    """
    Retreive all available classes.

    Returns:
    - dict: A dictionary containing the details of the classes

    Raises:
    - HTTPException (404): If record not found
    """
    try:
        result = db.execute(
            """
            SELECT COUNT(student_id)
            FROM waitlist
            WHERE class_id=? AND 
                waitlist_date <= (SELECT waitlist_date 
                                    FROM waitlist
                                    WHERE class_id=? AND 
                                            student_id=?)
            ;
            """, [class_id, class_id, student_id]
        ).fetchone()

        if result[0] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Record Not Found"
            )
        return {"position": result[0]}

    except sqlite3.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"type": type(e).__name__, "msg": str(e)},
        )


@student_router.delete("/waitlist/{class_id}/", status_code=status.HTTP_200_OK)
def remove_from_waitlist(
    class_id: int,
    student_id: int = Header(
        alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
    db: sqlite3.Connection = Depends(get_db)
):
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
        curr = db.execute(
            "DELETE FROM waitlist WHERE class_id=? AND student_id=?", [class_id, student_id])

        if curr.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Record Not Found"
            )

    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": type(e).__name__, "msg": str(e)},
        )

    return {"detail": "Item deleted successfully"}
