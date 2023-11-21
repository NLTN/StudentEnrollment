from typing import Annotated, Any
# import sqlite3
from http import HTTPStatus
from fastapi import Depends, Response, HTTPException, Body, status, APIRouter, Request
from fastapi.responses import JSONResponse
from .dynamoclient import DynamoClient
from .db_connection import get_dynamodb, TableNames
from .models import Course, ClassCreate, ClassPatch, Config, Personnel
from .registrar_helper import *
from .dependency_injection import get_or_create_user
from botocore.exceptions import ClientError

registrar_router = APIRouter()


@registrar_router.put("/auto-enrollment/")
def set_auto_enrollment(config: Config, dynamodb: DynamoClient = Depends(get_dynamodb)):
    """
    Endpoint for enabling/disabling automatic enrollment.

    Parameters:
    - semester (str): term's semester
    - year (int) : term's year 
    - auto_enrollment_enabled (bool): A boolean indicating whether automatic enrollment should be enabled or disabled.

    Raises:
    - HTTPException (404): If the enrollment period is not found.

    Returns:
        dict: A dictionary containing a detail message confirming the status of auto enrollment.
    """
    try:
        kwargs = {
            "Item": {
                "variable_name": "auto_enrollment_enabled",
                "value": config.auto_enrollment_enabled
            }
        }
        dynamodb.put_item(TableNames.CONFIGS, kwargs)
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="INTERNAL SERVER ERROR")
    else:
        return {"detail": "success"}


@registrar_router.post("/courses/")
def create_course(course: Course, dynamodb: DynamoClient = Depends(get_dynamodb)):
    """
    Creates a new course with the provided details.

    Parameters:
    - `course` (CourseInput): JSON body input for the course with the following fields:
        - `department_code` (str): The department code for the course.
        - `course_no` (str): The course number.
        - `title` (str): The title of the course.

    Returns:
    - dict: A dictionary containing the details of the created item.

    Raises:
    - HTTPException (409): If a conflict occurs (e.g., duplicate course).
    """
    try:
        kwargs = {
            "Item": dict(course),
            "ConditionExpression": "attribute_not_exists(department_code) AND attribute_not_exists(course_no)"
        }
        dynamodb.put_item(TableNames.COURSES, kwargs)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(status_code=HTTPStatus.CONFLICT,
                                detail="Item already exists")
        else:
            raise Exception(e.response)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="INTERNAL SERVER ERROR")
    else:
        return JSONResponse(status_code=HTTPStatus.CREATED, content={"message": "Item created successfully"})


@registrar_router.post("/classes/",  dependencies=[Depends(get_or_create_user)])
def create_class(new_class: ClassCreate, dynamodb: DynamoClient = Depends(get_dynamodb)):
    """
    Creates a new class.

    Parameters:
    - `class` (ClassCreate): The JSON object representing the class with the following properties:
        - `id` (int): Unique ID
        - `department_code` (str): Department code.
        - `course_no` (int): Course number.
        - `section_no` (int): Section number.
        - `year` (int): Academic year.
        - `semester` (str): Semester name (SP, SU, FA, WI).
        - `instructor_id` (int): Instructor ID.
        - `room_capacity` (int): Room capacity.


    Returns:
    - dict: A dictionary containing the details of the created item.

    Raises:
    - HTTPException (409): If a conflict occurs (e.g., duplicate course).
    - HTTPException (400): If course information or instructor information is not found
    """
    get_course_kwargs = {
        "Get": {
            "TableName": TableNames.COURSES,
            "Key": {
                "department_code": new_class.department_code,
                "course_no": new_class.course_no,
            }
        }
    }

    get_instructor_kwargs = {
        "Get": {
            "TableName": TableNames.PERSONNEL,
            "Key": {
                "cwid": new_class.instructor_id
            }
        }
    }

    try:
        # ---------------------------------------------------------------------
        # Check if course & instructor exists
        # ---------------------------------------------------------------------
        responses = dynamodb.transact_get_items(
            [get_course_kwargs, get_instructor_kwargs])

        if not responses[0]:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                detail="Course information not found")

        if not responses[1] or not "Instructor" in responses[1]["Item"]["roles"]:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                detail="Instructor not found")

        # ---------------------------------------------------------------------
        # Insert into DB
        # ---------------------------------------------------------------------
        item = dict(new_class)  # Convert to dictionary
        # Append new attribute `term`
        item["available_status"] = "true"

        kwargs = {
            "Item": item,
            "ConditionExpression": "attribute_not_exists(id)"
        }

        dynamodb.put_item(TableNames.CLASSES, kwargs)

    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(status_code=HTTPStatus.CONFLICT,
                                detail="Item already exists")
        else:
            raise Exception(e.response)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=e)
    else:
        return JSONResponse(status_code=HTTPStatus.CREATED, content={"detail": "Item created successfully"})


