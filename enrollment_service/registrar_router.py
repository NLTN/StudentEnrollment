from typing import Annotated, Any
# import sqlite3
from http import HTTPStatus
from fastapi import Depends, Response, HTTPException, Body, status, APIRouter, Request
from fastapi.responses import JSONResponse
from .db_connection import get_db
# from .enrollment_helper import enroll_students_from_waitlist, get_available_classes_within_first_2weeks
from .models import Course, ClassCreate, ClassPatch, Config, Personnel
from .registrar_helper import *
from .Dynamo import Dynamo, DYNAMO_TABLENAMES
from .dependency_injection import get_or_create_user, get_current_user, get_dynamo
from botocore.exceptions import ClientError

registrar_router = APIRouter()

@registrar_router.put("/auto-enrollment/")
def set_auto_enrollment(config: Config, db: Any = Depends(get_dynamo)):
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

    query_params = generate_get_enrollment_period_params()
    get_enrollment_period_status = db.query(DYNAMO_TABLENAMES["config"], query_params)

    if not get_enrollment_period_status:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail={"detail" : "config not found"})
    
    if get_enrollment_period_status[0]["value"] == config.auto_enrollment_enabled:
        enrollment_period_status = {            
            "auto_enrollment_enabled" : get_enrollment_period_status[0]["value"]
        }
        return JSONResponse(status_code=HTTPStatus.OK, content={"message" : enrollment_period_status})

    update_params = generate_update_enrollment_period_params(config.auto_enrollment_enabled)
    result = db.update_item(DYNAMO_TABLENAMES["config"] ,update_params)

    return JSONResponse(status_code=HTTPStatus.OK, content={"message" : f'updated enrollment period successfully', "detail": result})

    # try:
    #     db.execute("UPDATE configs set automatic_enrollment = ?;", [enabled])
    #     db.commit()

    #     if enabled:
    #         opening_classes = get_available_classes_within_first_2weeks(db)
    #         enroll_students_from_waitlist(db, opening_classes)

    # except sqlite3.IntegrityError as e:
    #     raise HTTPException(
    #         status_code=status.HTTP_409_CONFLICT,
    #         detail={"type": type(e).__name__, "msg": str(e)},
    #     )

    # return {"detail": f"Auto enrollment: {enabled}"}

@registrar_router.post("/courses/")
def create_course(course: Course, db: Dynamo = Depends(get_dynamo)):
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
    query_params = generate_get_course_params(course)
    get_course = db.query(DYNAMO_TABLENAMES["course"], query_params)

    if get_course:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail="Specified course already exists!")
    
    new_course = dict(course)
    data = {
        "Item": new_course
    }
    if db.dyn_resource.Table(DYNAMO_TABLENAMES["course"]).put_item(**data):
        return JSONResponse(status_code=HTTPStatus.CREATED, content={"message": "class added successfully", "data" : new_course})

@registrar_router.post("/classes/",  dependencies=[Depends(get_or_create_user)])
def create_class(new_class: ClassCreate, db: Dynamo= Depends(get_dynamo)):
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
    get_course_params = {
        "Get" : {
            "TableName" : DYNAMO_TABLENAMES["course"],
            "Key" : {
                "department_code" : new_class.department_code,
                "course_no" : new_class.course_no,
            }
        }
    }

    get_instructor_params = {
        "Get" : {
            "TableName" : DYNAMO_TABLENAMES["personnel"],
            "Key" : {
                "cwid" : new_class.instructor_id
            }
        }
    }

    try:
        results = db.transact_get_items([get_course_params, get_instructor_params])

        if not results[0]:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Course information not found")
        
        if not results[1] or not "Instructor" in results[1]["Item"]["roles"]:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Instructor not found")
        
        # Convert to Python dictionary
        item = dict(new_class)
        data = {
            "Item": item,
            "ConditionExpression": "attribute_not_exists(id)" #check if the item does not already exist
        }
        if db.dyn_resource.Table(DYNAMO_TABLENAMES["class"]).put_item(**data):
            return JSONResponse(status_code=HTTPStatus.CREATED, content={"message": "Created class successfully", "data" : item})
    
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(status_code=HTTPStatus.CONFLICT, detail="Item already exists")
        else:
            raise Exception(e.response)
    
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="INTERNAL SERVER ERROR")
    
@registrar_router.delete("/classes/{class_id}")
def delete_class(class_id : int, db: Dynamo = Depends(get_dynamo)):
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
        delete_params = {
            "Key": {
                "id" : class_id
            },
            "ConditionExpression": "attribute_exists(id)", #check if the item already exists
        }

        if db.delete_item(tablename=DYNAMO_TABLENAMES["class"], delete_params=delete_params):
            return JSONResponse(status_code=HTTPStatus.OK, content={"message" : "Item deleted successfully"})
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Item Not Found")
        else:
            raise Exception(e.response)
    
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="INTERNAL SERVER ERROR")

@registrar_router.patch("/classes/{class_id}", dependencies=[Depends(get_or_create_user)])
def update_class_instructor(instructor: PatchInstructor, class_id : int, db: Dynamo = Depends(get_dynamo)):
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
        get_instructor_params = {
            "Get": {
                "TableName" : DYNAMO_TABLENAMES["personnel"],
                "Key" : {
                    "cwid" : instructor.cwid
                }
            }
        }

        query_results = db.transact_get_items([get_instructor_params])
        
        if not query_results[0] or not "Instructor" in query_results[0]["Item"]["roles"]:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="instructor information not found")

        update_instructor_params = {
            "Key" : {
                "id" : class_id
            },
            "ConditionExpression": "attribute_exists(id)", #check if the item already exists
            "UpdateExpression" : "SET #instructor_id = :v1, #instructor_first_name = :v2, #instructor_last_name = :v3",
            "ExpressionAttributeValues" : {
                ":v1" : instructor.cwid,
                ":v2" : query_results[0]["Item"]["first_name"],
                ":v3" : query_results[0]["Item"]["last_name"]
            },
            "ExpressionAttributeNames" : {
                "#instructor_id" : "instructor_id",
                "#instructor_first_name" : "instructor_first_name",
                "#instructor_last_name" : "instructor_last_name"
            },
            "ReturnValues" : "UPDATED_NEW"
        }

        db.update_item(tablename=DYNAMO_TABLENAMES["class"], update_params = update_instructor_params)
        
        return JSONResponse(status_code=HTTPStatus.OK, content={"message" : "updated instructor for class successfully"})
    
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Item Not Found")
        else:
            raise Exception(e.response)
    
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="INTERNAL SERVER ERROR")