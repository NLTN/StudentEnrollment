import sqlite3
from http import HTTPStatus
from fastapi import HTTPException, status
from botocore.exceptions import ClientError
from .dynamoclient import DynamoClient
from .db_connection import get_dynamodb, get_redisdb, TableNames

def is_auto_enroll_enabled(dynamodb: DynamoClient):
    """
    Check if automatic enrollment is enabled

    Parameters:
        db (sqlite3.Connection): Database connection.

    Returns:
        bool: True if automatic enrollment is enabled. Otherwise, False.
    """
    kwargs = {"Key": {"variable_name": "auto_enrollment_enabled"}}
    response = dynamodb.get_item(TableNames.CONFIGS, kwargs)
    return response["Item"]["value"] == True

def get_available_classes_within_first_2weeks(db: sqlite3.Connection):
    """
    Get classes which have available seats

    Parameters:
        db (sqlite3.Connection): Database connection.

    Returns:
        list[int]: A list of class_id.
    """

    cursor = db.execute(
        """
        SELECT id 
        FROM class 
        WHERE course_start_date >= datetime('now', '-14 days')
            AND room_capacity > (SELECT COUNT(student_id)
                            FROM enrollment
                            WHERE class_id = id
                            )
        """)
    rows = cursor.fetchall()
    return [row[0] for row in rows]

def enroll_students_from_waitlist(class_id_list: list, dynamodb: DynamoClient):
    """
    This function checks the waitlist for available spots in the classes
    and enrolls students accordingly.

    Parameters:
        dynamodb (DynamoClient): Database connection.

    Returns:
        int: The number of success enrollments.
    """
    
    num_students_enrolled = 0
    
    try:
        redisdb = get_redisdb()

        for class_id in class_id_list:
            # ---------------------------------------------------------------------
            # Get class information: num_open_seats = room_capacity - enrollment_count
            # ---------------------------------------------------------------------
            kwargs = {"Key": {"id": class_id}}
            response = dynamodb.get_item(TableNames.CLASSES, kwargs)
            
            if "room_capacity" in response["Item"]:
                room_capacity = int(response["Item"]["room_capacity"])
            else:
                room_capacity = 0

            if "enrollment_count" in response["Item"]:
                enrollment_count = int(response["Item"]["enrollment_count"])
            else:
                enrollment_count = 0

            num_open_seats = room_capacity - enrollment_count

            # ---------------------------------------------------------------------
            # Move students from the waitlist to enrollments
            # ---------------------------------------------------------------------
            if num_open_seats > 0:
                # ***********************************************
                # Get the first n students from the waitlist
                # ***********************************************
                members = redisdb.zrange(class_id, 0, num_open_seats - 1)
                student_id, first_name, last_name = members[0].decode('utf-8').split("#")

                # ***********************************************
                # Build a list of PutRequests 
                # ***********************************************
                enrollment_table_requests = []

                for m in members:
                    student_id, first_name, last_name = m.decode('utf-8').split("#")
                    item = {
                        "PutRequest": {
                            "Item": {
                                "class_id": class_id, 
                                "student_cwid": int(student_id),
                                "student_info": {
                                    "first_name": first_name,
                                    "last_name": last_name
                                }
                            }
                        }                        
                    }
                    enrollment_table_requests.append(item)

                # ***********************************************
                # BATCH INSERT INTO enrollments
                # ***********************************************
                batch_write_request = {
                    'RequestItems': {TableNames.ENROLLMENTS: enrollment_table_requests}
                }
                
                # Perform the batch write operation
                dynamodb.batch_write_item(batch_write_request)
            
                # ***********************************************
                # Delete those students from the waitlist 
                # because they enrolled successfully
                # ***********************************************
                redisdb.zremrangebyrank(class_id, 0, num_open_seats - 1)


                # ***********************************************
                # Update the counter
                # ***********************************************
                num_students_enrolled += num_open_seats

    except Exception as e:
        print(e)
    finally:
        redisdb.close()  # Close the Redis connection
    
    return num_students_enrolled


def add_to_waitlist(class_id, student_id, member_name: str, score: int):
    try:
        redisdb = get_redisdb()
        dynamodb = get_dynamodb()

        # Insert into Redis DB
        redisdb.zadd(class_id, {member_name: score})

        # Update Personnel table: add class_id to waitlist attribute
        update_kwargs = {
            "Key": {
                "cwid": student_id
            },
            "ConditionExpression": "attribute_exists(cwid)",
            "UpdateExpression": "SET waitlists = list_append(if_not_exists(waitlists, :empty_list), :new_item)",
            "ExpressionAttributeValues": {
                ":new_item": [class_id],
                ':empty_list': []
            },
            "ReturnValues": "UPDATED_NEW"
        }

        dynamodb.update_item(TableNames.PERSONNEL, update_kwargs)

    except Exception as e:
        raise Exception(f"AddToWaitlistFailed: {e}")

def drop_from_enrollment(class_id, student_id, administrative: bool, dynamodb: DynamoClient):
    try:
        TransactItems = [
            {
                # ***********************************************
                # DELETE FROM enrollment table
                # ***********************************************
                "Delete": {
                    "TableName": TableNames.ENROLLMENTS,
                    "Key": {
                        "class_id": class_id,
                        "student_cwid": student_id
                    },
                    "ConditionExpression": "attribute_exists(class_id) AND attribute_exists(student_cwid)"
                }
            },
            {
                # ***********************************************
                # INSERT INTO droplist table
                # ***********************************************
                "Put": {
                    "TableName": TableNames.DROPLIST,
                    "Item": {
                        "class_id": class_id,
                        "student_cwid": student_id,
                        "administrative": administrative
                    }
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
                                            enrollment_count = if_not_exists(enrollment_count, :zero) + :step_size",
                    "ExpressionAttributeValues": {
                        ":status": "true",
                        ":step_size": -1,
                        ":zero": 0
                    }
                }
            }
        ]

        dynamodb.transact_write_items(TransactItems)

        # ---------------------------------------------------------------------
        # Trigger auto enrollment
        # ---------------------------------------------------------------------
        # TODO: Call the function auto_enrollment_from_waitlist()
        if is_auto_enroll_enabled(dynamodb):
            enroll_students_from_waitlist([class_id], dynamodb)

    except ClientError as e:
        if e.response["Error"]["Code"] == "TransactionCanceledException":
            cancellation_reasons = e.response["CancellationReasons"]
            if cancellation_reasons[0]["Code"] == "ConditionalCheckFailed":
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail="Transaction Canceled")
            else:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail="Conflict occurs")
        else:
            raise Exception(e.response)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                            detail=e)
    else:
        return {"detail": "Item deleted successfully"}