@registrar_router.delete("/classes/{class_id}")
def delete_class(class_id: int, dynamodb: DynamoClient = Depends(get_dynamodb)):
    """
    Deletes a specific class.

    Parameters:
    - `class_term_slug` (str): concatenated string of class term.
    i.e class_term_slug = Fall-2023_CPSC-449

    Returns:
    - dict: A dictionary indicating the success of the deletion operation.
      Example: {"message": "Item deleted successfully"}

    Raises:
    - HTTPException (400): If invalid class_term_slug was passed.
    - HTTPException (404): If the class with class_term_slug is not found.
    """
    try:
        kwargs = {
            "Key": {
                "id": class_id
            },
            "ConditionExpression": "attribute_exists(id)",
        }
        dynamodb.delete_item(TableNames.CLASSES, kwargs)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Item Not Found")
        else:
            raise Exception(e.response)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="INTERNAL SERVER ERROR")
    else:
        return JSONResponse(status_code=HTTPStatus.OK, content={"message": "Item deleted successfully"})


@registrar_router.patch("/classes/{class_id}", dependencies=[Depends(get_or_create_user)])
def update_class_instructor(instructor: PatchInstructor, class_id: int, dynamodb: DynamoClient = Depends(get_dynamodb)):
    """
    Updates instructor information for a class.

    Parameters:
    - `instructor` (PatchInstructor): The JSON object representing the class with the following properties:
        - `cwid` (int): Instructor ID.

    Returns:
    - dict: A dictionary indicating the success of the update operation.
      Example: {"message": "Item updated successfully"}

    Raises:
    - HTTPException (404): If the class with the specified ID, or instructor is not found.
    """
    try:
        kwargs = {
            "Get": {
                "TableName": TableNames.PERSONNEL,
                "Key": {
                    "cwid": instructor.cwid
                }
            }
        }
        responses = dynamodb.transact_get_items([kwargs])

        if not responses[0] or not "Instructor" in responses[0]["Item"]["roles"]:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                detail="instructor information not found")

        update_kwargs = {
            "Key": {
                "id": class_id
            },
            # check if the item already exists
            "ConditionExpression": "attribute_exists(id)",
            "UpdateExpression": "SET #instructor_id = :v1, #instructor_first_name = :v2, #instructor_last_name = :v3",
            "ExpressionAttributeValues": {
                ":v1": instructor.cwid,
                ":v2": responses[0]["Item"]["first_name"],
                ":v3": responses[0]["Item"]["last_name"]
            },
            "ExpressionAttributeNames": {
                "#instructor_id": "instructor_id",
                "#instructor_first_name": "instructor_first_name",
                "#instructor_last_name": "instructor_last_name"
            },
            "ReturnValues": "UPDATED_NEW"
        }

        dynamodb.update_item(TableNames.CLASSES, update_kwargs)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Item Not Found")
        else:
            raise Exception(e.response)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="INTERNAL SERVER ERROR")
    else:
        return JSONResponse(status_code=HTTPStatus.OK, content={"message": "Item updated successfully"})
